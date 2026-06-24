from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import InventoryServiceDependency
from app.domain.enums import BatchStatus
from app.schemas.batch import BatchCreate, BatchRead, BatchUpdate
from app.schemas.common import Page

router = APIRouter(prefix="/batches")


@router.post(
    "", response_model=BatchRead, status_code=status.HTTP_201_CREATED,
    summary="Register an inventory batch",
)
def create_batch(payload: BatchCreate, service: InventoryServiceDependency) -> BatchRead:
    return service.create_batch(payload)


@router.get("", response_model=Page[BatchRead], summary="List inventory batches")
def list_batches(
    service: InventoryServiceDependency,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum records to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Matching records to skip.")] = 0,
    organization_id: Annotated[
        UUID | None, Query(description="Only batches owned by this organization.")
    ] = None,
    product_id: Annotated[
        UUID | None, Query(description="Only batches for this catalog product.")
    ] = None,
    location_id: Annotated[
        UUID | None, Query(description="Only batches currently held at this location.")
    ] = None,
    batch_status: Annotated[
        BatchStatus | None, Query(alias="status", description="Only batches in this lifecycle status.")
    ] = None,
    expiry_date: Annotated[
        date | None, Query(description="Only batches expiring on this exact date.")
    ] = None,
    expires_from: Annotated[
        date | None, Query(description="Include batches expiring on or after this date.")
    ] = None,
    expires_to: Annotated[
        date | None, Query(description="Include batches expiring on or before this date.")
    ] = None,
) -> Page[BatchRead]:
    page = service.list_batches(
        limit=limit, offset=offset, organization_id=organization_id,
        product_id=product_id, location_id=location_id, status=batch_status,
        expiry_date=expiry_date, expires_from=expires_from, expires_to=expires_to,
    )
    return Page[BatchRead].model_validate(page)


@router.get("/{batch_id}", response_model=BatchRead, summary="Get an inventory batch")
def get_batch(batch_id: UUID, service: InventoryServiceDependency) -> BatchRead:
    return service.get_batch(batch_id)


@router.patch("/{batch_id}", response_model=BatchRead, summary="Update an inventory batch")
def update_batch(
    batch_id: UUID, payload: BatchUpdate, service: InventoryServiceDependency
) -> BatchRead:
    return service.update_batch(batch_id, payload)


@router.delete(
    "/{batch_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an inventory batch",
)
def delete_batch(batch_id: UUID, service: InventoryServiceDependency) -> Response:
    service.delete_batch(batch_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
