import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.cli.import_legacy_sqlite as legacy_importer
from app.db.models import Batch, Location, Organization, Product


@contextmanager
def use_test_session(session: Session) -> Iterator[Session]:
    yield session


def patch_session(monkeypatch, session: Session) -> None:
    monkeypatch.setattr(
        legacy_importer,
        "SessionLocal",
        lambda: use_test_session(session),
    )


def create_products_sqlite(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            create table products (
                id integer primary key autoincrement,
                name text not null,
                category text not null,
                quantity integer not null,
                expiry_date text not null,
                remarks text not null default '',
                status text not null default 'ACTIVE',
                created_at text not null,
                updated_at text not null
            )
            """
        )
        connection.execute(
            """
            insert into products
                (id, name, category, quantity, expiry_date, remarks, created_at, updated_at)
            values
                (101, 'Legacy Soap', 'Detergents', 12, '2027-04-01',
                 '12 cartons', '2026-06-28T00:00:00', '2026-06-28T00:00:00')
            """
        )


def create_students_sqlite(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            create table students (
                roll integer primary key autoincrement,
                name text,
                branch text,
                sem integer,
                mobile integer,
                address text
            )
            """
        )
        connection.execute(
            """
            insert into students (roll, name, branch, sem, mobile, address)
            values (7, 'Old Apple', 'Fruit', 4, '2027-05-10', 'legacy note')
            """
        )


def test_legacy_importer_dry_run_validates_without_writing(
    tmp_path: Path, database_session: Session, monkeypatch
) -> None:
    patch_session(monkeypatch, database_session)
    source = tmp_path / "legacy.db"
    create_products_sqlite(source)

    report = legacy_importer.import_legacy_sqlite(
        source_path=source,
        source_table="products",
        organization_name="Dry Run Org",
        organization_slug="dry-run-org",
        location_name="Legacy Location",
        location_code="LEGACY",
        owner_email=None,
        dry_run=True,
    )

    assert report.dry_run is True
    assert report.imported == 1
    assert report.skipped == 0
    assert report.failed == 0
    assert database_session.scalar(
        select(Organization).where(Organization.slug == "dry-run-org")
    ) is None


def test_legacy_importer_imports_products_and_skips_duplicates(
    tmp_path: Path, database_session: Session, monkeypatch
) -> None:
    patch_session(monkeypatch, database_session)
    source = tmp_path / "legacy.db"
    create_products_sqlite(source)

    first_report = legacy_importer.import_legacy_sqlite(
        source_path=source,
        source_table="auto",
        organization_name="Legacy Org",
        organization_slug="legacy-org",
        location_name="Legacy Location",
        location_code="LEGACY",
        owner_email=None,
        dry_run=False,
    )
    second_report = legacy_importer.import_legacy_sqlite(
        source_path=source,
        source_table="auto",
        organization_name="Legacy Org",
        organization_slug="legacy-org",
        location_name="Legacy Location",
        location_code="LEGACY",
        owner_email=None,
        dry_run=False,
    )

    organization = database_session.scalar(
        select(Organization).where(Organization.slug == "legacy-org")
    )
    assert organization is not None
    product = database_session.scalar(
        select(Product).where(Product.sku == "LEGACY-products-101")
    )
    batch = database_session.scalar(
        select(Batch).where(Batch.batch_number == "LEGACY-products-101")
    )
    location = database_session.scalar(
        select(Location).where(Location.code == "LEGACY")
    )

    assert first_report.imported == 1
    assert first_report.destination_total_after == 1
    assert second_report.imported == 0
    assert second_report.skipped == 1
    assert product is not None
    assert product.category == "Detergents"
    assert batch is not None
    assert batch.quantity_available == 12
    assert location is not None


def test_legacy_importer_supports_original_students_mapping(
    tmp_path: Path, database_session: Session, monkeypatch
) -> None:
    patch_session(monkeypatch, database_session)
    source = tmp_path / "students.db"
    create_students_sqlite(source)

    report = legacy_importer.import_legacy_sqlite(
        source_path=source,
        source_table="students",
        organization_name="Students Legacy Org",
        organization_slug="students-legacy-org",
        location_name="Legacy Location",
        location_code="LEGACY",
        owner_email=None,
        dry_run=False,
    )

    product = database_session.scalar(
        select(Product).where(Product.sku == "LEGACY-students-7")
    )
    batch = database_session.scalar(
        select(Batch).where(Batch.batch_number == "LEGACY-students-7")
    )

    assert report.imported == 1
    assert report.failed == 0
    assert product is not None
    assert product.name == "Old Apple"
    assert product.category == "Fruit"
    assert batch is not None
    assert batch.quantity_received == 4
    assert batch.notes == "legacy note"
