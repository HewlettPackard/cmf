# Automatic PostgreSQL 17 Upgrade

This directory contains the helper image and script used to automatically move CMF from PostgreSQL 13 to PostgreSQL 17.

## Files

```text
postgres-upgrade/
├── Dockerfile
├── README.md
└── upgrade-postgres.sh
```

- `Dockerfile` builds the upgrade helper image.
- `upgrade-postgres.sh` checks the existing PostgreSQL data directory and runs the upgrade when needed.

## Docker Compose Services

The upgrade flow uses two services in `docker-compose-server.yml`:

```text
postgres-upgrade  one-time helper that upgrades PG13 data to PG17
postgres          actual PostgreSQL 17 database used by CMF
```

The `postgres-upgrade` service runs first. The `postgres` service starts only after the upgrade service exits successfully.

## Data Directories

CMF keeps PostgreSQL 13 and PostgreSQL 17 data in separate directories:

```text
${CMF_DATA_DIR}/postgres_data      original PostgreSQL 13 data
${CMF_DATA_DIR}/postgres_data_17   active PostgreSQL 17 data
${CMF_DATA_DIR}/postgres_upgrade   upgrade logs and marker files
```

This protects the original PostgreSQL 13 data if an upgrade fails and makes it clear which data directory is used by PostgreSQL 17.

## Automatic Startup

To start CMF and let Docker Compose run the upgrade automatically:

```bash
docker compose -f docker-compose-server.yml up -d --build
```

What happens:

```text
1. postgres-upgrade image is built if needed.
2. postgres-upgrade checks the mounted data directories.
3. If PostgreSQL 13 data exists, pg_upgrade creates PostgreSQL 17 data.
4. If PostgreSQL 17 data already exists, upgrade is skipped.
5. postgres:17 starts with postgres_data_17.
6. CMF server, UI, MCP, TensorBoard, and Nginx start after PostgreSQL is healthy.
```

## Manual Upgrade Command

To run only the upgrade step manually:

```bash
docker compose -f docker-compose-server.yml run --rm --build postgres-upgrade
```

Recommended manual sequence:

```bash
docker compose -f docker-compose-server.yml stop server ui mcp nginx postgres

docker compose -f docker-compose-server.yml run --rm --build postgres-upgrade

docker compose -f docker-compose-server.yml up -d postgres

docker compose -f docker-compose-server.yml up -d server ui mcp nginx
```

## Upgrade Behavior

The script is idempotent and handles these cases:

```text
No existing PostgreSQL data:
  skip upgrade; postgres:17 initializes a fresh database

Existing PostgreSQL 13 data:
  initialize PostgreSQL 17 data directory
  run pg_upgrade from 13 to 17
  preserve original PostgreSQL 13 data

Existing PostgreSQL 17 data:
  skip upgrade; database is already upgraded

Unsupported PostgreSQL version:
  fail safely and do not start PostgreSQL 17
```

## Safe Default Mode

By default, the upgrade uses copy mode:

```bash
PG_UPGRADE_LINK=false
```

Copy mode requires more disk space, but the original PostgreSQL 13 data remains independent from the new PostgreSQL 17 data.

For faster upgrades with less disk usage, set:

```bash
PG_UPGRADE_LINK=true
```

This enables `pg_upgrade --link`. Link mode is faster, but rollback is more restrictive because old and new clusters share files.

## Validation

Check that the running PostgreSQL container is version 17:

```bash
docker compose -f docker-compose-server.yml exec -T postgres postgres --version
```

Expected output starts with:

```text
PostgreSQL 17
```

Check the active database server version:

```bash
docker compose -f docker-compose-server.yml exec -T postgres \
    psql -U "${POSTGRES_USER:-myuser}" \
    -d "${POSTGRES_DB:-mlmd}" \
    -tAc "SHOW server_version;"
```

Expected output starts with:

```text
17
```

Check the active data directory version:

```bash
docker compose -f docker-compose-server.yml exec -T postgres \
    cat /var/lib/postgresql/data/PG_VERSION
```

Expected output:

```text
17
```
