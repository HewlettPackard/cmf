/***
 * Keycloak session helpers for the CMF UI.
 * Tokens come from POST /v1/auth/token (password grant); secret stays on the API.
 ***/

import config from "./config";

const TOKEN_KEY = "cmf_keycloak_access_token";
const USER_KEY = "cmf_keycloak_username";
const EXPIRES_KEY = "cmf_keycloak_expires_at";

const runtimeConfig = window.RUNTIME_CONFIG || {};

export function keycloakClientId() {
  return (
    runtimeConfig.KEYCLOAK_CLIENT_ID ||
    process.env.REACT_APP_KEYCLOAK_CLIENT_ID ||
    "d3dsearch"
  );
}

export function getAccessToken() {
  const token = sessionStorage.getItem(TOKEN_KEY);
  if (!token) return null;
  const expiresAt = Number(sessionStorage.getItem(EXPIRES_KEY) || 0);
  if (expiresAt && Date.now() >= expiresAt - 15_000) {
    clearSession();
    return null;
  }
  return token;
}

export function getUsername() {
  return sessionStorage.getItem(USER_KEY) || "";
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(EXPIRES_KEY);
}

function decodeJwtPayload(token) {
  try {
    const part = token.split(".")[1];
    const padded = part + "=".repeat((4 - (part.length % 4)) % 4);
    return JSON.parse(atob(padded.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return {};
  }
}

export function storeSession(tokenResponse) {
  const token = tokenResponse.access_token;
  if (!token) throw new Error("No access_token in response");
  const expiresIn = Number(tokenResponse.expires_in || 300);
  const claims = decodeJwtPayload(token);
  const username =
    claims.preferred_username || claims.email || claims.azp || "user";
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(USER_KEY, username);
  sessionStorage.setItem(EXPIRES_KEY, String(Date.now() + expiresIn * 1000));
  return { username, expiresIn };
}

/** Fetch auth mode from the API (public). */
export async function fetchAuthConfig() {
  const url = `${config.apiBasePath}/v1/auth/config`;
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`auth/config failed (${res.status})`);
  const body = await res.json();
  return body.data || body;
}

export function authIsRequired(authConfig) {
  const mode = (authConfig?.mode || "off").toLowerCase();
  return mode === "required";
}

/** Password grant via CMF API (server attaches client_secret). */
export async function loginWithPassword(username, password) {
  const url = `${config.apiBasePath}/v1/auth/token`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      grant_type: "password",
      client_id: keycloakClientId(),
      username,
      password,
    }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      body?.message ||
      body?.errors?.[0]?.message ||
      body?.error?.message ||
      `Login failed (${res.status})`;
    throw new Error(msg);
  }
  const data = body.data || body;
  return storeSession(data);
}

export function logout() {
  clearSession();
  window.location.href = "/login";
}
