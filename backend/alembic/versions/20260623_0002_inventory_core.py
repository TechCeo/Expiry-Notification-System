"""Create organizations, products, locations, and inventory batches.

Revision ID: 20260623_0002
Revises: 20260623_0001
Create Date: 2026-06-23
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260623_0002"
down_revision: str | Sequence[str] | None = "20260623_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=63), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_organizations"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'archived')", name="ck_products_product_status_valid"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            name="fk_products_organization_id_organizations", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint(
            "organization_id", "sku", name="uq_products_organization_sku"
        ),
    )
    op.create_index("ix_products_category", "products", ["category"], unique=False)
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_organization_id", "products", ["organization_id"], unique=False)
    op.create_index(
        "ix_products_organization_status", "products", ["organization_id", "status"], unique=False
    )

    op.create_table(
        "locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            name="fk_locations_organization_id_organizations", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_locations"),
        sa.UniqueConstraint(
            "organization_id", "code", name="uq_locations_organization_code"
        ),
    )
    op.create_index("ix_locations_name", "locations", ["name"], unique=False)
    op.create_index("ix_locations_organization_id", "locations", ["organization_id"], unique=False)
    op.create_index(
        "ix_locations_organization_active", "locations", ["organization_id", "is_active"], unique=False
    )

    op.create_table(
        "batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_number", sa.String(length=64), nullable=False),
        sa.Column("quantity_received", sa.Integer(), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'depleted', 'quarantined', 'expired')",
            name="ck_batches_batch_status_valid",
        ),
        sa.CheckConstraint(
            "quantity_available <= quantity_received",
            name="ck_batches_quantity_available_within_received",
        ),
        sa.CheckConstraint(
            "quantity_available >= 0", name="ck_batches_quantity_available_nonnegative"
        ),
        sa.CheckConstraint(
            "quantity_received >= 0", name="ck_batches_quantity_received_nonnegative"
        ),
        sa.ForeignKeyConstraint(
            ["location_id"], ["locations.id"],
            name="fk_batches_location_id_locations", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"],
            name="fk_batches_organization_id_organizations", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"],
            name="fk_batches_product_id_products", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_batches"),
        sa.UniqueConstraint(
            "organization_id", "product_id", "batch_number",
            name="uq_batches_organization_product_number",
        ),
    )
    op.create_index("ix_batches_location_id", "batches", ["location_id"], unique=False)
    op.create_index(
        "ix_batches_location_status", "batches", ["location_id", "status"], unique=False
    )
    op.create_index("ix_batches_organization_id", "batches", ["organization_id"], unique=False)
    op.create_index(
        "ix_batches_organization_expiry", "batches", ["organization_id", "expiry_date"], unique=False
    )
    op.create_index("ix_batches_product_id", "batches", ["product_id"], unique=False)
    op.create_index(
        "ix_batches_product_expiry", "batches", ["product_id", "expiry_date"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_batches_product_expiry", table_name="batches")
    op.drop_index("ix_batches_product_id", table_name="batches")
    op.drop_index("ix_batches_organization_expiry", table_name="batches")
    op.drop_index("ix_batches_organization_id", table_name="batches")
    op.drop_index("ix_batches_location_status", table_name="batches")
    op.drop_index("ix_batches_location_id", table_name="batches")
    op.drop_table("batches")

    op.drop_index("ix_locations_organization_active", table_name="locations")
    op.drop_index("ix_locations_organization_id", table_name="locations")
    op.drop_index("ix_locations_name", table_name="locations")
    op.drop_table("locations")

    op.drop_index("ix_products_organization_status", table_name="products")
    op.drop_index("ix_products_organization_id", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_table("products")

    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")
