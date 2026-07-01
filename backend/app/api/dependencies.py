from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.authentication import CurrentUser
from app.db.session import get_db
from app.repositories.identity import IdentityRepository
from app.repositories.inventory import InventoryRepository
from app.services.authorization import AuthorizationService
from app.services.identity import IdentityService
from app.services.inventory import InventoryService


def get_inventory_service(
    database: Annotated[Session, Depends(get_db)],
    actor: CurrentUser,
) -> InventoryService:
    identity_repository = IdentityRepository(database)
    authorization = AuthorizationService(identity_repository, actor)
    return InventoryService(InventoryRepository(database), authorization)


def get_identity_service(
    database: Annotated[Session, Depends(get_db)],
    actor: CurrentUser,
) -> IdentityService:
    repository = IdentityRepository(database)
    authorization = AuthorizationService(repository, actor)
    return IdentityService(repository, authorization, actor)


InventoryServiceDependency = Annotated[InventoryService, Depends(get_inventory_service)]
IdentityServiceDependency = Annotated[IdentityService, Depends(get_identity_service)]
