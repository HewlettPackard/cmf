"""Keycloak / OIDC bearer-token validation for the CMF REST API.

Validates JWTs locally against the realm JWKS (preferred). Optionally falls
back to token introspection when a client secret is configured.

Aligned with ADIL FEDER (`federdatalake` / `d3dsearch`).

Environment
-----------
KEYCLOAK_ISSUER          e.g. https://auth.adil.sdsc.edu:9001/realms/federdatalake
KEYCLOAK_JWKS_URL        optional; defaults to {issuer}/protocol/openid-connect/certs
KEYCLOAK_TOKEN_URL       optional; defaults to {issuer}/protocol/openid-connect/token
KEYCLOAK_INTROSPECT_URL  optional; defaults to {issuer}/protocol/openid-connect/token/introspect
KEYCLOAK_CLIENT_ID       e.g. d3dsearch
KEYCLOAK_CLIENT_SECRET   confidential client secret (password-grant proxy + introspection;
                         NOT required to verify JWTs)
KEYCLOAK_AUDIENCE        optional expected ``aud`` claim; if unset, audience is not
                         enforced (Keycloak access tokens often use aud=account)
KEYCLOAK_AUTH_MODE       off | optional | required  (default: off)
KEYCLOAK_SSL_VERIFY      true|false (default true)
KEYCLOAK_JWKS_TTL        seconds to cache JWKS (default 3600)
"""

from __future__ import annotations

import json
import logging
import os
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

MODES = ("off", "optional", "required")
DEFAULT_ISSUER = "https://auth.adil.sdsc.edu:9001/realms/federdatalake"
DEFAULT_CLIENT_ID = "d3dsearch"

_jwks_lock = threading.Lock()
_jwks: dict[str, Any] = {"fetched_at": 0.0, "keys": {}}


def mode() -> str:
    m = (os.environ.get("KEYCLOAK_AUTH_MODE") or os.environ.get("FEDER_OIDC_AUTH_MODE") or "off").strip().lower()
    if m not in MODES:
        logger.warning("Keycloak: unknown KEYCLOAK_AUTH_MODE=%r; treating as off", m)
        return "off"
    return m


def issuer() -> str:
    return (os.environ.get("KEYCLOAK_ISSUER") or DEFAULT_ISSUER).rstrip("/")


def client_id() -> str:
    return (os.environ.get("KEYCLOAK_CLIENT_ID") or DEFAULT_CLIENT_ID).strip()


def client_secret() -> str:
    return (os.environ.get("KEYCLOAK_CLIENT_SECRET") or "").strip()


def jwks_url() -> str:
    return (
        os.environ.get("KEYCLOAK_JWKS_URL")
        or f"{issuer()}/protocol/openid-connect/certs"
    ).strip()


def token_url() -> str:
    return (
        os.environ.get("KEYCLOAK_TOKEN_URL")
        or f"{issuer()}/protocol/openid-connect/token"
    ).strip()


def introspect_url() -> str:
    return (
        os.environ.get("KEYCLOAK_INTROSPECT_URL")
        or f"{issuer()}/protocol/openid-connect/token/introspect"
    ).strip()


def audience() -> str | None:
    value = (os.environ.get("KEYCLOAK_AUDIENCE") or "").strip()
    return value or None


