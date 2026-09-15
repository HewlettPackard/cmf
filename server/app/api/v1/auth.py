"""Keycloak auth helper endpoints for CMF (config / status / token mint)."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.app import keycloak_auth as oidc
from server.app.schemas.responses import error_response, success_response

router = APIRouter(prefix="/v1", tags=["Authentication"])


class AuthTokenRequest(BaseModel):
    grant_type: str = Field(default="password", description="password | client_credentials")
    client_id: str = Field(default="d3dsearch")
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    scope: Optional[str] = None


@router.get("/auth/config")
async def auth_config() -> Any:
    return success_response(data=oidc.public_config(), message="Keycloak auth config")


@router.get("/auth/status")
async def auth_status(request: Request) -> Any:
    identity = oidc.check(request.headers.get("Authorization"))
    data = {
        "mode": oidc.mode(),
        "valid": identity.valid,
        "username": identity.username,
        "client": identity.client,
        "subject": identity.subject,
        "reason": identity.reason,
        "source": identity.source,
    }
    return success_response(data=data, message="Auth status")


@router.post("/auth/token")
async def auth_token(body: AuthTokenRequest) -> Any:
    """Exchange credentials for an access token (password grant preferred).

    For the configured API client, password grant may omit client_secret — the
    server attaches KEYCLOAK_CLIENT_SECRET. client_credentials always requires
    the caller to send a secret.
    """
    try:
        token = oidc.request_token(
            grant_type=body.grant_type,
            client_id=body.client_id,
            client_secret=body.client_secret,
            username=body.username,
            password=body.password,
            scope=body.scope,
        )
    except oidc.AuthError as exc:
        err = error_response(
            message=exc.message,
            code=exc.status,
            errors=[{"message": exc.message, "code": exc.code}],
        )
        return JSONResponse(status_code=exc.status, content=err.dict(), headers=exc.headers or None)
    return success_response(data=token, message="Token issued")
