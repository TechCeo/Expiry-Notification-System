from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.audit_event import AuditEvent
    from app.db.models.batch import Batch
    from app.db.models.location import Location
    from app.db.models.product import Product
    from app.db.models.membership import OrganizationMembership


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(63), nullable=False, unique=True, index=True)

    products: Mapped[list[Product]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    locations: Mapped[list[Location]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    batches: Mapped[list[Batch]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    memberships: Mapped[list[OrganizationMembership]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list[AuditEvent]] = relationship(back_populates="organization")
