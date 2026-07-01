from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, DomainValidationError, ResourceNotFoundError
from app.db.models import OrganizationMembership, User
from app.domain.enums import OrganizationRole
from app.repositories.identity import IdentityRepository
from app.repositories.inventory import PageResult
from app.schemas.identity import MembershipCreate, MembershipUpdate
from app.services.authorization import AuthorizationService


class IdentityService:
    def __init__(
        self,
        repository: IdentityRepository,
        authorization: AuthorizationService,
        actor: User,
    ) -> None:
        self.repository = repository
        self.authorization = authorization
        self.actor = actor

    def memberships_for_current_user(self) -> list[OrganizationMembership]:
        return self.repository.memberships_for_user(self.actor.id)

    def list_memberships(self, organization_id: UUID) -> list[OrganizationMembership]:
        self.authorization.require_role(organization_id, OrganizationRole.ADMIN)
        return self.repository.list_memberships(organization_id)

    def add_membership(
        self, organization_id: UUID, payload: MembershipCreate
    ) -> OrganizationMembership:
        actor_membership = self.authorization.require_role(
            organization_id, OrganizationRole.ADMIN
        )
        if payload.role is OrganizationRole.OWNER and actor_membership.role != OrganizationRole.OWNER.value:
            raise DomainValidationError("Only an owner may grant the owner role.")
        user = self.repository.get_user_by_email(str(payload.user_email))
        if user is None:
            raise ResourceNotFoundError("User email", payload.user_email)
        if not user.email_verified:
            raise DomainValidationError(
                "Organization access can only be granted to a verified email address."
            )
        membership = OrganizationMembership(
            organization_id=organization_id, user_id=user.id, role=payload.role.value
        )
        try:
            membership = self.repository.add(membership)
        except IntegrityError as error:
            self.repository.session.rollback()
            raise ConflictError("This user is already a member of the organization.") from error
        membership.user = user
        self.authorization.audit(
            organization_id=organization_id,
            action="membership.created",
            resource_type="membership",
            resource_id=membership.id,
            details={"user_id": str(user.id), "role": payload.role.value},
        )
        return membership

    def update_membership(
        self, organization_id: UUID, membership_id: UUID, payload: MembershipUpdate
    ) -> OrganizationMembership:
        actor_membership = self.authorization.require_role(
            organization_id, OrganizationRole.ADMIN
        )
        membership = self._get_membership(organization_id, membership_id)
        old_role = OrganizationRole(membership.role)
        if OrganizationRole.OWNER in {old_role, payload.role}:
            if actor_membership.role != OrganizationRole.OWNER.value:
                raise DomainValidationError("Only an owner may change owner memberships.")
            if old_role is OrganizationRole.OWNER and payload.role is not OrganizationRole.OWNER:
                self._ensure_another_owner(organization_id)
        membership.role = payload.role.value
        membership = self.repository.flush(membership)
        self.authorization.audit(
            organization_id=organization_id,
            action="membership.updated",
            resource_type="membership",
            resource_id=membership.id,
            details={"old_role": old_role.value, "new_role": payload.role.value},
        )
        return membership

    def delete_membership(self, organization_id: UUID, membership_id: UUID) -> None:
        actor_membership = self.authorization.require_role(
            organization_id, OrganizationRole.ADMIN
        )
        membership = self._get_membership(organization_id, membership_id)
        membership_role = OrganizationRole(membership.role)
        if membership_role is OrganizationRole.OWNER:
            if actor_membership.role != OrganizationRole.OWNER.value:
                raise DomainValidationError("Only an owner may remove an owner membership.")
            self._ensure_another_owner(organization_id)
        removed_user_id = membership.user_id
        self.repository.delete(membership)
        self.authorization.audit(
            organization_id=organization_id,
            action="membership.deleted",
            resource_type="membership",
            resource_id=membership_id,
            details={"user_id": str(removed_user_id), "role": membership_role.value},
        )

    def list_audit_events(
        self, organization_id: UUID, *, limit: int, offset: int
    ) -> PageResult:
        self.authorization.require_role(organization_id, OrganizationRole.ADMIN)
        return self.repository.list_audit_events(
            organization_id, limit=limit, offset=offset
        )

    def _get_membership(
        self, organization_id: UUID, membership_id: UUID
    ) -> OrganizationMembership:
        membership = self.repository.get_membership_by_id(membership_id)
        if membership is None or membership.organization_id != organization_id:
            raise ResourceNotFoundError("Membership", membership_id)
        return membership

    def _ensure_another_owner(self, organization_id: UUID) -> None:
        if self.repository.count_owners(organization_id) <= 1:
            raise DomainValidationError("An organization must retain at least one owner.")
