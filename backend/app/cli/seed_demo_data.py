from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Batch, Location, Organization, OrganizationMembership, Product, User
from app.db.session import SessionLocal
from app.domain.enums import BatchStatus, OrganizationRole
from app.repositories.identity import IdentityRepository
from app.repositories.inventory import InventoryRepository
from app.schemas.batch import BatchCreate
from app.schemas.location import LocationCreate
from app.schemas.organization import OrganizationCreate
from app.schemas.product import ProductCreate
from app.services.authorization import AuthorizationService
from app.services.inventory import InventoryService

DEFAULT_OWNER_EMAIL = "owner@example.com"
DEFAULT_OWNER_SUBJECT = "11111111-1111-4111-8111-111111111111"


@dataclass(frozen=True, slots=True)
class LocationSeed:
    name: str
    code: str
    address: str


@dataclass(frozen=True, slots=True)
class ProductSeed:
    sku: str
    name: str
    category: str
    description: str
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class BatchSeed:
    product_sku: str
    location_code: str
    batch_number: str
    quantity_received: int
    quantity_available: int
    expiry_offset_days: int
    received_offset_days: int
    status: BatchStatus
    notes: str


@dataclass(frozen=True, slots=True)
class OrganizationSeed:
    name: str
    slug: str
    locations: tuple[LocationSeed, ...]
    products: tuple[ProductSeed, ...]
    batches: tuple[BatchSeed, ...]


@dataclass(slots=True)
class SeedReport:
    dry_run: bool
    owner_email: str
    organizations_created: int = 0
    organizations_skipped: int = 0
    memberships_created: int = 0
    memberships_skipped: int = 0
    locations_created: int = 0
    locations_skipped: int = 0
    products_created: int = 0
    products_skipped: int = 0
    batches_created: int = 0
    batches_skipped: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


