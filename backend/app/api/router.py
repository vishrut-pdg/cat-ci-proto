from fastapi import APIRouter

from app.api.v1.health import (
    router as health_router,
)
from app.api.v1.opportunities import (
    router as opportunities_router,
)

from app.api.v1.recsys import (
    router as recsys_router,
)


api_router = APIRouter()

api_router.include_router(
    health_router
)

api_router.include_router(
    opportunities_router
)

api_router.include_router(
    recsys_router
)