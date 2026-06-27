from fastapi import APIRouter


root_route = APIRouter()

@root_route.get("/")
async def health_check():
    return {"success": True}


from .auth import auth_router
from .admin import admin_router


root_route.include_router(auth_router, prefix="/auth")
root_route.include_router(admin_router, prefix="/admin")
