#!/bin/sh
# Runs inside the nginx container before nginx starts (via /docker-entrypoint.d/).
# Ensures /etc/nginx/certs-active/ contains cmf.crt and cmf.key so the 443 ssl
# server block always has a certificate to load:
#   - if the user mounted a certificate in /etc/nginx/certs/, use it
#   - otherwise generate a throwaway self-signed cert (non-persistent)
#
# This prevents nginx from crashing on startup when the operator has not yet
# run scripts/generate-self-signed-cert.sh on the host. For a stable/persistent
# certificate, run that script (or supply your own cmf.crt/cmf.key in
# $CMF_DATA_DIR/nginx-certs/).
set -eu

SRC_DIR=/etc/nginx/certs
ACTIVE_DIR=/etc/nginx/certs-active
mkdir -p "$ACTIVE_DIR"

# Reuse a user-provided certificate if present and non-empty.
if [ -s "$SRC_DIR/cmf.crt" ] && [ -s "$SRC_DIR/cmf.key" ]; then
    cp "$SRC_DIR/cmf.crt" "$ACTIVE_DIR/cmf.crt"
    cp "$SRC_DIR/cmf.key" "$ACTIVE_DIR/cmf.key"
    echo "[autogen-cert] Using user-provided certificate from $SRC_DIR"
    exit 0
fi

echo "[autogen-cert] No certificate found in $SRC_DIR; generating a throwaway self-signed cert"

# nginx:alpine does not ship openssl; install it on demand.
if ! command -v openssl >/dev/null 2>&1; then
    echo "[autogen-cert] Installing openssl..."
    apk add --no-cache openssl >/dev/null
fi

HOST="$(hostname 2>/dev/null || echo localhost)"
openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
    -keyout "$ACTIVE_DIR/cmf.key" \
    -out     "$ACTIVE_DIR/cmf.crt" \
    -subj "/CN=$HOST" \
    -addext "subjectAltName=DNS:localhost,DNS:$HOST,IP:127.0.0.1" >/dev/null 2>&1

echo "[autogen-cert] Generated throwaway self-signed cert for CN=$HOST (regenerated on each start)"
