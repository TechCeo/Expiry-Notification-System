from dataclasses import dataclass
from datetime import date
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Batch, Location, Organization, Product

ModelT = TypeVar("ModelT")


@dataclass(frozen=True, slots=True)
class PageResult(Generic[ModelT]):
    items: list[ModelT]
    total: int
    limit: int
    offset: int


class InventoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, model: ModelT) -> ModelT:
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return model

    def flush(self, model: ModelT) -> ModelT:
        self.session.flush()
        self.session.refresh(model)
        return model

    def delete(self, model: object) -> None:
        self.session.delete(model)
        self.session.flush()

    def get_organization(self, organization_id: UUID) -> Organization | None:
        return self.session.get(Organization, organization_id)

    def list_organizations(
        self, *, limit: int, offset: int, name: str | None,
        organization_ids: list[UUID],
    ) -> PageResult[Organization]:
        filters = [Organization.id.in_(organization_ids)]
        if name:
            filters.append(Organization.name.ilike(f"%{name}%"))
        return self._page(
            Organization, filters, (Organization.name.asc(), Organization.id.asc()),
            limit=limit, offset=offset
        )

    def get_product(self, product_id: UUID) -> Product | None:
        return self.session.get(Product, product_id)

    def list_products(
        self,
        *,
        limit: int,
        offset: int,
        organization_id: UUID | None,
        status: str | None,
        category: str | None,
        search: str | None,
        organization_ids: list[UUID],
    ) -> PageResult[Product]:
        filters = [Product.organization_id.in_(organization_ids)]
        if organization_id:
            filters.append(Product.organization_id == organization_id)
        if status:
            filters.append(Product.status == status)
        if category:
            filters.append(Product.category == category)
        if search:
            term = f"%{search}%"
            filters.append(or_(Product.name.ilike(term), Product.sku.ilike(term)))
        return self._page(
            Product, filters, (Product.name.asc(), Product.id.asc()), limit=limit, offset=offset
        )

    def get_location(self, location_id: UUID) -> Location | None:
        return self.session.get(Location, location_id)

    def list_locations(
        self,
        *,
        limit: int,
        offset: int,
        organization_id: UUID | None,
        is_active: bool | None,
        name: str | None,
        organization_ids: list[UUID],
    ) -> PageResult[Location]:
        filters = [Location.organization_id.in_(organization_ids)]
        if organization_id:
            filters.append(Location.organization_id == organization_id)
        if is_active is not None:
            filters.append(Location.is_active.is_(is_active))
        if name:
            filters.append(Location.name.ilike(f"%{name}%"))
        return self._page(
            Location, filters, (Location.name.asc(), Location.id.asc()),
            limit=limit, offset=offset
        )

    def get_batch(self, batch_id: UUID) -> Batch | None:
        return self.session.get(Batch, batch_id)

    def list_batches(
        self,
        *,
        limit: int,
        offset: int,
        organization_id: UUID | None,
        product_id: UUID | None,
        location_id: UUID | None,
        status: str | None,
        expiry_date: date | None,
        expires_from: date | None,
        expires_to: date | None,
        organization_ids: list[UUID],
    ) -> PageResult[Batch]:
        filters = [Batch.organization_id.in_(organization_ids)]
        if organization_id:
            filters.append(Batch.organization_id == organization_id)
        if product_id:
            filters.append(Batch.product_id == product_id)
        if location_id:
            filters.append(Batch.location_id == location_id)
        if status:
            filters.append(Batch.status == status)
        if expiry_date:
            filters.append(Batch.expiry_date == expiry_date)
        if expires_from:
            filters.append(Batch.expiry_date >= expires_from)
        if expires_to:
            filters.append(Batch.expiry_date <= expires_to)
        return self._page(
            Batch, filters, (Batch.expiry_date.asc(), Batch.id.asc()),
            limit=limit, offset=offset
        )

    def _page(
        self,
        model: type[ModelT],
        filters: list[object],
        order_by: tuple[object, ...],
        *,
        limit: int,
        offset: int,
    ) -> PageResult[ModelT]:
        total = self.session.scalar(
            select(func.count()).select_from(model).where(*filters)
        ) or 0
        items = list(
            self.session.scalars(
                select(model).where(*filters).order_by(*order_by).limit(limit).offset(offset)
            ).all()
        )
        return PageResult(items=items, total=total, limit=limit, offset=offset)
