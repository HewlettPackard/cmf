# Keycloak bearer auth for CMF API

ADIL enables Keycloak OIDC on the CMF REST API (`/api/v1/*`), matching FEDER.

## Enable

In `.env` (from `env-example`):

```bash
KEYCLOAK_AUTH_MODE=required
KEYCLOAK_CLIENT_ID=d3dsearch
KEYCLOAK_CLIENT_SECRET=<server-only secret>
KEYCLOAK_SSL_VERIFY=false
```

Rebuild/restart the `server` service so `PyJWT` / `cryptography` are installed.

## Call the API

1. Mint a **user** token (no client secret in the request — server attaches it):

```bash
curl -sS -X POST 'http://127.0.0.1:8089/api/v1/auth/token' \
  -H 'Content-Type: application/json' \
  -d '{"grant_type":"password","client_id":"d3dsearch","username":"...","password":"..."}'
```

2. Call protected routes with the bearer:

```bash
TOKEN=...
curl -sS -H "Authorization: Bearer $TOKEN" \
  'http://127.0.0.1:8089/api/v1/pipelines'
```

## Public without a token

- `GET /` (health)
- `GET /api/v1/auth/config`, `/auth/status`, `POST /api/v1/auth/token`
- `POST /api/v1/acknowledge` (peer federation handshake)
- OpenAPI `/docs`, `/openapi.json`

## UI login

When `KEYCLOAK_AUTH_MODE=required`, open http://127.0.0.1:8089/ — you are
redirected to **/login**. Sign in with Keycloak username/password; the UI stores
the access token in `sessionStorage` and sends `Authorization: Bearer …` on API
calls. Use **Log out** in the header to clear the session.

## Modes

| `KEYCLOAK_AUTH_MODE` | Behaviour |
|---|---|
| `off` | No bearer check (default) |
| `optional` | Validates if present; does not reject missing |
| `required` | Missing/invalid JWT → **401**; UI shows login page |

