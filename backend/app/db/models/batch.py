from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.domain.enums import BatchStatus

if TYPE_CHECKING:
    from app.db.models.location import Location
    from app.db.models.organization import Organization
    from app.db.models.product import Product


class Batch(TimestampMixin, Base):
    __tablename__ = "batches"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "product_id", "batch_number",
            name="uq_batches_organization_product_number",
        ),
        CheckConstraint("quantity_received >= 0", name="quantity_received_nonnegative"),
        CheckConstraint("quantity_available >= 0", name="quantity_available_nonnegative"),
        CheckConstraint(
            "quantity_available <= quantity_received", name="quantity_available_within_received"
        ),
        CheckConstraint(
            "status IN ('active', 'depleted', 'quarantined', 'expired')",
            name="batch_status_valid",
        ),
        Index("ix_batches_organization_expiry", "organization_id", "expiry_date"),
        Index("ix_batches_product_expiry", "product_id", "expiry_date"),
        Index("ix_batches_location_status", "location_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity_received: Mapped[int] = mapped_column(nullable=False)
    quantity_available: Mapped[int] = mapped_column(nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=BatchStatus.ACTIVE.value
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="batches")
    product: Mapped[Product] = relationship(back_populates="batches")
    location: Mapped[Location] = relationship(back_populates="batches")
