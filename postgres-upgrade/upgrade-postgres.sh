#!/usr/bin/env bash
set -Eeuo pipefail

OLD_DATA_DIR="${PG13_DATA_DIR:-/var/lib/postgresql/13/data}"
NEW_DATA_DIR="${PG17_DATA_DIR:-/var/lib/postgresql/17/data}"
UPGRADE_DIR="${POSTGRES_UPGRADE_DIR:-/upgrade}"
OLD_BIN_DIR="${PG13_BIN_DIR:-/usr/lib/postgresql/13/bin}"
NEW_BIN_DIR="${PG17_BIN_DIR:-/usr/lib/postgresql/17/bin}"
POSTGRES_USER="${POSTGRES_USER:-myuser}"
PG_UPGRADE_LINK="${PG_UPGRADE_LINK:-false}"

log() {
    printf '[postgres-upgrade] %s\n' "$*"
}

fail() {
    log "ERROR: $*"
    exit 1
}

is_empty_dir() {
    [[ ! -d "$1" || -z "$(find "$1" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]
}

cluster_version() {
    local data_dir="$1"

    if [[ -f "${data_dir}/PG_VERSION" ]]; then
        tr -d '[:space:]' < "${data_dir}/PG_VERSION"
    fi
}

pg_control_value() {
    local key="$1"

    "${OLD_BIN_DIR}/pg_controldata" "${OLD_DATA_DIR}" \
        | awk -F: -v key="$key" '$1 == key { sub(/^[[:space:]]+/, "", $2); print $2; exit }'
}

append_if_missing() {
    local line="$1"
    local file="$2"

    grep -Fqx "$line" "$file" || printf '\n%s\n' "$line" >> "$file"
}

old_version="$(cluster_version "$OLD_DATA_DIR")"
new_version="$(cluster_version "$NEW_DATA_DIR")"

if [[ "$new_version" == "17" ]]; then
    log "PostgreSQL 17 data directory already exists at ${NEW_DATA_DIR}; skipping upgrade."
    exit 0
fi

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

    log "Existing PostgreSQL 17 data found in legacy directory; copying it to ${NEW_DATA_DIR}."
    mkdir -p "$NEW_DATA_DIR"
    cp -a "${OLD_DATA_DIR}/." "$NEW_DATA_DIR/"
    chown -R postgres:postgres "$NEW_DATA_DIR"
    exit 0
fi

if [[ "$old_version" != "13" ]]; then
    fail "Unsupported PostgreSQL data directory version ${old_version}. Automatic upgrade supports only 13 to 17."
fi

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

append_if_missing "listen_addresses = '*'" "${NEW_DATA_DIR}/postgresql.conf"
append_if_missing "host all all all md5" "${NEW_DATA_DIR}/pg_hba.conf"

touch "${UPGRADE_DIR}/postgres-13-to-17.done"
log "Upgrade complete. Original PostgreSQL 13 data remains at ${OLD_DATA_DIR}; active PostgreSQL 17 data is at ${NEW_DATA_DIR}."
