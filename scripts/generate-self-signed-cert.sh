#!/usr/bin/env bash
# Generate a self-signed TLS certificate for the CMF nginx HTTPS endpoint.
#
# REQUIRED: the nginx service has a 443 ssl server block that will fail to
# start without cmf.crt and cmf.key. Run this script before `docker compose up`.
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
#   IP         = first IPv4 address reported by `hostname -I`
set -euo pipefail

OUT_DIR="${1:-${CMF_DATA_DIR:-./data}/nginx-certs}"
HOST="${2:-$(hostname)}"
IP="${3:-$(hostname -I | awk '{print $1}')}"

mkdir -p "$OUT_DIR"

openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
  -keyout "$OUT_DIR/cmf.key" \
  -out     "$OUT_DIR/cmf.crt" \
  -subj "/CN=$HOST" \
  -addext "subjectAltName=DNS:localhost,DNS:$HOST,IP:$IP,IP:127.0.0.1"

echo "Wrote $OUT_DIR/cmf.crt and $OUT_DIR/cmf.key"
echo "  CN        : $HOST"
echo "  SAN hosts : localhost, $HOST"
echo "  SAN IPs   : $IP, 127.0.0.1"
