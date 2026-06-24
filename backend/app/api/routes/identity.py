from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.authentication import CurrentUser
from app.api.dependencies import IdentityServiceDependency
from app.schemas.common import Page
from app.schemas.identity import (
    AuditEventRead,
    CurrentUserRead,
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
    UserRead,
)

router = APIRouter()


@router.get("/me", response_model=CurrentUserRead, summary="Get the authenticated user")
def get_me(actor: CurrentUser, service: IdentityServiceDependency) -> CurrentUserRead:
    profile = UserRead.model_validate(actor)
    return CurrentUserRead(
        **profile.model_dump(), memberships=service.memberships_for_current_user()
    )


@router.get(
    "/organizations/{organization_id}/memberships",
    response_model=list[MembershipRead],
    summary="List organization memberships",
)
def list_memberships(
    organization_id: UUID, service: IdentityServiceDependency
) -> list[MembershipRead]:
    return service.list_memberships(organization_id)


@router.post(
    "/organizations/{organization_id}/memberships",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    summary="Grant organization access",
)
def add_membership(
    organization_id: UUID,
    payload: MembershipCreate,
    service: IdentityServiceDependency,
) -> MembershipRead:
    return service.add_membership(organization_id, payload)


@router.patch(
    "/organizations/{organization_id}/memberships/{membership_id}",
    response_model=MembershipRead,
    summary="Change an organization role",
)
def update_membership(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipUpdate,
    service: IdentityServiceDependency,
) -> MembershipRead:
    return service.update_membership(organization_id, membership_id, payload)


@router.delete(
    "/organizations/{organization_id}/memberships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke organization access",
)
def delete_membership(
    organization_id: UUID,
    membership_id: UUID,
    service: IdentityServiceDependency,
) -> Response:
    service.delete_membership(organization_id, membership_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/organizations/{organization_id}/audit-events",
    response_model=Page[AuditEventRead],
    summary="List organization audit events",
)
def list_audit_events(
    organization_id: UUID,
    service: IdentityServiceDependency,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum records to return.")] = 50,
    offset: Annotated[int, Query(ge=0, description="Matching records to skip.")] = 0,
) -> Page[AuditEventRead]:
    page = service.list_audit_events(organization_id, limit=limit, offset=offset)
    return Page[AuditEventRead].model_validate(page)
