from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, DomainValidationError, ResourceNotFoundError
from app.db.models import Batch, Location, Organization, OrganizationMembership, Product
from app.domain.enums import BatchStatus, OrganizationRole, ProductStatus
from app.repositories.inventory import InventoryRepository, PageResult
from app.schemas.batch import BatchCreate, BatchUpdate
from app.schemas.location import LocationCreate, LocationUpdate
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.authorization import AuthorizationService


class InventoryService:
    def __init__(
        self,
        repository: InventoryRepository,
        authorization: AuthorizationService,
    ) -> None:
        self.repository = repository
        self.authorization = authorization

    def create_organization(self, payload: OrganizationCreate) -> Organization:
        organization = self._persist(
            Organization(**payload.model_dump()), "Organization slug already exists."
        )
        self.authorization.repository.add(
            OrganizationMembership(
                organization_id=organization.id,
                user_id=self.authorization.actor.id,
                role=OrganizationRole.OWNER.value,
            )
        )
        self.authorization.audit(
            organization_id=organization.id,
            action="organization.created",
            resource_type="organization",
            resource_id=organization.id,
        )
        return organization

    def get_organization(self, organization_id: UUID) -> Organization:
        organization = self.repository.get_organization(organization_id)
        if organization is None:
            raise ResourceNotFoundError("Organization", organization_id)
        self.authorization.require_role(organization_id, OrganizationRole.VIEWER)
        return organization

    def list_organizations(
        self, *, limit: int, offset: int, name: str | None
    ) -> PageResult[Organization]:
        return self.repository.list_organizations(
            limit=limit,
            offset=offset,
            name=name,
            organization_ids=self.authorization.organization_ids(),
        )

    def update_organization(
        self, organization_id: UUID, payload: OrganizationUpdate
    ) -> Organization:
        self.authorization.require_role(organization_id, OrganizationRole.ADMIN)
        organization = self.get_organization(organization_id)
        changes = payload.model_dump(exclude_unset=True)
        self._reject_nulls(changes, {"name", "slug"})
        self._apply(organization, changes)
        organization = self._flush(organization, "Organization slug already exists.")
        self.authorization.audit(
            organization_id=organization.id,
            action="organization.updated",
            resource_type="organization",
            resource_id=organization.id,
            details={"fields": sorted(changes)},
        )
        return organization

    def delete_organization(self, organization_id: UUID) -> None:
        self.authorization.require_role(organization_id, OrganizationRole.OWNER)
        organization = self.get_organization(organization_id)
        self.authorization.audit(
            organization_id=organization_id,
            action="organization.deleted",
            resource_type="organization",
            resource_id=organization_id,
        )
        self.repository.delete(organization)

    def create_product(self, payload: ProductCreate) -> Product:
        self.authorization.require_role(
            payload.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        self.get_organization(payload.organization_id)
        values = payload.model_dump(exclude={"metadata"})
        values["status"] = payload.status.value
        values["attributes"] = payload.metadata
        product = self._persist(
            Product(**values), "A product with this SKU already exists in the organization."
        )
        self.authorization.audit(
            organization_id=product.organization_id,
            action="product.created",
            resource_type="product",
            resource_id=product.id,
        )
        return product

    def get_product(self, product_id: UUID) -> Product:
        product = self.repository.get_product(product_id)
        if product is None:
            raise ResourceNotFoundError("Product", product_id)
        self.authorization.require_role(product.organization_id, OrganizationRole.VIEWER)
        return product

    def list_products(
        self, *, limit: int, offset: int, organization_id: UUID | None,
        status: ProductStatus | None, category: str | None, search: str | None,
    ) -> PageResult[Product]:
        organization_ids = self._readable_organizations(organization_id)
        return self.repository.list_products(
            limit=limit, offset=offset, organization_id=organization_id,
            status=status.value if status else None, category=category, search=search,
            organization_ids=organization_ids,
        )

    def update_product(self, product_id: UUID, payload: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        self.authorization.require_role(
            product.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        changes = payload.model_dump(exclude_unset=True, exclude={"metadata"})
        self._reject_nulls(changes, {"sku", "name", "status"})
        if isinstance(changes.get("status"), ProductStatus):
            changes["status"] = changes["status"].value
        if "metadata" in payload.model_fields_set:
            changes["attributes"] = payload.metadata or {}
        self._apply(product, changes)
        product = self._flush(
            product, "A product with this SKU already exists in the organization."
        )
        self.authorization.audit(
            organization_id=product.organization_id,
            action="product.updated",
            resource_type="product",
            resource_id=product.id,
            details={"fields": sorted(changes)},
        )
        return product

    def delete_product(self, product_id: UUID) -> None:
        product = self.get_product(product_id)
        self.authorization.require_role(
            product.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        try:
            self.repository.delete(product)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError("Products with inventory batches cannot be deleted; archive them instead.") from error
        self.authorization.audit(
            organization_id=product.organization_id,
            action="product.deleted",
            resource_type="product",
            resource_id=product_id,
        )

    def create_location(self, payload: LocationCreate) -> Location:
        self.authorization.require_role(
            payload.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        self.get_organization(payload.organization_id)
        location = self._persist(
            Location(**payload.model_dump()),
            "A location with this code already exists in the organization.",
        )
        self.authorization.audit(
            organization_id=location.organization_id,
            action="location.created",
            resource_type="location",
            resource_id=location.id,
        )
        return location

    def get_location(self, location_id: UUID) -> Location:
        location = self.repository.get_location(location_id)
        if location is None:
            raise ResourceNotFoundError("Location", location_id)
        self.authorization.require_role(location.organization_id, OrganizationRole.VIEWER)
        return location

    def list_locations(
        self, *, limit: int, offset: int, organization_id: UUID | None,
        is_active: bool | None, name: str | None,
    ) -> PageResult[Location]:
        organization_ids = self._readable_organizations(organization_id)
        return self.repository.list_locations(
            limit=limit, offset=offset, organization_id=organization_id,
            is_active=is_active, name=name,
            organization_ids=organization_ids,
        )

    def update_location(self, location_id: UUID, payload: LocationUpdate) -> Location:
        location = self.get_location(location_id)
        self.authorization.require_role(
            location.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        changes = payload.model_dump(exclude_unset=True)
        self._reject_nulls(changes, {"name", "code", "timezone", "is_active"})
        self._apply(location, changes)
        location = self._flush(
            location, "A location with this code already exists in the organization."
        )
        self.authorization.audit(
            organization_id=location.organization_id,
            action="location.updated",
            resource_type="location",
            resource_id=location.id,
            details={"fields": sorted(changes)},
        )
        return location

    def delete_location(self, location_id: UUID) -> None:
        location = self.get_location(location_id)
        self.authorization.require_role(
            location.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        try:
            self.repository.delete(location)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError("Locations holding inventory batches cannot be deleted; deactivate them instead.") from error
        self.authorization.audit(
            organization_id=location.organization_id,
            action="location.deleted",
            resource_type="location",
            resource_id=location_id,
        )

    def create_batch(self, payload: BatchCreate) -> Batch:
        self.authorization.require_role(
            payload.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        self.get_organization(payload.organization_id)
        product = self.get_product(payload.product_id)
        location = self.get_location(payload.location_id)
        self._validate_batch_tenant(payload.organization_id, product, location)
        values = payload.model_dump()
        values["status"] = payload.status.value
        batch = self._persist(
            Batch(**values), "This product already has a batch with the supplied batch number."
        )
        self.authorization.audit(
            organization_id=batch.organization_id,
            action="batch.created",
            resource_type="batch",
            resource_id=batch.id,
        )
        return batch

    def get_batch(self, batch_id: UUID) -> Batch:
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise ResourceNotFoundError("Batch", batch_id)
        self.authorization.require_role(batch.organization_id, OrganizationRole.VIEWER)
        return batch

    def list_batches(
        self, *, limit: int, offset: int, organization_id: UUID | None,
        product_id: UUID | None, location_id: UUID | None,
        status: BatchStatus | None, expiry_date: date | None,
        expires_from: date | None, expires_to: date | None,
    ) -> PageResult[Batch]:
        if expires_from and expires_to and expires_from > expires_to:
            raise DomainValidationError("expires_from cannot be later than expires_to.")
        organization_ids = self._readable_organizations(organization_id)
        return self.repository.list_batches(
            limit=limit, offset=offset, organization_id=organization_id,
            product_id=product_id, location_id=location_id,
            status=status.value if status else None, expiry_date=expiry_date,
            expires_from=expires_from, expires_to=expires_to,
            organization_ids=organization_ids,
        )

    def update_batch(self, batch_id: UUID, payload: BatchUpdate) -> Batch:
        batch = self.get_batch(batch_id)
        self.authorization.require_role(
            batch.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        changes = payload.model_dump(exclude_unset=True)
        self._reject_nulls(
            changes,
            {"location_id", "batch_number", "quantity_received", "quantity_available",
             "expiry_date", "received_date", "status"},
        )
        if "location_id" in changes:
            location = self.get_location(changes["location_id"])
            if location.organization_id != batch.organization_id:
                raise DomainValidationError("Batch and location must belong to the same organization.")
        received = changes.get("quantity_received", batch.quantity_received)
        available = changes.get("quantity_available", batch.quantity_available)
        if available > received:
            raise DomainValidationError("quantity_available cannot exceed quantity_received.")
        if isinstance(changes.get("status"), BatchStatus):
            changes["status"] = changes["status"].value
        self._apply(batch, changes)
        batch = self._flush(
            batch, "This product already has a batch with the supplied batch number."
        )
        self.authorization.audit(
            organization_id=batch.organization_id,
            action="batch.updated",
            resource_type="batch",
            resource_id=batch.id,
            details={"fields": sorted(changes)},
        )
        return batch

    def delete_batch(self, batch_id: UUID) -> None:
        batch = self.get_batch(batch_id)
        self.authorization.require_role(
            batch.organization_id, OrganizationRole.INVENTORY_MANAGER
        )
        self.repository.delete(batch)
        self.authorization.audit(
            organization_id=batch.organization_id,
            action="batch.deleted",
            resource_type="batch",
            resource_id=batch_id,
        )

    def _persist(self, model: object, conflict_message: str):
        try:
            return self.repository.add(model)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError(conflict_message) from error

    def _flush(self, model: object, conflict_message: str):
        try:
            return self.repository.flush(model)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError(conflict_message) from error

    @staticmethod
    def _apply(model: object, changes: dict[str, object]) -> None:
        for field, value in changes.items():
            setattr(model, field, value)

    @staticmethod
    def _reject_nulls(changes: dict[str, object], required_fields: set[str]) -> None:
        invalid = sorted(field for field in required_fields if field in changes and changes[field] is None)
        if invalid:
            raise DomainValidationError(f"Fields cannot be null: {', '.join(invalid)}.")

    @staticmethod
    def _validate_batch_tenant(
        organization_id: UUID, product: Product, location: Location
    ) -> None:
        if product.organization_id != organization_id:
            raise DomainValidationError("Batch and product must belong to the same organization.")
        if location.organization_id != organization_id:
            raise DomainValidationError("Batch and location must belong to the same organization.")

    def _readable_organizations(self, organization_id: UUID | None) -> list[UUID]:
        if organization_id is not None:
            self.authorization.require_role(organization_id, OrganizationRole.VIEWER)
            return [organization_id]
        return self.authorization.organization_ids()
