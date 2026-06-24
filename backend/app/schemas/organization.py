from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    """Fields required to create an inventory-owning organization."""

    name: str = Field(
        min_length=1, max_length=120,
        description="Human-readable legal or trading name of the organization.",
        examples=["Northside Grocers"],
    )
    slug: str = Field(
        min_length=2, max_length=63, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Globally unique, URL-safe organization identifier.",
        examples=["northside-grocers"],
    )


class OrganizationUpdate(BaseModel):
    """Mutable organization fields; omitted fields remain unchanged."""

    name: str | None = Field(
        default=None, min_length=1, max_length=120,
        description="Replacement human-readable organization name.",
    )
    slug: str | None = Field(
        default=None, min_length=2, max_length=63,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Replacement globally unique URL-safe identifier.",
    )


class OrganizationRead(BaseModel):
    """Organization resource returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable public organization identifier.")
    name: str = Field(description="Human-readable organization name.")
    slug: str = Field(description="Globally unique URL-safe organization identifier.")
    created_at: datetime = Field(description="UTC timestamp when the organization was created.")
    updated_at: datetime = Field(description="UTC timestamp of the latest organization update.")
