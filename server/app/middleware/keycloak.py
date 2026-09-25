"""Starlette middleware: require Keycloak Bearer JWT on CMF /v1 API routes."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from server.app import keycloak_auth as oidc
from server.app.schemas.responses import error_response


class KeycloakBearerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not oidc.path_requires_auth(path):
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        try:
            if oidc.mode() == "required":
                identity = oidc.require(authorization)
            else:
                identity = oidc.check(authorization)
        except oidc.AuthError as exc:
            body = error_response(
                message=exc.message,
                code=exc.status,
                errors=[{"message": exc.message, "code": exc.code}],
            )
            return JSONResponse(
                status_code=exc.status,
                content=body.dict(),
                headers=exc.headers or None,
            )

        request.state.identity = identity
        return await call_next(request)
