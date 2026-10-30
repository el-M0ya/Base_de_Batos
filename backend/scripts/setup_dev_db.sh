#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# This script initializes the development database from scratch by executing
# all SQL scripts in numeric order. 
#
# Rules:
#   - Use psql only (no Alembic/migrations framework)
#   - Stop on first error using ON_ERROR_STOP=1
#   - Drop and recreate the target database if it exists
#   - Run scripts in the exact order: 001_ -> 008_
#   - Respect the updated MERX: routine block structure stored as JSONB in
#     PostgreSQL (routine_structure)
#   - Read connection parameters from environment or .env
# -----------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
SCRIPTS_DIR="${REPO_ROOT}/backend/database/scripts"
ENV_FILE="${REPO_ROOT}/.env"

# Load .env if present
if [[ -f "${ENV_FILE}" ]]; then
  echo "[INFO] Loading environment variables from .env"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

# Connection parameters (defaults aligned with compose.yaml/.env.example)
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-basedebatos}"
PGPASSWORD="${PGPASSWORD:-basedebatos}"
PGDATABASE="${PGDATABASE:-basedebatos}"

export PGPASSWORD

echo "[INFO] Database initialization started"
echo "[INFO] Host: ${PGHOST}:${PGPORT} | User: ${PGUSER} | Target DB: ${PGDATABASE}"
echo "[INFO] Scripts directory: ${SCRIPTS_DIR}"

# Ensure psql is available
if ! command -v psql >/dev/null 2>&1; then
  echo "[ERROR] 'psql' not found in PATH. Install PostgreSQL client tools or use them via Docker."
  exit 1
fi

# Terminate existing connections and recreate database
echo "[INFO] Terminating active connections to '${PGDATABASE}' (if any)..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -v ON_ERROR_STOP=1 \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${PGDATABASE}' AND pid <> pg_backend_pid();" >/dev/null || true

echo "[INFO] Dropping database '${PGDATABASE}' if exists..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -v ON_ERROR_STOP=1 \
  -c "DROP DATABASE IF EXISTS \"${PGDATABASE}\";"

echo "[INFO] Creating database '${PGDATABASE}' owned by '${PGUSER}'..."
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -v ON_ERROR_STOP=1 \
  -c "CREATE DATABASE \"${PGDATABASE}\" OWNER \"${PGUSER}\";"

echo "[INFO] Executing SQL scripts in numeric order with ON_ERROR_STOP..."

# Execute in strict numeric order
for script in \
  "${SCRIPTS_DIR}/001_identity_and_sites.sql" \
  "${SCRIPTS_DIR}/002_catalogs_and_programs.sql" \
  "${SCRIPTS_DIR}/003_exercises_authorisations_enrolments.sql" \
  "${SCRIPTS_DIR}/004_routines_and_structure.sql" \
  "${SCRIPTS_DIR}/005_validation_assignments_sessions_adjustments.sql" \
  "${SCRIPTS_DIR}/006_integrity_constraints.sql" \
  "${SCRIPTS_DIR}/007_consistency_triggers.sql" \
  "${SCRIPTS_DIR}/008_catalog_seeds.sql"
do
  if [[ -f "${script}" ]]; then
    echo "[RUN] $(basename "${script}")"
    psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -v ON_ERROR_STOP=1 -f "${script}"
  else
    echo "[WARN] Skipping missing script: $(basename "${script}")"
  fi
done

echo "[SUCCESS] Development database '${PGDATABASE}' initialized from scratch."
echo "[INFO] You can now connect with: psql -h ${PGHOST} -p ${PGPORT} -U ${PGUSER} -d ${PGDATABASE}"