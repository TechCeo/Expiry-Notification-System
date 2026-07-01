class ApplicationError(Exception):
    """Base class for expected application-layer failures."""


class ResourceNotFoundError(ApplicationError):
    def __init__(self, resource: str, resource_id: object) -> None:
        super().__init__(f"{resource} '{resource_id}' was not found.")


class ConflictError(ApplicationError):
    """Requested mutation conflicts with existing persisted state."""


class DomainValidationError(ApplicationError):
    """Request is structurally valid but violates an inventory business rule."""


class AuthenticationError(ApplicationError):
    """Access token is absent, invalid, expired, or issued for another API."""


class PermissionDeniedError(ApplicationError):
    """Authenticated user lacks the required organization role."""
