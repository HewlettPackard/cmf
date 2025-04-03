#!/bin/bash
set -e  # Exit on any error

echo "Starting PostgreSQL..."

# Start PostgreSQL in the background
docker-entrypoint.sh postgres &

# Wait until PostgreSQL is ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Run the SQL script every time the server starts
if [ -f /docker-entrypoint-initdb.d/db_init.sql ]; then
  echo "Running SQL script..."
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/db_init.sql
  echo "SQL script executed!"
else
  echo "SQL script not found!"
fi

# Keep PostgreSQL running in the foreground
wait

