from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    """Fields required to create an inventory storage location."""

    organization_id: UUID = Field(description="Organization that owns this location.")
    name: str = Field(
        min_length=1, max_length=120,
        description="Human-readable warehouse, shop, or storage-area name.",
        examples=["Downtown Store"],
    )
    code: str = Field(
        min_length=1, max_length=32,
        description="Organization-scoped short location code.", examples=["DT-01"],
    )
    timezone: str = Field(
        default="UTC", min_length=1, max_length=64,
        description="IANA time-zone name used for local scheduling and reporting.",
        examples=["America/New_York"],
    )
    address: str | None = Field(
        default=None, max_length=1000,
        description="Optional postal address or internal storage directions.",
    )
    is_active: bool = Field(
        default=True, description="Whether new inventory may be assigned to this location."
    )


class LocationUpdate(BaseModel):
    """Mutable location fields; organization ownership cannot be changed."""

    name: str | None = Field(
        default=None, min_length=1, max_length=120,
        description="Replacement human-readable location name.",
    )
    code: str | None = Field(
        default=None, min_length=1, max_length=32,
        description="Replacement organization-scoped location code.",
    )
    timezone: str | None = Field(
        default=None, min_length=1, max_length=64,
        description="Replacement IANA time-zone name.",
    )
    address: str | None = Field(
        default=None, max_length=1000,
        description="Replacement address; null clears the value.",
    )
    is_active: bool | None = Field(
        default=None, description="Replacement active assignment status."
    )


class LocationRead(BaseModel):
    """Inventory storage location returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable public location identifier.")
    organization_id: UUID = Field(description="Organization that owns the location.")
    name: str = Field(description="Human-readable location name.")
    code: str = Field(description="Organization-scoped short location code.")
    timezone: str = Field(description="IANA time-zone name for local operations.")
    address: str | None = Field(description="Optional postal or internal address.")
    is_active: bool = Field(description="Whether new inventory may use this location.")
    created_at: datetime = Field(description="UTC timestamp when the location was created.")
    updated_at: datetime = Field(description="UTC timestamp of the latest location update.")
