from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

ItemT = TypeVar("ItemT")


class Page(BaseModel, Generic[ItemT]):
    """Offset-based page returned by collection endpoints."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ItemT] = Field(description="Resources contained in the requested page.")
    total: int = Field(
        ge=0, description="Total resources matching the filters before pagination."
    )
    limit: int = Field(
        ge=1, description="Maximum number of resources requested for this page."
    )
    offset: int = Field(
        ge=0, description="Number of matching resources skipped before this page."
    )