DEMO_ORGANIZATIONS: tuple[OrganizationSeed, ...] = (
    OrganizationSeed(
        name="FreshMart Downtown",
        slug="freshmart-downtown",
        locations=(
            LocationSeed(
                name="Downtown Storefront",
                code="DT-SALES",
                address="100 Market Street, New York, NY",
            ),
            LocationSeed(
                name="Downtown Walk-in Cooler",
                code="DT-COOLER",
                address="100 Market Street, basement cold room",
            ),
            LocationSeed(
                name="Downtown Freezer Bay",
                code="DT-FREEZER",
                address="100 Market Street, rear freezer bay",
            ),
        ),
        products=(
            ProductSeed(
                sku="DAIRY-MILK-1GAL",
                name="Whole Milk 1 Gallon",
                category="Dairy",
                description="Refrigerated whole milk for retail sale.",
                metadata={"brand": "Valley Fresh", "refrigerated": True, "size": "1 gallon"},
            ),
            ProductSeed(
                sku="BAKERY-SOURDOUGH",
                name="Sourdough Bread Loaf",
                category="Bakery",
                description="Fresh baked sourdough loaf.",
                metadata={"bakery_item": True, "shelf_life_days": 5},
            ),
            ProductSeed(
                sku="MEAT-CHICKEN-BREAST",
                name="Boneless Chicken Breast",
                category="Meat",
                description="Fresh chilled poultry packed by weight.",
                metadata={"refrigerated": True, "case_pack": "12 trays"},
            ),
            ProductSeed(
                sku="FROZEN-PEAS-2LB",
                name="Frozen Green Peas 2 lb",
                category="Frozen",
                description="Frozen vegetable bags for retail freezer.",
                metadata={"frozen": True, "size": "2 lb"},
            ),
            ProductSeed(
                sku="PANTRY-TOMATOES-28OZ",
                name="Canned Crushed Tomatoes 28 oz",
                category="Pantry",
                description="Shelf-stable canned tomatoes.",
                metadata={"shelf_stable": True, "can_size_oz": 28},
            ),
        ),
        batches=(
            BatchSeed(
                product_sku="BAKERY-SOURDOUGH",
                location_code="DT-SALES",
                batch_number="DT-EXPIRED-BREAD-001",
                quantity_received=40,
                quantity_available=12,
                expiry_offset_days=-3,
                received_offset_days=-7,
                status=BatchStatus.EXPIRED,
                notes="Expired bakery inventory retained for dashboard validation.",
            ),
            BatchSeed(
                product_sku="DAIRY-MILK-1GAL",
                location_code="DT-COOLER",
                batch_number="DT-SOON-MILK-001",
                quantity_received=96,
                quantity_available=58,
                expiry_offset_days=9,
                received_offset_days=-2,
                status=BatchStatus.ACTIVE,
                notes="Expiring soon; should appear in the 30-day alert view.",
            ),
            BatchSeed(
                product_sku="FROZEN-PEAS-2LB",
                location_code="DT-FREEZER",
                batch_number="DT-HEALTHY-PEAS-001",
                quantity_received=160,
                quantity_available=144,
                expiry_offset_days=180,
                received_offset_days=-12,
                status=BatchStatus.ACTIVE,
                notes="Healthy frozen stock with long runway.",
            ),
            BatchSeed(
                product_sku="MEAT-CHICKEN-BREAST",
                location_code="DT-COOLER",
                batch_number="DT-QUAR-CHICKEN-001",
                quantity_received=36,
                quantity_available=36,
                expiry_offset_days=15,
                received_offset_days=-1,
                status=BatchStatus.QUARANTINED,
                notes="Temperature excursion investigation; quarantined for QA review.",
            ),
            BatchSeed(
                product_sku="PANTRY-TOMATOES-28OZ",
                location_code="DT-SALES",
                batch_number="DT-DEPLETED-TOMATO-001",
                quantity_received=72,
                quantity_available=0,
                expiry_offset_days=240,
                received_offset_days=-40,
                status=BatchStatus.DEPLETED,
                notes="Sold through; validates depleted inventory view.",
            ),
        ),
    ),
    OrganizationSeed(
        name="FreshMart Regional Warehouse",
        slug="freshmart-regional-warehouse",
        locations=(
            LocationSeed(
                name="Inbound Receiving Dock",
                code="WH-INBOUND",
                address="500 Distribution Drive, Newark, NJ",
            ),
            LocationSeed(
                name="Bulk Dry Storage",
                code="WH-DRY",
                address="500 Distribution Drive, aisle D",
            ),
            LocationSeed(
                name="Cold Chain Zone",
                code="WH-COLD",
                address="500 Distribution Drive, cold chain zone",
            ),
        ),
        products=(
            ProductSeed(
                sku="PRODUCE-APPLES-CASE",
                name="Honeycrisp Apples Case",
                category="Produce",
                description="Bulk case of fresh Honeycrisp apples.",
                metadata={"case_weight_lb": 40, "requires_rotation": True},
            ),
            ProductSeed(
                sku="DELI-YOGURT-CASE",
                name="Greek Yogurt Case",
                category="Dairy",
                description="Case-packed single-serve Greek yogurt cups.",
                metadata={"refrigerated": True, "units_per_case": 24},
            ),
            ProductSeed(
                sku="PANTRY-RICE-25LB",
                name="Jasmine Rice 25 lb",
                category="Pantry",
                description="Bulk dry rice for replenishment.",
                metadata={"shelf_stable": True, "bag_size_lb": 25},
            ),
            ProductSeed(
                sku="BEV-ORANGE-JUICE",
                name="Orange Juice 52 oz",
                category="Beverages",
                description="Chilled orange juice bottles.",
                metadata={"refrigerated": True, "volume_oz": 52},
            ),
            ProductSeed(
                sku="SEAFOOD-SALMON-FILLET",
                name="Atlantic Salmon Fillet",
                category="Seafood",
                description="Fresh salmon fillets for store distribution.",
                metadata={"refrigerated": True, "high_risk": True},
            ),
        ),
        batches=(
            BatchSeed(
                product_sku="SEAFOOD-SALMON-FILLET",
                location_code="WH-COLD",
                batch_number="WH-EXPIRED-SALMON-001",
                quantity_received=50,
                quantity_available=18,
                expiry_offset_days=-1,
                received_offset_days=-6,
                status=BatchStatus.EXPIRED,
                notes="Expired seafood batch used for exception reporting.",
            ),
            BatchSeed(
                product_sku="DELI-YOGURT-CASE",
                location_code="WH-COLD",
                batch_number="WH-SOON-YOGURT-001",
                quantity_received=120,
                quantity_available=83,
                expiry_offset_days=21,
                received_offset_days=-5,
                status=BatchStatus.ACTIVE,
                notes="Approaching expiry; should trigger expiring-soon workflows.",
            ),
            BatchSeed(
                product_sku="PANTRY-RICE-25LB",
                location_code="WH-DRY",
                batch_number="WH-HEALTHY-RICE-001",
                quantity_received=220,
                quantity_available=211,
                expiry_offset_days=365,
                received_offset_days=-30,
                status=BatchStatus.ACTIVE,
                notes="Stable dry goods with long shelf life.",
            ),
            BatchSeed(
                product_sku="BEV-ORANGE-JUICE",
                location_code="WH-INBOUND",
                batch_number="WH-QUAR-OJ-001",
                quantity_received=88,
                quantity_available=88,
                expiry_offset_days=28,
                received_offset_days=0,
                status=BatchStatus.QUARANTINED,
                notes="Supplier paperwork mismatch; held at inbound receiving.",
            ),
            BatchSeed(
                product_sku="PRODUCE-APPLES-CASE",
                location_code="WH-DRY",
                batch_number="WH-DEPLETED-APPLES-001",
                quantity_received=64,
                quantity_available=0,
                expiry_offset_days=35,
                received_offset_days=-14,
                status=BatchStatus.DEPLETED,
                notes="Transferred out to stores; validates zero-available stock.",
            ),
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed deterministic local demo organizations and inventory data."
    )
    parser.add_argument("--owner-email", default=DEFAULT_OWNER_EMAIL)
    parser.add_argument(
        "--owner-subject",
        default=DEFAULT_OWNER_SUBJECT,
        help="OIDC subject for the local demo owner. Matches the bundled Keycloak realm.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = seed_demo_data(
        owner_email=args.owner_email,
        owner_subject=args.owner_subject,
        dry_run=args.dry_run,
    )
    print(report.to_json())
    return 0


def seed_demo_data(*, owner_email: str, owner_subject: str, dry_run: bool) -> SeedReport:
    report = SeedReport(dry_run=dry_run, owner_email=owner_email)
    with SessionLocal() as session:
        owner = get_or_create_owner(
            session,
            owner_email=owner_email,
            owner_subject=owner_subject,
            dry_run=dry_run,
        )
        identity_repository = IdentityRepository(session)
        inventory_service = InventoryService(
            InventoryRepository(session),
            AuthorizationService(identity_repository, owner),
        )

        for organization_seed in DEMO_ORGANIZATIONS:
            seed_organization(
                session=session,
                service=inventory_service,
                actor=owner,
                seed=organization_seed,
                report=report,
                dry_run=dry_run,
            )

        if dry_run:
            session.rollback()
        else:
            session.commit()
    return report


def get_or_create_owner(
    session: Session, *, owner_email: str, owner_subject: str, dry_run: bool
) -> User:
    repository = IdentityRepository(session)
    owner = repository.get_user_by_email(owner_email)
    if owner is not None:
        return owner

    owner = repository.get_user_by_subject(owner_subject)
    if owner is not None:
        if owner.email is None:
            owner.email = owner_email
            owner.email_verified = True
            owner.display_name = owner.display_name or "Local Demo Owner"
            if not dry_run:
                repository.flush(owner)
        return owner

    owner = User(
        oidc_subject=owner_subject,
        email=owner_email,
        email_verified=True,
        display_name="Local Demo Owner",
    )
    session.add(owner)
    session.flush()
    session.refresh(owner)
    return owner


def seed_organization(
    *,
    session: Session,
    service: InventoryService,
    actor: User,
    seed: OrganizationSeed,
    report: SeedReport,
    dry_run: bool,
) -> None:
    organization = get_organization_by_slug(session, seed.slug)
    if organization is None:
        organization = service.create_organization(
            OrganizationCreate(name=seed.name, slug=seed.slug)
        )
        report.organizations_created += 1
    else:
        report.organizations_skipped += 1
        ensure_owner_membership(session, organization, actor, report, dry_run)

    locations = seed_locations(session, service, organization, seed.locations, report)
    products = seed_products(session, service, organization, seed.products, report)
    seed_batches(session, service, organization, locations, products, seed.batches, report)


def ensure_owner_membership(
    session: Session,
    organization: Organization,
    actor: User,
    report: SeedReport,
    dry_run: bool,
) -> None:
    repository = IdentityRepository(session)
    membership = repository.get_membership(organization.id, actor.id)
    if membership is not None:
        report.memberships_skipped += 1
        return

    session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=actor.id,
            role=OrganizationRole.OWNER.value,
        )
    )
    session.flush()
    report.memberships_created += 1
    if not dry_run:
        AuthorizationService(repository, actor).audit(
            organization_id=organization.id,
            action="membership.seeded",
            resource_type="membership",
            resource_id=None,
            details={"role": OrganizationRole.OWNER.value, "user_id": str(actor.id)},
        )


