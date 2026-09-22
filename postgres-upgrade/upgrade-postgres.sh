#!/usr/bin/env bash
###
# Copyright (2026) Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###

set -Eeuo pipefail

# These paths match the volume mounts configured for the postgres-upgrade service.
# OLD_DATA_DIR is kept as the rollback source; NEW_DATA_DIR becomes the active PG17 cluster.
OLD_DATA_DIR="${PG13_DATA_DIR:-/var/lib/postgresql/13/data}"
NEW_DATA_DIR="${PG17_DATA_DIR:-/var/lib/postgresql/17/data}"
UPGRADE_DIR="${POSTGRES_UPGRADE_DIR:-/upgrade}"

# pg_upgrade requires binaries from both the old and new PostgreSQL versions.
OLD_BIN_DIR="${PG13_BIN_DIR:-/usr/lib/postgresql/13/bin}"
NEW_BIN_DIR="${PG17_BIN_DIR:-/usr/lib/postgresql/17/bin}"
POSTGRES_USER="${POSTGRES_USER:-myuser}"
PG_UPGRADE_LINK="${PG_UPGRADE_LINK:-false}"

# Log a message with a consistent prefix.
log() {
    printf '[postgres-upgrade] %s\n' "$*"
}

# Print an error message and exit the script.
fail() {
    log "ERROR: $*"
    exit 1
}

# Check if a directory is empty or does not exist. Returns true if the directory is empty or missing.
is_empty_dir() {
    [[ ! -d "$1" || -z "$(find "$1" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]
}

# Determine the PostgreSQL cluster version from the data directory. Returns the version number as a string.
cluster_version() {
    local data_dir="$1"

    if [[ -f "${data_dir}/PG_VERSION" ]]; then
        tr -d '[:space:]' < "${data_dir}/PG_VERSION"
    fi
}

# Retrieve a specific value from the pg_controldata output of the old PostgreSQL cluster.
pg_control_value() {
    local key="$1"

    "${OLD_BIN_DIR}/pg_controldata" "${OLD_DATA_DIR}" \
        | awk -F: -v key="$key" '$1 == key { sub(/^[[:space:]]+/, "", $2); print $2; exit }'
}

# Append a line to a file if it is not already present.
append_if_missing() {
    local line="$1"
    local file="$2"

    grep -Fqx "$line" "$file" || printf '\n%s\n' "$line" >> "$file"
}

old_version="$(cluster_version "$OLD_DATA_DIR")"
new_version="$(cluster_version "$NEW_DATA_DIR")"

# The upgrade service is intentionally idempotent so it can run on every compose startup.
if [[ "$new_version" == "17" ]]; then
    log "PostgreSQL 17 data directory already exists at ${NEW_DATA_DIR}; skipping upgrade."
    exit 0
fi

# Fresh installs have no PG13 data. In that case, the normal postgres:17 container initializes the DB.
if is_empty_dir "$OLD_DATA_DIR"; then
    log "No PostgreSQL 13 data directory found; fresh PostgreSQL 17 initialization will be handled by the postgres service."
    exit 0
fi

if [[ -z "$old_version" ]]; then
    fail "${OLD_DATA_DIR} is not empty, but PG_VERSION is missing. Refusing to continue."
fi

if [[ "$old_version" == "17" ]]; then
    if ! is_empty_dir "$NEW_DATA_DIR"; then
        fail "${NEW_DATA_DIR} exists but is not a valid PostgreSQL 17 data directory."
    fi

    # Support deployments that already placed PG17 data in the legacy mount path.
    log "Existing PostgreSQL 17 data found in legacy directory; copying it to ${NEW_DATA_DIR}."
    mkdir -p "$NEW_DATA_DIR"
    cp -a "${OLD_DATA_DIR}/." "$NEW_DATA_DIR/"
    chown -R postgres:postgres "$NEW_DATA_DIR"
    exit 0
fi

if [[ "$old_version" != "13" ]]; then
    fail "Unsupported PostgreSQL data directory version ${old_version}. Automatic upgrade supports only 13 to 17."
fi

# pg_upgrade must run only when the old PostgreSQL cluster is fully stopped.
if [[ -f "${OLD_DATA_DIR}/postmaster.pid" ]]; then
    fail "PostgreSQL 13 appears to be running or was not stopped cleanly. Stop the old database and remove only a stale postmaster.pid after verifying no postgres process is using the data directory."
fi

if ! is_empty_dir "$NEW_DATA_DIR"; then
    fail "${NEW_DATA_DIR} exists but is not a valid PostgreSQL 17 data directory. Move it aside before retrying."
fi

mkdir -p "$NEW_DATA_DIR" "$UPGRADE_DIR"
chown -R postgres:postgres "$NEW_DATA_DIR" "$UPGRADE_DIR"

old_encoding="$(pg_control_value 'Database encoding')"
old_lc_collate="$(pg_control_value 'LC_COLLATE')"
old_lc_ctype="$(pg_control_value 'LC_CTYPE')"

# Initialize the new cluster with the old cluster's locale settings so pg_upgrade can compare them safely.
initdb_args=(
    -D "$NEW_DATA_DIR"
    --username="$POSTGRES_USER"
)

if [[ -n "$old_encoding" ]]; then
    initdb_args+=(--encoding="$old_encoding")
fi

if [[ -n "$old_lc_collate" ]]; then
    initdb_args+=(--lc-collate="$old_lc_collate")
fi

if [[ -n "$old_lc_ctype" ]]; then
    initdb_args+=(--lc-ctype="$old_lc_ctype")
fi

log "Initializing PostgreSQL 17 data directory at ${NEW_DATA_DIR}."
gosu postgres "${NEW_BIN_DIR}/initdb" "${initdb_args[@]}"

# Keep copy mode as the default because it preserves the original PG13 data directory independently.
upgrade_args=(
    --old-datadir="$OLD_DATA_DIR"
    --new-datadir="$NEW_DATA_DIR"
    --old-bindir="$OLD_BIN_DIR"
    --new-bindir="$NEW_BIN_DIR"
    --username="$POSTGRES_USER"
)

if [[ "${PG_UPGRADE_LINK,,}" == "true" ]]; then
    log "Using pg_upgrade --link mode. This is faster and uses less disk, but rollback is more restrictive."
    upgrade_args+=(--link)
fi

log "Running pg_upgrade from PostgreSQL 13 to PostgreSQL 17."
cd "$UPGRADE_DIR"
gosu postgres "${NEW_BIN_DIR}/pg_upgrade" "${upgrade_args[@]}"

# Match the official postgres image defaults so the upgraded cluster accepts container network connections.
append_if_missing "listen_addresses = '*'" "${NEW_DATA_DIR}/postgresql.conf"
append_if_missing "host all all all md5" "${NEW_DATA_DIR}/pg_hba.conf"

touch "${UPGRADE_DIR}/postgres-13-to-17.done"
log "Upgrade complete. Original PostgreSQL 13 data remains at ${OLD_DATA_DIR}; active PostgreSQL 17 data is at ${NEW_DATA_DIR}."
