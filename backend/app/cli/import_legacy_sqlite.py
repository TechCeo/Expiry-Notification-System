from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Batch, Location, Organization, OrganizationMembership, Product, User
from app.db.session import SessionLocal
from app.domain.enums import BatchStatus, OrganizationRole, ProductStatus


@dataclass(slots=True)
class LegacyRow:
    source_table: str
    legacy_id: int
    name: str
    category: str
    quantity: int
    expiry_date: date
    notes: str


@dataclass(slots=True)
class ImportFailure:
    source_table: str
    legacy_id: int | None
    reason: str


@dataclass(slots=True)
class ImportReport:
    dry_run: bool
    source_path: str
    source_table: str
    organization_slug: str
    location_code: str
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    source_total: int = 0
    destination_total_before: int = 0
    destination_total_after: int = 0
    failures: list[ImportFailure] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds")
    )

    def to_json(self) -> str:
        payload = asdict(self)
        return json.dumps(payload, indent=2, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import legacy SQLite inventory into PostgreSQL."
    )
    parser.add_argument("--source", default="database.db", help="Path to legacy SQLite DB.")
    parser.add_argument(
        "--source-table",
        choices=("auto", "products", "students"),
        default="auto",
        help="Legacy table to import. auto prefers products, then students.",
    )
    parser.add_argument("--organization-name", default="Legacy Import")
    parser.add_argument("--organization-slug", default="legacy-import")
    parser.add_argument("--location-name", default="Legacy Default Location")
    parser.add_argument("--location-code", default="LEGACY")
    parser.add_argument(
        "--owner-email",
        default=None,
        help="Optional existing verified user email to grant owner access to imported org.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing.")
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional path for the machine-readable JSON migration report.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = import_legacy_sqlite(
        source_path=Path(args.source),
        source_table=args.source_table,
        organization_name=args.organization_name,
        organization_slug=args.organization_slug,
        location_name=args.location_name,
        location_code=args.location_code,
        owner_email=args.owner_email,
        dry_run=args.dry_run,
    )
    output = report.to_json()
    if args.report_path:
        Path(args.report_path).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if report.failed else 0


def import_legacy_sqlite(
    *,
    source_path: Path,
    source_table: str,
    organization_name: str,
    organization_slug: str,
    location_name: str,
    location_code: str,
    owner_email: str | None,
    dry_run: bool,
) -> ImportReport:
    if not source_path.exists():
        raise SystemExit(f"Legacy SQLite database not found: {source_path}")

    with sqlite3.connect(source_path) as legacy:
        legacy.row_factory = sqlite3.Row
        selected_table = resolve_source_table(legacy, source_table)
        raw_rows = list(read_legacy_rows(legacy, selected_table))

    report = ImportReport(
        dry_run=dry_run,
        source_path=str(source_path),
        source_table=selected_table,
        organization_slug=organization_slug,
        location_code=location_code,
        source_total=len(raw_rows),
    )
    valid_rows = validate_rows(raw_rows, report)

    with SessionLocal() as session:
        report.destination_total_before = count_imported_batches(
            session, organization_slug, selected_table
        )
        organization = get_or_create_organization(
            session, organization_name, organization_slug, dry_run
        )
        location = get_or_create_location(
            session, organization, location_name, location_code, dry_run
        )
        if owner_email:
            grant_owner(session, organization, owner_email, dry_run)

        for row in valid_rows:
            if legacy_batch_exists(session, organization.id, row):
                report.skipped += 1
                continue
            if dry_run:
                report.imported += 1
                continue
            product = get_or_create_product(session, organization, row)
            batch = Batch(
                organization_id=organization.id,
                product_id=product.id,
                location_id=location.id,
                batch_number=legacy_batch_number(row),
                quantity_received=row.quantity,
                quantity_available=row.quantity,
                expiry_date=row.expiry_date,
                received_date=date.today(),
                status=batch_status(row).value,
                notes=row.notes,
            )
            session.add(batch)
            report.imported += 1

        if dry_run:
            session.rollback()
            report.destination_total_after = report.destination_total_before
        else:
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                report.failed += 1
                report.failures.append(
                    ImportFailure(
                        source_table=selected_table,
                        legacy_id=None,
                        reason=f"PostgreSQL integrity error: {error.orig}",
                    )
                )
            report.destination_total_after = count_imported_batches(
                session, organization_slug, selected_table
            )

    return report


def resolve_source_table(connection: sqlite3.Connection, requested: str) -> str:
    tables = {
        row["name"]
        for row in connection.execute(
            "select name from sqlite_master where type = 'table'"
        )
    }
    if requested != "auto":
        if requested not in tables:
            raise SystemExit(f"Legacy table {requested!r} not found.")
        return requested
    if "products" in tables:
        return "products"
    if "students" in tables:
        return "students"
    raise SystemExit("No supported legacy table found. Expected products or students.")