def seed_locations(
    session: Session,
    service: InventoryService,
    organization: Organization,
    seeds: tuple[LocationSeed, ...],
    report: SeedReport,
) -> dict[str, Location]:
    locations: dict[str, Location] = {}
    for seed in seeds:
        location = get_location_by_code(session, organization.id, seed.code)
        if location is None:
            location = service.create_location(
                LocationCreate(
                    organization_id=organization.id,
                    name=seed.name,
                    code=seed.code,
                    timezone="America/New_York",
                    address=seed.address,
                )
            )
            report.locations_created += 1
        else:
            report.locations_skipped += 1
        locations[seed.code] = location
    return locations


def seed_products(
    session: Session,
    service: InventoryService,
    organization: Organization,
    seeds: tuple[ProductSeed, ...],
    report: SeedReport,
) -> dict[str, Product]:
    products: dict[str, Product] = {}
    for seed in seeds:
        product = get_product_by_sku(session, organization.id, seed.sku)
        if product is None:
            product = service.create_product(
                ProductCreate(
                    organization_id=organization.id,
                    sku=seed.sku,
                    name=seed.name,
                    description=seed.description,
                    category=seed.category,
                    metadata=seed.metadata,
                )
            )
            report.products_created += 1
        else:
            report.products_skipped += 1
        products[seed.sku] = product
    return products


