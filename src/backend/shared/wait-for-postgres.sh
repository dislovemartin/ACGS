#!/bin/sh
# wait-for-postgres.sh

set -e

host="$1"
user="$2"
password="$3"
# Shift away the first three arguments (host, user, password)
shift 3 
# The rest of the arguments are the command to execute after Postgres is ready
cmd="$@"

# Loop until Postgres is available
# PGPASSWORD is used by psql for non-interactive password authentication
# `psql -h host -U user -c '\q'` attempts to connect and quit immediately.
# If successful, it exits with 0. If not, it exits with a non-zero code.
until PGPASSWORD=$password psql -h "$host" -U "$user" -d "${POSTGRES_DB:-acgs_pgp_db}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

# >&2 echoes to stderr
>&2 echo "Postgres is up - executing command: $cmd"
# Execute the command passed in after Postgres is ready
exec $cmd
