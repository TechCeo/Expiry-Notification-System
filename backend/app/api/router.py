from fastapi import APIRouter

from app.api.routes.batches import router as batches_router
from app.api.routes.health import router as health_router
from app.api.routes.identity import router as identity_router
from app.api.routes.locations import router as locations_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.products import router as products_router

system_router = APIRouter()
system_router.include_router(health_router, tags=["system"])

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["system"])
api_v1_router.include_router(identity_router, tags=["identity and access"])
api_v1_router.include_router(organizations_router, tags=["organizations"])
api_v1_router.include_router(products_router, tags=["products"])
api_v1_router.include_router(locations_router, tags=["locations"])
api_v1_router.include_router(batches_router, tags=["batches"])