def seed_batches(
    session: Session,
    service: InventoryService,
    organization: Organization,
    locations: dict[str, Location],
    products: dict[str, Product],
    seeds: tuple[BatchSeed, ...],
    report: SeedReport,
) -> None:
    today = date.today()
    for seed in seeds:
        product = products[seed.product_sku]
        batch = get_batch_by_number(
            session,
            organization_id=organization.id,
            product_id=product.id,
            batch_number=seed.batch_number,
        )
        if batch is not None:
            report.batches_skipped += 1
            continue

        service.create_batch(
            BatchCreate(
                organization_id=organization.id,
                product_id=product.id,
                location_id=locations[seed.location_code].id,
                batch_number=seed.batch_number,
                quantity_received=seed.quantity_received,
                quantity_available=seed.quantity_available,
                expiry_date=today + timedelta(days=seed.expiry_offset_days),
                received_date=today + timedelta(days=seed.received_offset_days),
                status=seed.status,
                notes=seed.notes,
            )
        )
        report.batches_created += 1


def get_organization_by_slug(session: Session, slug: str) -> Organization | None:
    return session.scalar(select(Organization).where(Organization.slug == slug))


def get_location_by_code(
    session: Session, organization_id, code: str
) -> Location | None:
    return session.scalar(
        select(Location).where(
            Location.organization_id == organization_id,
            Location.code == code,
        )
    )


def get_product_by_sku(session: Session, organization_id, sku: str) -> Product | None:
    return session.scalar(
        select(Product).where(
            Product.organization_id == organization_id,
            Product.sku == sku,
        )
    )


def get_batch_by_number(
    session: Session, *, organization_id, product_id, batch_number: str
) -> Batch | None:
    return session.scalar(
        select(Batch).where(
            Batch.organization_id == organization_id,
            Batch.product_id == product_id,
            Batch.batch_number == batch_number,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
