from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ProductStatus


class ProductCreate(BaseModel):
    """Fields required to add a product to an organization's catalog."""

    organization_id: UUID = Field(description="Organization that owns this product.")
    sku: str = Field(
        min_length=1, max_length=64,
        description="Organization-scoped stock keeping unit.", examples=["BEV-COLA-500"],
    )
    name: str = Field(
        min_length=1, max_length=120,
        description="Human-readable product name.", examples=["Cola 500 ml"],
    )
    description: str | None = Field(
        default=None, max_length=2000,
        description="Optional long-form product description.",
    )
    category: str | None = Field(
        default=None, min_length=1, max_length=80,
        description="Optional category used to group and filter products.",
        examples=["Beverages"],
    )
    status: ProductStatus = Field(
        default=ProductStatus.ACTIVE,
        description="Catalog lifecycle status; archived products remain historically visible.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Flexible product attributes such as brand, size, or barcode.",
        examples=[{"brand": "Acme", "volume_ml": 500}],
    )


class ProductUpdate(BaseModel):
    """Mutable product fields; organization ownership cannot be changed."""

    sku: str | None = Field(
        default=None, min_length=1, max_length=64,
        description="Replacement organization-scoped stock keeping unit.",
    )
    name: str | None = Field(
        default=None, min_length=1, max_length=120,
        description="Replacement human-readable product name.",
    )
    description: str | None = Field(
        default=None, max_length=2000,
        description="Replacement product description; null clears the value.",
    )
    category: str | None = Field(
        default=None, max_length=80,
        description="Replacement category; null clears the value.",
    )
    status: ProductStatus | None = Field(
        default=None, description="Replacement catalog lifecycle status."
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Replacement flexible product attribute document."
    )


class ProductRead(BaseModel):
    """Product catalog resource returned by the API."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID = Field(description="Stable public product identifier.")
    organization_id: UUID = Field(description="Organization that owns the product.")
    sku: str = Field(description="Organization-scoped stock keeping unit.")
    name: str = Field(description="Human-readable product name.")
    description: str | None = Field(description="Optional long-form product description.")
    category: str | None = Field(description="Optional product category.")
    status: ProductStatus = Field(description="Current product lifecycle status.")
    metadata: dict[str, Any] = Field(
        validation_alias="attributes",
        serialization_alias="metadata",
        description="Flexible product attributes stored as PostgreSQL JSONB.",
    )
    created_at: datetime = Field(description="UTC timestamp when the product was created.")
    updated_at: datetime = Field(description="UTC timestamp of the latest product update.")
