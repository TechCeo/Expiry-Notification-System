from uuid import UUID

from app.core.exceptions import PermissionDeniedError
from app.db.models import OrganizationMembership, User
from app.domain.enums import OrganizationRole
from app.repositories.identity import IdentityRepository

ROLE_LEVEL = {
    OrganizationRole.VIEWER: 10,
    OrganizationRole.INVENTORY_MANAGER: 20,
    OrganizationRole.ADMIN: 30,
    OrganizationRole.OWNER: 40,
}


class AuthorizationService:
    def __init__(self, repository: IdentityRepository, actor: User) -> None:
        self.repository = repository
        self.actor = actor

    def require_role(
        self, organization_id: UUID, minimum_role: OrganizationRole
    ) -> OrganizationMembership:
        membership = self.repository.get_membership(organization_id, self.actor.id)
        if membership is None:
            raise PermissionDeniedError("You do not have access to this organization.")
        actual_role = OrganizationRole(membership.role)
        if ROLE_LEVEL[actual_role] < ROLE_LEVEL[minimum_role]:
            raise PermissionDeniedError(
                f"The '{minimum_role.value}' role or higher is required."
            )
        return membership

    def organization_ids(self) -> list[UUID]:
        return self.repository.organization_ids_for_user(self.actor.id)

    def audit(
        self,
        *,
        organization_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        details: dict[str, object] | None = None,
    ) -> None:
        self.repository.record_audit(
            organization_id=organization_id,
            actor_user_id=self.actor.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
