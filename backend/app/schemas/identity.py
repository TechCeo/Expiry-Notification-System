from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import OrganizationRole


class UserRead(BaseModel):
    """OIDC-backed application user; password credentials are never stored."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable internal user identifier.")
    email: EmailStr | None = Field(description="Email asserted by the identity provider.")
    email_verified: bool = Field(
        description="Whether the identity provider explicitly verified the email address."
    )
    display_name: str | None = Field(description="Display name asserted by the identity provider.")
    is_active: bool = Field(description="Whether the account may access the API.")
    created_at: datetime = Field(description="UTC timestamp when the user first authenticated.")
    updated_at: datetime = Field(description="UTC timestamp of the latest profile synchronization.")


class MembershipSummary(BaseModel):
    """Current user's role in one organization."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable membership identifier.")
    organization_id: UUID = Field(description="Organization covered by this membership.")
    role: OrganizationRole = Field(description="Role granted to the user in this organization.")


class CurrentUserRead(UserRead):
    """Authenticated user profile and organization access."""

    memberships: list[MembershipSummary] = Field(
        description="Organization memberships currently granted to the authenticated user."
    )


class MembershipCreate(BaseModel):
    """Request to grant an existing OIDC user organization access."""

    user_email: EmailStr = Field(
        description="Email of a user who has authenticated at least once.",
        examples=["manager@example.com"],
    )
    role: OrganizationRole = Field(description="Organization role to grant to the user.")


class MembershipUpdate(BaseModel):
    """Request to replace an existing membership role."""

    role: OrganizationRole = Field(description="Replacement organization role.")


class MembershipRead(BaseModel):
    """Organization membership with the associated user profile."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable membership identifier.")
    organization_id: UUID = Field(description="Organization covered by the membership.")
    user_id: UUID = Field(description="User receiving organization access.")
    role: OrganizationRole = Field(description="Role granted within the organization.")
    user: UserRead = Field(description="OIDC-backed profile for the member.")
    created_at: datetime = Field(description="UTC timestamp when access was granted.")
    updated_at: datetime = Field(description="UTC timestamp of the latest role change.")


class AuditEventRead(BaseModel):
    """Immutable record of an authenticated mutation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Stable audit-event identifier.")
    organization_id: UUID | None = Field(
        description="Organization affected by the event, retained as null after deletion."
    )
    actor_user_id: UUID | None = Field(
        description="User responsible for the event, retained as null after user deletion."
    )
    action: str = Field(description="Machine-readable operation such as product.created.")
    resource_type: str = Field(description="Type of resource affected by the operation.")
    resource_id: UUID | None = Field(description="Identifier of the affected resource.")
    details: dict[str, Any] = Field(description="Non-sensitive contextual event attributes.")
    created_at: datetime = Field(description="UTC timestamp when the mutation occurred.")
