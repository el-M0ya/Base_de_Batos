# Database Scripts

This directory contains the SQL scripts that define and initialize the relational schema for the **Base de Batos** project. 

These scripts are the **single source of truth** for the physical model. The environment is orchestrated via `compose.yaml` (PostgreSQL 17 + Redis 8). Routine block structure is stored as **JSONB** in `routine_structure` (one-to-one with `routine`) in the same transaction, following **issue #23**.

## Execution Order

Scripts must be executed in the following numeric order:

| Script | Issue | Purpose |
| :-- | :-- | :-- |
| `001_identity_and_sites.sql` | #20 | `app_user`, `trainer`, `site`, `client` (room chiefs use trainer identity with `can_validate` authorization) |
| `002_catalogs_and_programs.sql.sql` | #21 | `workout_program`, `muscle_group`, `exercise_type`, `covers` |
| `003_exercises_authorisations_enrolments.sql` | #22 | `exercise`, `authorises`, `inscribed` |
| `004_routines_and_structure.sql` | #23 | `routine`, `parameters_routine`, `contains`, `routine_structure` (JSONB). Routine and structure created atomically in one transaction. |
| `005_validation_assignments_sessions_adjustments.sql` | #24 | `validate`, `assignment`, `session`, `request`, `adjustment_result` |
| `006_integrity_constraints.sql` | #25 | Uniqueness, domain CHECKs, temporal CHECKs and supporting indexes aligned with the physical schema |
| `007_consistency_triggers.sql` | #26 | Model consistency triggers (role/specialization checks, routine state consistency, adjustment resolver validation) and cache invalidation hooks for Redis |
| `008_catalog_seeds.sql` | #27 | Initial exercise-type catalog data |
| `010_add_user_is_active.sql` | Auth | Adds the active flag used by user sessions |
| `011_routine_parameters_full_generation.sql` | E6-02 | Adds the flexibility proportion and muscle-group coverage snapshot to `parameters_routine` |
| `012_routine_replacement.sql` | #122 | Adds `routine.id_routine_origin`, the `REPLACED` status, and a unique successor-per-source constraint |

## Initialize from Scratch

The recommended way is to use the provided script. It **does not use Alembic** and stops at the first error (`ON_ERROR_STOP`).

### On Linux / macOS / Git Bash (Windows)

```bash
# Make it executable (first time)
chmod +x backend/scripts/setup_dev_db.sh

# Run from repository root
./backend/scripts/setup_dev_db.sh
