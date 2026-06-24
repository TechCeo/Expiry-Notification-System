from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.enums import BatchStatus


class BatchCreate(BaseModel):
    """Fields required to register a physical inventory batch."""

    organization_id: UUID = Field(description="Organization that owns this inventory batch.")
    product_id: UUID = Field(description="Catalog product represented by this batch.")
    location_id: UUID = Field(description="Location currently holding this batch.")
    batch_number: str = Field(
        min_length=1, max_length=64,
        description="Supplier or internally assigned batch/lot number.", examples=["LOT-2026-0042"],
    )
    quantity_received: int = Field(
        ge=0, description="Total units originally received in this batch.", examples=[100]
    )
    quantity_available: int = Field(
        ge=0, description="Units currently available for use or sale.", examples=[87]
    )
    expiry_date: date = Field(
        description="Calendar date after which this batch is considered expired.",
        examples=["2026-12-31"],
    )
    received_date: date = Field(
        description="Calendar date on which the batch entered inventory.",
        examples=["2026-06-23"],
    )
    status: BatchStatus = Field(
        default=BatchStatus.ACTIVE, description="Operational lifecycle status of the batch."
    )
    notes: str | None = Field(
        default=None, max_length=2000,
        description="Optional handling, supplier, or inspection notes.",
    )

    @model_validator(mode="after")
    def quantities_are_consistent(self) -> "BatchCreate":
        if self.quantity_available > self.quantity_received:
            raise ValueError("quantity_available cannot exceed quantity_received")
        return self


class BatchUpdate(BaseModel):
    """Mutable inventory-batch fields; organization and product are immutable."""

    location_id: UUID | None = Field(
        default=None, description="Replacement location holding the batch."
    )
    batch_number: str | None = Field(
        default=None, min_length=1, max_length=64,
        description="Replacement supplier or internal batch/lot number.",
    )
    quantity_received: int | None = Field(
        default=None, ge=0, description="Replacement total quantity received."
    )
    quantity_available: int | None = Field(
        default=None, ge=0, description="Replacement currently available quantity."
    )
    expiry_date: date | None = Field(
        default=None, description="Replacement batch expiration date."
    )
    received_date: date | None = Field(
        default=None, description="Replacement inventory receipt date."
    )
    status: BatchStatus | None = Field(
        default=None, description="Replacement operational batch status."
    )
    notes: str | None = Field(
        default=None, max_length=2000,
        description="Replacement notes; null clears the value.",
    )


class BatchRead(BaseModel):
    """Physical inventory batch returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable public batch identifier.")
    organization_id: UUID = Field(description="Organization that owns the batch.")
    product_id: UUID = Field(description="Catalog product represented by the batch.")
    location_id: UUID = Field(description="Location currently holding the batch.")
    batch_number: str = Field(description="Supplier or internal batch/lot number.")
    quantity_received: int = Field(description="Total units originally received.")
    quantity_available: int = Field(description="Units currently available for use or sale.")
    expiry_date: date = Field(description="Calendar date when the batch expires.")
    received_date: date = Field(description="Calendar date when inventory was received.")
    status: BatchStatus = Field(description="Current operational batch status.")
    notes: str | None = Field(description="Optional handling or inspection notes.")
    created_at: datetime = Field(description="UTC timestamp when the batch was created.")
    updated_at: datetime = Field(description="UTC timestamp of the latest batch update.")
