from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import InventoryServiceDependency
from app.schemas.common import Page
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate

router = APIRouter(prefix="/organizations")


@router.post(
    "", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED,
    summary="Create an organization",
)
def create_organization(
    payload: OrganizationCreate, service: InventoryServiceDependency
) -> OrganizationRead:
    return service.create_organization(payload)


@router.get("", response_model=Page[OrganizationRead], summary="List organizations")
def list_organizations(
    service: InventoryServiceDependency,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum records to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Matching records to skip.")] = 0,
    name: Annotated[
        str | None, Query(min_length=1, max_length=120, description="Case-insensitive name fragment.")
    ] = None,
) -> Page[OrganizationRead]:
    page = service.list_organizations(limit=limit, offset=offset, name=name)
    return Page[OrganizationRead].model_validate(page)


@router.get("/{organization_id}", response_model=OrganizationRead, summary="Get an organization")
def get_organization(
    organization_id: UUID, service: InventoryServiceDependency
) -> OrganizationRead:
    return service.get_organization(organization_id)


@router.patch(
    "/{organization_id}", response_model=OrganizationRead, summary="Update an organization"
)
def update_organization(
    organization_id: UUID,
    payload: OrganizationUpdate,
    service: InventoryServiceDependency,
) -> OrganizationRead:
    return service.update_organization(organization_id, payload)


@router.delete(
    "/{organization_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an organization and its inventory",
)
def delete_organization(
    organization_id: UUID, service: InventoryServiceDependency
) -> Response:
    service.delete_organization(organization_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
