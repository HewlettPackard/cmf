"""Version 2 API routers for the CMF server."""

from fastapi import APIRouter

from server.app.api.v2.ui_actions import router as ui_actions_router

api_router = APIRouter()

api_router.include_router(ui_actions_router)