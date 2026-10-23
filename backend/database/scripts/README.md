# Database Scripts

This directory contains the SQL scripts that define and initialize the relational schema for the **Base de Batos** project. 

These scripts are the **single source of truth** for the physical model. The environment is orchestrated via `compose.yaml` (PostgreSQL 17 + Redis 8). Routine block structure is stored as **JSONB** in `routine_structure` (one-to-one with `routine`) in the same transaction, following **issue #23**.

## Execution Order

Scripts must be executed in the following numeric order:

| Script | Issue | Purpose |
| :-- | :-- | :-- |
| `001_identity_and_sites.sql` | #20 | `user`, `trainer`, `room_chief`, `site`, `client` (role stored as attribute of `user`, generalization resolved by shared PKs) |
| `002_catalogs_and_programs.sql` | #21 | `workout_program`, `muscle_group`, `exercise_type`, `intensity_level`, `covers` |
| `003_exercises_authorisations_enrolments.sql` | #22 | `exercise`, `authorises`, `inscribed` |
| `004_routines_and_structure.sql` | #23 | `routine`, `parameters_routine`, `contains`, `routine_structure` (JSONB). Routine and structure created atomically in one transaction. |
| `005_validation_assignments_sessions_adjustments.sql` | #24 | `validate`, `assignment`, `session`, `request`, `adjustment_result` |
| `006_integrity_constraints.sql` | #25 | Uniqueness (U-1–U-12), domain CHECKs, temporal CHECKs and supporting indexes |
| `007_consistency_triggers.sql` | #26 | Model consistency triggers (role/specialization checks, routine state consistency, adjustment resolver validation) and cache invalidation hooks for Redis |
| `008_catalog_seeds.sql` | #27 | Initial catalog data and SQL fixtures for development/testing |

## Initialize from Scratch

The recommended way is to use the provided script. It **does not use Alembic** and stops at the first error (`ON_ERROR_STOP`).

### On Linux / macOS / Git Bash (Windows)

```bash
# Make it executable (first time)
chmod +x backend/scripts/setup_dev_db.sh

# Run from repository root
./backend/scripts/setup_dev_db.sh