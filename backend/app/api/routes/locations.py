from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import InventoryServiceDependency
from app.schemas.common import Page
from app.schemas.location import LocationCreate, LocationRead, LocationUpdate

router = APIRouter(prefix="/locations")


@router.post(
    "", response_model=LocationRead, status_code=status.HTTP_201_CREATED,
    summary="Create an inventory location",
)
def create_location(payload: LocationCreate, service: InventoryServiceDependency) -> LocationRead:
    return service.create_location(payload)


@router.get("", response_model=Page[LocationRead], summary="List inventory locations")
def list_locations(
    service: InventoryServiceDependency,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum records to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Matching records to skip.")] = 0,
    organization_id: Annotated[
        UUID | None, Query(description="Only locations owned by this organization.")
    ] = None,
    is_active: Annotated[
        bool | None, Query(description="Filter by active inventory-assignment status.")
    ] = None,
    name: Annotated[
        str | None, Query(min_length=1, max_length=120, description="Case-insensitive name fragment.")
    ] = None,
) -> Page[LocationRead]:
    page = service.list_locations(
        limit=limit, offset=offset, organization_id=organization_id,
        is_active=is_active, name=name,
    )
    return Page[LocationRead].model_validate(page)


@router.get("/{location_id}", response_model=LocationRead, summary="Get an inventory location")
def get_location(location_id: UUID, service: InventoryServiceDependency) -> LocationRead:
    return service.get_location(location_id)


@router.patch("/{location_id}", response_model=LocationRead, summary="Update an inventory location")
def update_location(
    location_id: UUID, payload: LocationUpdate, service: InventoryServiceDependency
) -> LocationRead:
    return service.update_location(location_id, payload)


@router.delete(
    "/{location_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a location without inventory history",
)
def delete_location(location_id: UUID, service: InventoryServiceDependency) -> Response:
    service.delete_location(location_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
