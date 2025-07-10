#!/bin/bash
set -e  # Exit on any error

echo "Starting PostgreSQL..."

# Start PostgreSQL in the background
docker-entrypoint.sh postgres -c port=${POSTGRES_PORT} &

# Wait until PostgreSQL is ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -p "$POSTGRES_PORT"; do
  echo "Waiting for PostgreSQL to be ready on port ${POSTGRES_PORT}..."
  sleep 2
done

echo "PostgreSQL is ready on port ${POSTGRES_PORT}!"

# Check if the database exists, and create it if it doesn't
DB_EXISTS=$(psql -U "$POSTGRES_USER" -p "$POSTGRES_PORT" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'")

if [ "$DB_EXISTS" != "1" ]; then
  echo "Database $POSTGRES_DB does not exist. Creating it..."
  createdb -U "$POSTGRES_USER" -p "$POSTGRES_PORT" "$POSTGRES_DB"
  echo "Database $POSTGRES_DB created!"
else
  echo "Database $POSTGRES_DB already exists."
fi

# Run the SQL script every time the server starts
if [ -f /docker-entrypoint-initdb.d/db_init.sql ]; then
  echo "Running SQL script..."
  psql -U "$POSTGRES_USER" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/db_init.sql
  echo "SQL script executed!"
else
  echo "SQL script not found!"
fi

# Keep PostgreSQL running in the foreground
wait
