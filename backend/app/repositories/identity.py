from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import AuditEvent, OrganizationMembership, User
from app.domain.enums import OrganizationRole
from app.repositories.inventory import PageResult


class IdentityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, model):
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return model

    def flush(self, model):
        self.session.flush()
        self.session.refresh(model)
        return model

    def delete(self, model: object) -> None:
        self.session.delete(model)
        self.session.flush()

    def get_user(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_user_by_subject(self, subject: str) -> User | None:
        return self.session.scalar(select(User).where(User.oidc_subject == subject))

    def get_user_by_email(self, email: str) -> User | None:
        return self.session.scalar(
            select(User).where(func.lower(User.email) == email.lower()).limit(1)
        )

    def memberships_for_user(self, user_id: UUID) -> list[OrganizationMembership]:
        return list(
            self.session.scalars(
                select(OrganizationMembership)
                .options(selectinload(OrganizationMembership.organization))
                .where(OrganizationMembership.user_id == user_id)
                .order_by(OrganizationMembership.created_at, OrganizationMembership.id)
            ).all()
        )

    def organization_ids_for_user(self, user_id: UUID) -> list[UUID]:
        return list(
            self.session.scalars(
                select(OrganizationMembership.organization_id).where(
                    OrganizationMembership.user_id == user_id
                )
            ).all()
        )

    def get_membership(
        self, organization_id: UUID, user_id: UUID
    ) -> OrganizationMembership | None:
        return self.session.scalar(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
            )
        )

    def get_membership_by_id(self, membership_id: UUID) -> OrganizationMembership | None:
        return self.session.scalar(
            select(OrganizationMembership)
            .options(selectinload(OrganizationMembership.user))
            .where(OrganizationMembership.id == membership_id)
        )

    def list_memberships(self, organization_id: UUID) -> list[OrganizationMembership]:
        return list(
            self.session.scalars(
                select(OrganizationMembership)
                .options(selectinload(OrganizationMembership.user))
                .where(OrganizationMembership.organization_id == organization_id)
                .order_by(OrganizationMembership.created_at, OrganizationMembership.id)
            ).all()
        )

    def count_owners(self, organization_id: UUID) -> int:
        return self.session.scalar(
            select(func.count()).select_from(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.role == OrganizationRole.OWNER.value,
            )
        ) or 0

    def record_audit(
        self,
        *,
        organization_id: UUID | None,
        actor_user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID | None,
        details: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_audit_events(
        self, organization_id: UUID, *, limit: int, offset: int
    ) -> PageResult[AuditEvent]:
        predicate = AuditEvent.organization_id == organization_id
        total = self.session.scalar(
            select(func.count()).select_from(AuditEvent).where(predicate)
        ) or 0
        items = list(
            self.session.scalars(
                select(AuditEvent)
                .where(predicate)
                .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )
        return PageResult(items=items, total=total, limit=limit, offset=offset)
