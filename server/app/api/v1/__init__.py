
"""Version 1 API routers for the CMF server."""

from fastapi import APIRouter

from server.app.api.v1.artifacts import router as artifacts_router
from server.app.api.v1.metadata import router as metadata_router
from server.app.api.v1.pipelines import router as pipelines_router
from server.app.api.v1.servers import router as servers_router
from server.app.api.v1.schedules import router as schedules_router
from server.app.api.v1.ui_actions import router as ui_actions_router
from server.app.api.v1.env import router as env_router

api_router = APIRouter()

api_router.include_router(pipelines_router)
api_router.include_router(metadata_router)
api_router.include_router(servers_router)
api_router.include_router(artifacts_router)
api_router.include_router(schedules_router)
api_router.include_router(ui_actions_router)
api_router.include_router(env_router)
