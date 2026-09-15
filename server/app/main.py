# cmf-server api's
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from starlette.exceptions import HTTPException
from server.app.get_data import (
    get_all_artifact_ids,
    get_all_exe_ids,
    async_api,
)
from server.app.services.mlmd_state import (
    mlmd_state,
)
from server.app.services.scheduler import schedule_runner
from server.app.db.dbconfig import init_db
from pathlib import Path
import dotenv
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from server.app.schemas.responses import error_response
from server.app.api.v1 import api_router
from server.app.middleware.keycloak import KeycloakBearerMiddleware
dotenv.load_dotenv()

#lifespan used to prevent multiple loading and save time for visualization.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    App startup/shutdown hook: initializes the DB schema, preloads execution/artifact
    id caches into MlmdState, and starts/stops the background sync scheduler task.

    Args:
        app (FastAPI): The FastAPI application instance.

    Returns:
        AsyncGenerator[None, None]: Yields control to the running app between startup and shutdown.
    """
    app.state.mlmd = mlmd_state

    # Initialize the database schema
    await init_db()

    if app.state.mlmd.query:
        # loaded execution ids with names into memory
        exe_ids = await async_api(get_all_exe_ids, app.state.mlmd.query)
        app.state.mlmd.dict_of_exe_ids.update(exe_ids)
        # loaded artifact ids into memory
        art_ids = await async_api(get_all_artifact_ids, app.state.mlmd.query, app.state.mlmd.dict_of_exe_ids)
        app.state.mlmd.dict_of_art_ids.update(art_ids)
    # Start background scheduler task
    app.state.scheduler_task = asyncio.create_task(schedule_runner())
    yield
    # Cancel scheduler on shutdown
    # If FastAPI is down, no scheduled sync runs.
    # On restart, the scheduler resumes from DB state.
    # Missed schedules are not deleted or skipped automatically.
    # One-time schedules run once after restart if overdue.
    # Periodic schedules keep running and may attempt backlog catch-up.
    # There is no explicit restart cleanup/update pass for scheduled_syncs.
    task = getattr(app.state, "scheduler_task", None)
    if task:
        task.cancel()
    app.state.mlmd.dict_of_art_ids.clear()
    app.state.mlmd.dict_of_exe_ids.clear()

app = FastAPI(
    title="cmf-server",
    lifespan=lifespan,
    root_path="/api",
    swagger_ui_parameters={"persistAuthorization": True},
)
app.state.mlmd = mlmd_state

app.include_router(api_router)


def custom_openapi():
    """Expose Keycloak Bearer JWT in Swagger Authorize dialog."""
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=getattr(app, "version", None) or "0.1.0",
        description=(
            "CMF REST API with optional Keycloak OIDC.\n\n"
            "1. Call **POST /v1/auth/token** with your Keycloak username/password "
            "(`grant_type=password`, `client_id=d3dsearch`) — no client_secret needed.\n"
            "2. Click **Authorize**, paste the `access_token` value (Bearer is added "
            "automatically).\n"
            "3. Call protected `/v1/*` routes."
        ),
        routes=app.routes,
    )
    components = openapi_schema.setdefault("components", {})
    schemes = components.setdefault("securitySchemes", {})
    schemes["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": (
            "Keycloak access token from POST /v1/auth/token "
            "(password grant). Paste the token only — do not include the word Bearer."
        ),
    }
    # Default: require bearer on all operations; clear it for public auth helpers.
    openapi_schema["security"] = [{"bearerAuth": []}]
    public_paths = {
        "/v1/auth/config",
        "/v1/auth/status",
        "/v1/auth/token",
        "/v1/acknowledge",
        "/",
    }
    for path, methods in (openapi_schema.get("paths") or {}).items():
        if path in public_paths or path.endswith("/auth/config") or path.endswith("/auth/status") or path.endswith("/auth/token") or path.endswith("/acknowledge"):
            for op in methods.values():
                if isinstance(op, dict):
                    op["security"] = []
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Keycloak bearer gate (KEYCLOAK_AUTH_MODE=off|optional|required).
# Registered before CORS so it is the innermost middleware (runs first on request).
app.add_middleware(KeycloakBearerMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convert Pydantic request validation errors into the standard error response format.

    Args:
        request (Request): The incoming request that failed validation.
        exc (RequestValidationError): The raised validation error, with per-field details.

    Returns:
        JSONResponse: 422 response with field, message, and code per validation error.
    """
    # Parse validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:]) if len(error["loc"]) > 1 else str(error["loc"][0])
        errors.append({
            "field": field,
            "message": error["msg"],
            "code": error["type"],
        })
    
    response = error_response(
        message="Request validation failed",
        code=422,
        errors=errors,
    )
    return JSONResponse(status_code=422, content=response.dict())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Convert HTTPExceptions raised by API routes into the standard error response format.

    Args:
        request (Request): The incoming request being handled.
        exc (HTTPException): The raised exception, with status_code and detail.

    Returns:
        JSONResponse: Response with exc.status_code and the standardized error body.
    """
    response = error_response(
        message=str(exc.detail),
        code=exc.status_code,
        errors=[],
    )
    return JSONResponse(status_code=exc.status_code, content=response.dict())


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    """
    Convert unexpected/non-HTTP exceptions into the standard error response format.

    Examples: ZeroDivisionError, AttributeError, KeyError, TypeError, ValueError.

    Args:
        request (Request): The incoming request being handled.
        exc (Exception): The unhandled exception.

    Returns:
        JSONResponse: 500 response with a generic "Internal server error" message.
    """
    response = error_response(
        message="Internal server error",
        code=500,
        errors=[],
    )
    return JSONResponse(status_code=500, content=response.dict())


BASE_PATH = Path(__file__).resolve().parent
app.mount("/cmf-server/data/static", StaticFiles(directory="/cmf-server/data/static"), name="static")

@app.get("/")
async def read_root(request: Request):
    return {"cmf-server"}


# Business logic functions have been moved to their respective router modules:
# - Metadata functions: server/app/api/v1/metadata.py
# - Pipeline functions: server/app/api/v1/pipelines.py  
# - Server functions: server/app/api/v1/servers.py
# - Execution functions: server/app/api/v1/executions.py
# - Artifact functions: server/app/api/v1/artifacts.py
# - Lineage functions: server/app/api/v1/lineage.py
