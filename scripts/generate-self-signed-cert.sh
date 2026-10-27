#!/usr/bin/env bash
# Generate a self-signed TLS certificate for the CMF nginx HTTPS endpoint.
#
# Recommended but not strictly required: the nginx container's entrypoint
# (scripts/nginx-autogen-cert.sh) will generate a throwaway cert on startup
# if none is mounted. Run THIS script to create a STABLE cert that persists
# across restarts and covers your hostname/IP in the SAN.
#
# Certs are written to $CMF_DATA_DIR/nginx-certs/ (or ./data/nginx-certs/ if
# CMF_DATA_DIR is unset) and are consumed by the nginx service via the volume
# mount defined in docker-compose-server.yml.
#
# Usage:
#   scripts/generate-self-signed-cert.sh [OUTPUT_DIR] [HOSTNAME] [IP]
#
# Defaults:
#   OUTPUT_DIR = ${CMF_DATA_DIR:-./data}/nginx-certs
#   HOSTNAME   = $(hostname)
#   IP         = first IPv4 address detected on this host (best-effort; see below)
set -euo pipefail

OUT_DIR="${1:-${CMF_DATA_DIR:-./data}/nginx-certs}"
HOST="${2:-$(hostname)}"

# Detect the host's primary IPv4 address. `hostname -I` is Linux-specific and
# may be empty on macOS/minimal containers; fall back to `ip` and `ifconfig`.
# If detection fails, the IP is simply omitted from the SAN — the cert still
# validates for localhost and the hostname.
detect_ip() {
  local ip=""
  # Linux: `hostname -I` prints space-separated IPv4/IPv6 list
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')" || ip=""
  # Fallback: `ip -4 route get 1.1.1.1` (Linux)
  if [ -z "$ip" ]; then
    ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}')" || ip=""
  fi
  # Fallback: `ifconfig` (macOS / older Linux)
  if [ -z "$ip" ]; then
    ip="$(ifconfig 2>/dev/null | awk '/inet / && !/127.0.0.1/ {sub(/addr:/,"",$2); print $2; exit}')" || ip=""
  fi
  # Validate it looks like an IPv4 address
  if [ -n "$ip" ] && printf '%s' "$ip" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
    printf '%s' "$ip"
  fi
}
IP="${3:-$(detect_ip)}"

mkdir -p "$OUT_DIR"

# Build the SAN extension. Always include localhost and the hostname as DNS
# entries and 127.0.0.1 as an IP. Add the detected host IP only if non-empty
# so we never produce a malformed `IP:` entry.
SAN="DNS:localhost,DNS:$HOST,IP:127.0.0.1"
if [ -n "$IP" ] && [ "$IP" != "127.0.0.1" ]; then
  SAN="$SAN,IP:$IP"
fi

openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
  -keyout "$OUT_DIR/cmf.key" \
  -out     "$OUT_DIR/cmf.crt" \
  -subj "/CN=$HOST" \
  -addext "subjectAltName=$SAN"

echo "Wrote $OUT_DIR/cmf.crt and $OUT_DIR/cmf.key"
echo "  CN        : $HOST"
echo "  SAN       : $SAN"
if [ -n "$IP" ]; then
  echo "  Host IP   : $IP"
else
  echo "  Host IP   : (not detected — cert covers localhost and $HOST only)"
fi
