from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import InventoryServiceDependency
from app.domain.enums import ProductStatus
from app.schemas.common import Page
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products")


@router.post(
    "", response_model=ProductRead, status_code=status.HTTP_201_CREATED,
    summary="Create a catalog product",
)
def create_product(payload: ProductCreate, service: InventoryServiceDependency) -> ProductRead:
    return service.create_product(payload)


@router.get("", response_model=Page[ProductRead], summary="List catalog products")
def list_products(
    service: InventoryServiceDependency,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum records to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Matching records to skip.")] = 0,
    organization_id: Annotated[
        UUID | None, Query(description="Only products owned by this organization.")
    ] = None,
    product_status: Annotated[
        ProductStatus | None, Query(alias="status", description="Only products in this lifecycle status.")
    ] = None,
    category: Annotated[
        str | None, Query(min_length=1, max_length=80, description="Exact product category.")
    ] = None,
    search: Annotated[
        str | None, Query(min_length=1, max_length=120, description="Case-insensitive SKU or name fragment.")
    ] = None,
) -> Page[ProductRead]:
    page = service.list_products(
        limit=limit, offset=offset, organization_id=organization_id,
        status=product_status, category=category, search=search,
    )
    return Page[ProductRead].model_validate(page)


@router.get("/{product_id}", response_model=ProductRead, summary="Get a catalog product")
def get_product(product_id: UUID, service: InventoryServiceDependency) -> ProductRead:
    return service.get_product(product_id)


@router.patch("/{product_id}", response_model=ProductRead, summary="Update a catalog product")
def update_product(
    product_id: UUID, payload: ProductUpdate, service: InventoryServiceDependency
) -> ProductRead:
    return service.update_product(product_id, payload)


@router.delete(
    "/{product_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product without inventory history",
)
def delete_product(product_id: UUID, service: InventoryServiceDependency) -> Response:
    service.delete_product(product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