def read_legacy_rows(
    connection: sqlite3.Connection, source_table: str
) -> list[dict[str, Any]]:
    if source_table == "products":
        return [
            dict(row)
            for row in connection.execute(
                "select id, name, category, quantity, expiry_date, remarks from products"
            )
        ]
    return [
        dict(row)
        for row in connection.execute(
            "select roll as id, name, branch as category, sem as quantity, "
            "mobile as expiry_date, address as remarks from students"
        )
    ]


def validate_rows(rows: list[dict[str, Any]], report: ImportReport) -> list[LegacyRow]:
    valid: list[LegacyRow] = []
    for row in rows:
        try:
            legacy_id = int(row["id"])
            name = str(row["name"]).strip()
            category = str(row["category"] or "Uncategorized").strip()
            quantity = int(row["quantity"])
            expiry = parse_legacy_date(row["expiry_date"])
            notes = str(row.get("remarks") or "").strip()
            if not name:
                raise ValueError("name is required")
            if quantity < 0:
                raise ValueError("quantity cannot be negative")
            valid.append(
                LegacyRow(
                    source_table=report.source_table,
                    legacy_id=legacy_id,
                    name=name,
                    category=category[:80] or "Uncategorized",
                    quantity=quantity,
                    expiry_date=expiry,
                    notes=notes,
                )
            )
        except Exception as error:  # noqa: BLE001 - reports row-level import failures.
            report.failed += 1
            report.failures.append(
                ImportFailure(
                    source_table=report.source_table,
                    legacy_id=row.get("id"),
                    reason=str(error),
                )
            )
    return valid


def parse_legacy_date(value: object) -> date:
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"invalid expiry date: {text!r}")


def get_or_create_organization(
    session: Session, name: str, slug: str, dry_run: bool
) -> Organization:
    organization = session.scalar(select(Organization).where(Organization.slug == slug))
    if organization:
        return organization
    organization = Organization(name=name, slug=slug)
    session.add(organization)
    session.flush()
    if dry_run:
        session.refresh(organization)
    return organization


def get_or_create_location(
    session: Session,
    organization: Organization,
    name: str,
    code: str,
    dry_run: bool,
) -> Location:
    location = session.scalar(
        select(Location).where(
            Location.organization_id == organization.id,
            Location.code == code,
        )
    )
    if location:
        return location
    location = Location(
        organization_id=organization.id,
        name=name,
        code=code,
        timezone="UTC",
        address="Created by the legacy SQLite importer.",
        is_active=True,
    )
    session.add(location)
    session.flush()
    if dry_run:
        session.refresh(location)
    return location


def grant_owner(
    session: Session, organization: Organization, owner_email: str, dry_run: bool
) -> None:
    user = session.scalar(
        select(User).where(User.email == owner_email, User.email_verified.is_(True))
    )
    if user is None:
        raise SystemExit(
            "owner-email must belong to an existing user with a verified email."
        )
    existing = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization.id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if existing:
        existing.role = OrganizationRole.OWNER.value
        return
    session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role=OrganizationRole.OWNER.value,
        )
    )
    if dry_run:
        session.flush()


def get_or_create_product(
    session: Session, organization: Organization, row: LegacyRow
) -> Product:
    sku = legacy_sku(row)
    product = session.scalar(
        select(Product).where(
            Product.organization_id == organization.id,
            Product.sku == sku,
        )
    )
    if product:
        return product
    product = Product(
        organization_id=organization.id,
        sku=sku,
        name=row.name[:120],
        description="Imported from legacy SQLite inventory.",
        category=row.category,
        status=ProductStatus.ACTIVE.value,
        attributes={
            "legacy": {
                "source_table": row.source_table,
                "id": row.legacy_id,
            }
        },
    )
    session.add(product)
    session.flush()
    return product


def legacy_batch_exists(
    session: Session, organization_id: Any, row: LegacyRow
) -> bool:
    return bool(
        session.scalar(
            select(Batch.id).where(
                Batch.organization_id == organization_id,
                Batch.batch_number == legacy_batch_number(row),
            )
        )
    )


def count_imported_batches(
    session: Session, organization_slug: str, source_table: str
) -> int:
    organization = session.scalar(
        select(Organization).where(Organization.slug == organization_slug)
    )
    if not organization:
        return 0
    return len(
        session.scalars(
            select(Batch.id).where(
                Batch.organization_id == organization.id,
                Batch.batch_number.like(f"LEGACY-{source_table}-%"),
            )
        ).all()
    )


def legacy_sku(row: LegacyRow) -> str:
    return f"LEGACY-{row.source_table}-{row.legacy_id}"


def legacy_batch_number(row: LegacyRow) -> str:
    return f"LEGACY-{row.source_table}-{row.legacy_id}"


def batch_status(row: LegacyRow) -> BatchStatus:
    if row.quantity == 0:
        return BatchStatus.DEPLETED
    if row.expiry_date < date.today():
        return BatchStatus.EXPIRED
    return BatchStatus.ACTIVE


if __name__ == "__main__":
    raise SystemExit(main())
