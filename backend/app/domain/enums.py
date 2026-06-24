from enum import StrEnum


class ProductStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class BatchStatus(StrEnum):
    ACTIVE = "active"
    DEPLETED = "depleted"
    QUARANTINED = "quarantined"
    EXPIRED = "expired"


class OrganizationRole(StrEnum):
    VIEWER = "viewer"
    INVENTORY_MANAGER = "inventory_manager"
    ADMIN = "admin"
    OWNER = "owner"