def ssl_verify() -> bool:
    return (os.environ.get("KEYCLOAK_SSL_VERIFY") or "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def jwks_ttl() -> int:
    try:
        return int(os.environ.get("KEYCLOAK_JWKS_TTL", "3600"))
    except ValueError:
        return 3600


def validation_available() -> bool:
    try:
        import jwt  # noqa: F401
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False


def _ssl_context() -> ssl.SSLContext | None:
    if ssl_verify():
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _fetch_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> Any:
    request = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    with urllib.request.urlopen(request, timeout=15, context=_ssl_context()) as response:
        return json.loads(response.read().decode("utf-8"))


class Identity:
    def __init__(
        self,
        *,
        valid: bool,
        subject: str | None = None,
        client: str | None = None,
        username: str | None = None,
        scope: str | None = None,
        expires_at: float | None = None,
        claims: dict[str, Any] | None = None,
        reason: str | None = None,
        source: str | None = None,
    ) -> None:
        self.valid = valid
        self.subject = subject
        self.client = client
        self.username = username
        self.scope = scope
        self.expires_at = expires_at
        self.claims = claims or {}
        self.reason = reason
        self.source = source

    @property
    def label(self) -> str:
        if not self.valid:
            return "anonymous"
        if self.username:
            return f"user:{self.username}"
        if self.client:
            return f"client:{self.client}"
        if self.subject:
            return f"sub:{self.subject[:16]}"
        return "authenticated"

    def public(self) -> dict[str, Any]:
        return {
            "authenticated": self.valid,
            "label": self.label,
            "subject": self.subject,
            "client": self.client,
            "username": self.username,
            "scope": self.scope,
            "expires_at": self.expires_at,
            "source": self.source,
            "reason": self.reason,
        }


ANONYMOUS = Identity(valid=False, reason="no token presented")


def public_config() -> dict[str, Any]:
    return {
        "mode": mode(),
        "issuer": issuer(),
        "realm": issuer().rsplit("/", 1)[-1],
        "client_id": client_id(),
        "token_url": token_url(),
        "jwks_url": jwks_url(),
        "introspection_url": introspect_url(),
        "discovery_url": f"{issuer()}/.well-known/openid-configuration",
        "audience": audience(),
        "validation_available": validation_available(),
        "client_secret_configured": bool(client_secret()),
        "grants": ["client_credentials", "password", "authorization_code", "refresh_token"],
    }


def signing_keys(force: bool = False) -> dict[str, Any]:
    now = time.time()
    with _jwks_lock:
        fresh = now - float(_jwks["fetched_at"]) < jwks_ttl()
        if _jwks["keys"] and fresh and not force:
            return _jwks["keys"]
        try:
            from jwt import PyJWK

            raw = _fetch_json(jwks_url())
            keys = {}
            for item in raw.get("keys", []):
                kid = item.get("kid")
                if not kid:
                    continue
                # Skip encryption keys (Keycloak publishes enc + sig).
                if item.get("use") == "enc":
                    continue
                if str(item.get("alg") or "").upper().startswith("RSA-OAEP"):
                    continue
                try:
                    keys[kid] = PyJWK.from_dict(item).key
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Keycloak: skipping JWKS kid=%s: %s", kid, exc)
            if keys:
                _jwks.update(fetched_at=now, keys=keys)
                logger.info("Keycloak: loaded %s signing key(s) from %s", len(keys), jwks_url())
        except Exception as exc:  # noqa: BLE001
            level = logger.warning if _jwks["keys"] else logger.error
            level("Keycloak: could not refresh JWKS from %s: %s", jwks_url(), exc)
        return _jwks["keys"]


def _bearer_token(authorization_header: str | None) -> str | None:
    if not authorization_header:
        return None
    value = authorization_header.strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    return value or None


def verify_jwt(token: str) -> Identity:
    if not token:
        return ANONYMOUS
    try:
        import jwt
    except ImportError:
        return Identity(valid=False, reason="token validation unavailable (PyJWT missing)")

    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:  # noqa: BLE001
        return Identity(valid=False, reason=f"malformed token ({type(exc).__name__})")

    keys = signing_keys()
    key = keys.get(header.get("kid"))
    if key is None and keys:
        key = signing_keys(force=True).get(header.get("kid"))
    if key is None:
        return Identity(valid=False, reason="signing key not known for this token")

    options = {"verify_aud": bool(audience())}
    try:
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256", "ES256"],
            "issuer": issuer(),
            "options": options,
        }
        if audience():
            decode_kwargs["audience"] = audience()
        claims = jwt.decode(token, key, **decode_kwargs)
    except jwt.ExpiredSignatureError:
        return Identity(valid=False, reason="token expired")
    except jwt.InvalidIssuerError:
        return Identity(valid=False, reason="token issuer mismatch")
    except jwt.InvalidAudienceError:
        return Identity(valid=False, reason="token audience mismatch")
    except Exception as exc:  # noqa: BLE001
        return Identity(valid=False, reason=f"token rejected ({type(exc).__name__})")

    azp = claims.get("azp") or claims.get("client_id")
    expected_client = client_id()
    # Prefer matching the configured API client when present; still accept user
    # tokens issued for other public clients in the same realm unless
    # KEYCLOAK_REQUIRE_CLIENT=true.
    require_client = (os.environ.get("KEYCLOAK_REQUIRE_CLIENT") or "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if require_client and expected_client and azp and azp != expected_client:
        return Identity(valid=False, reason=f"token client {azp!r} is not allowed")

    return Identity(
        valid=True,
        subject=str(claims.get("sub") or "") or None,
        client=str(azp) if azp else None,
        username=str(claims.get("preferred_username") or claims.get("email") or "") or None,
        scope=str(claims.get("scope") or "") or None,
        expires_at=float(claims["exp"]) if claims.get("exp") is not None else None,
        claims=claims,
        source="jwt",
    )


def introspect(token: str) -> Identity:
    secret = client_secret()
    if not secret:
        return Identity(valid=False, reason="introspection unavailable (no client secret)")
    body = urllib.parse.urlencode(
        {"token": token, "client_id": client_id(), "client_secret": secret}
    ).encode("utf-8")
    try:
        payload = _fetch_json(
            introspect_url(),
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except Exception as exc:  # noqa: BLE001
        return Identity(valid=False, reason=f"introspection failed ({type(exc).__name__})")
    if not payload.get("active"):
        return Identity(valid=False, reason="token inactive")
    return Identity(
        valid=True,
        subject=str(payload.get("sub") or "") or None,
        client=str(payload.get("client_id") or payload.get("azp") or "") or None,
        username=str(payload.get("username") or payload.get("preferred_username") or "") or None,
        scope=str(payload.get("scope") or "") or None,
        expires_at=float(payload["exp"]) if payload.get("exp") is not None else None,
        claims=payload,
        source="introspection",
    )


def verify(authorization_header: str | None) -> Identity:
    token = _bearer_token(authorization_header)
    if not token:
        return ANONYMOUS
    identity = verify_jwt(token)
    if identity.valid:
        return identity
    # Opaque / non-JWT access tokens: try introspection when configured.
    if client_secret() and token.count(".") != 2:
        return introspect(token)
    # JWT failed but secret present: optional introspect as last resort.
    if client_secret() and identity.reason and "expired" not in (identity.reason or ""):
        alt = introspect(token)
        if alt.valid:
            return alt
    return identity


def check(authorization_header: str | None) -> Identity:
    """Honour KEYCLOAK_AUTH_MODE for a request."""
    current = mode()
    if current == "off":
        return Identity(valid=True, reason="auth disabled", source="off")
    return verify(authorization_header)


def require(authorization_header: str | None) -> Identity:
    """Return a valid identity or raise AuthError when mode=required."""
    identity = check(authorization_header)
    if mode() != "required":
        return identity
    if not validation_available():
        raise AuthError(
            503,
            "Keycloak auth is required but PyJWT/cryptography are not installed",
            code="AUTH_MISCONFIGURED",
        )
    if not identity.valid:
        raise AuthError(
            401,
            f"A valid Keycloak bearer token is required: {identity.reason or 'unauthorized'}",
            code="UNAUTHORIZED",
            headers={"WWW-Authenticate": 'Bearer realm="federdatalake"'},
        )
    return identity


class AuthError(Exception):
    def __init__(
        self,
        status: int,
        message: str,
        *,
        code: str = "UNAUTHORIZED",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code
        self.headers = headers or {}


def fetch_client_credentials_token(*, scope: str | None = None) -> dict[str, Any]:
    """Mint a service token using the *server* client secret.

    For internal/ops scripts only. Never expose this through a public HTTP route.
    """
    secret = client_secret()
    if not secret:
        raise AuthError(503, "KEYCLOAK_CLIENT_SECRET is not configured", code="AUTH_MISCONFIGURED")
    return request_token(
        grant_type="client_credentials",
        client_id=client_id(),
        client_secret=secret,
        scope=scope,
    )


def request_token(
    *,
    grant_type: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    username: str | None = None,
    password: str | None = None,
    scope: str | None = None,
) -> dict[str, Any]:
    """Proxy a token request to Keycloak.

    - ``client_credentials``: caller **must** supply ``client_secret``. The
      server secret is never used (that would let anyone mint a service token).
    - ``password``: caller supplies username/password. If the Keycloak client is
      confidential and the caller omits ``client_secret``, the server may attach
      its own ``KEYCLOAK_CLIENT_SECRET`` when ``client_id`` matches the configured
      API client — so Jupyter notebooks never need the shared secret.
    """
    grant = (grant_type or "").strip()
    cid = (client_id or "").strip()
    secret = (client_secret or "").strip()
    user = (username or "").strip()
    if not cid:
        raise AuthError(400, "client_id is required", code="MISSING_CLIENT_ID")

    form: dict[str, str] = {"grant_type": grant, "client_id": cid}
    if scope:
        form["scope"] = str(scope)

    if grant == "client_credentials":
        if not secret:
            raise AuthError(
                400,
                "client_secret is required for grant_type=client_credentials",
                code="MISSING_CLIENT_SECRET",
            )
        form["client_secret"] = secret
    elif grant == "password":
        if not user or password is None or password == "":
            raise AuthError(
                400,
                "username and password are required for grant_type=password",
                code="MISSING_USER_CREDENTIALS",
            )
        form["username"] = user
        form["password"] = password
        if not secret:
            # Notebook-friendly: keep confidential-client secret on the API host.
            # (Parameter names shadow the module helpers client_id()/client_secret().)
            server_id = (os.environ.get("KEYCLOAK_CLIENT_ID") or DEFAULT_CLIENT_ID).strip()
            server_secret = (os.environ.get("KEYCLOAK_CLIENT_SECRET") or "").strip()
            if server_secret and cid == server_id:
                secret = server_secret
        if secret:
            form["client_secret"] = secret
    else:
        raise AuthError(
            400,
            "Unsupported grant_type; use password or client_credentials "
            "(or call Keycloak token URL directly for authorization_code).",
            code="UNSUPPORTED_GRANT",
        )

    body = urllib.parse.urlencode(form).encode("utf-8")
    try:
        return _fetch_json(
            token_url(),
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise AuthError(exc.code, f"token request failed: {detail}", code="TOKEN_REQUEST_FAILED") from exc


# Paths reachable without a bearer token even in required mode.
# CMF behind nginx sees /v1/...; TestClient / direct uvicorn may see /api/v1/...
PUBLIC_PATH_PREFIXES = (
    "/v1/auth/",
    "/api/v1/auth/",
)
PUBLIC_PATH_EXACT = {
    "/",
    "/v1/auth/status",
    "/v1/auth/config",
    "/v1/auth/token",
    "/api/v1/auth/status",
    "/api/v1/auth/config",
    "/api/v1/auth/token",
    # Peer federation handshake (no user token on inter-server calls yet).
    "/v1/acknowledge",
    "/api/v1/acknowledge",
}
PUBLIC_SUFFIXES = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/swagger",
)


def normalize_api_path(path: str) -> str:
    """Map nginx-stripped and full public paths onto a comparable form."""
    if not path:
        return "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") or "/"
    return path


def is_public_path(path: str) -> bool:
    path = normalize_api_path(path)
    if path in PUBLIC_PATH_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES):
        return True
    if any(path.endswith(suffix) for suffix in PUBLIC_SUFFIXES):
        return True
    return False


def path_requires_auth(path: str) -> bool:
    if mode() == "off":
        return False
    path = normalize_api_path(path)
    under_v1 = path.startswith("/v1/") or path.startswith("/api/v1/")
    if not under_v1:
        return False
    if is_public_path(path):
        return False
    return mode() in {"required", "optional"}
