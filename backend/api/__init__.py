from fastapi import APIRouter
from .auth import router as auth_router
from .families import router as families_router
from .bills import router as bills_router
from .upload import router as upload_router
from .health import router as health_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(families_router)
api_router.include_router(bills_router)
api_router.include_router(upload_router)
api_router.include_router(health_router)

__all__ = ["api_router"]