# Physical PostgreSQL schema

**Repository:** `el-M0ya/Base_de_Batos`  
**Parent epic:** #17 — [E1] Database and SQL Infrastructure  
**Issue:** #29 — E1-11 Document the Physical Schema and Mapping to the Approved Design  
**Scope:** Physical definitions in `backend/database/scripts/001_*` through `005_*`, integrity definitions in `006_*`, and triggers in `007_*`.

## 1. Source of truth and interpretation

This document distinguishes three things that must not be conflated:

1. **Declared physical DDL:** the table and column definitions actually present in SQL scripts 001–005. These definitions determine the physical names and types recorded below.
2. **Integrity and trigger intent:** scripts 006 and 007, which add constraints, indexes, and cross-table checks. Script 006 currently contains references that do not match the DDL in scripts 001–005; those statements are listed as unresolved rather than described as successfully installed.
3. **Approved design relations:** the 21 original relations identified in the project design documentation. Their mapping is in [schema-mapping.md](schema-mapping.md).

The SQL files currently declare **20 tables** across scripts 001–005. Of these, 19 are physical tables corresponding to original design relations and one is the additional `routine_structure` table. The original `ROOMCHIEF` and `INTENSITYLEVEL` relations do not have their own `CREATE TABLE` statements in the current scripts. `validate` nevertheless references `room_chief`, so the current sequence cannot create that table successfully without resolving the missing referenced relation.

This is a static review of the checked-in DDL. No live PostgreSQL instance was available through the repository connection, so this document does not claim that the complete initialization sequence has been executed successfully.

## 2. SQL script inventory

| Order | File as it exists in the repository | Tables declared |
|---|---|---|
| 001 | `backend/database/scripts/001_identity_and_sites.sql` | `site`, `app_user`, `trainer`, `client` |
| 002 | `backend/database/scripts/002_catalogs_and_programs.sql.sql` | `muscle_group`, `exercise_type`, `workout_program`, `covers` |
| 003 | `backend/database/scripts/003_exercises_authorisations_enrolments.sql` | `exercise`, `authorises`, `inscribed` |
| 004 | `backend/database/scripts/004_routines_and_structure.sql` | `routine`, `parameters_routine`, `contains`, `routine_structure` |
| 005 | `backend/database/scripts/005_validation_assignments_sessions_adjustments.sql` | `validate`, `assignment`, `session`, `request`, `adjustment_result` |
| 006 | `backend/database/scripts/006_integrity_constraints.sql` | Adds constraints and indexes; see §7 for mismatches |
| 007 | `backend/database/scripts/007_consistency_triggers.sql` | Adds three trigger mechanisms; see §8 |

> The double `.sql.sql` suffix on script 002 is the actual tracked filename. It is intentionally documented as-is; this issue does not rename SQL files.

## 3. Physical table inventory

The complete field-by-field dictionary, including types, nullability, defaults, and key roles, is in [data-dictionary.md](data-dictionary.md).

| Physical table | Purpose | Primary key | Main foreign keys |
|---|---|---|---|
| `site` | Gym site | `id_site` | — |
| `app_user` | Account, credentials, persisted role | `id_user` | — |
| `trainer` | Trainer specialization of a user | `id_trainer` | `app_user(id_user)` |
| `client` | Client specialization and site membership | `id_client` | `app_user(id_user)`, `site(id_site)` |
| `muscle_group` | Muscle-group catalog | `id_muscle_group` | — |
| `exercise_type` | Exercise-type catalog | `id_exercise_type` | — |
| `workout_program` | Training program | `id_workout_program` | — |
| `covers` | Program-to-muscle-group association | `(id_workout_program, id_muscle_group)` | `workout_program`, `muscle_group` |
| `exercise` | Exercise catalog and authorship | `id_exercise` | `exercise_type`, `muscle_group`, `trainer` |
| `authorises` | Trainer permissions per program | `(id_trainer, id_workout_program)` | `trainer`, `workout_program` |
| `inscribed` | Client enrollment in a program | `(id_client, id_workout_program)` | `client`, `workout_program` |
| `routine` | Routine header and status | `id_routine` | `workout_program`, `trainer`, optional `client` |
| `parameters_routine` | One generation-parameter row per routine | `id_routine` | `routine(id_routine)` |
| `contains` | Ordered exercise composition | `(id_routine, id_exercise, execution_order)` | `routine`, `exercise` |
| `routine_structure` | Variable routine blocks in JSONB | `id_routine` | `routine(id_routine)` |
| `validate` | Routine review/validation record | `id_validation` | `routine`, **missing** `room_chief` relation |
| `assignment` | Routine assigned to a client | `id_assignment` | `routine`, `client` |
| `session` | Training session against an assignment | `id_session` | `assignment` |
| `request` | Client adjustment request | `id_request` | `client`, `routine`, `trainer` |
| `adjustment_result` | Result for an adjustment request | `id_request` | `request`, resulting `routine`, resolving `trainer` |

### 3.1 Relationship and cardinality summary

- `app_user` to `trainer`: one-to-zero-or-one specialization. `trainer.id_trainer` is both its primary key and a foreign key to `app_user.id_user`.
- `app_user` to `client`: one-to-zero-or-one specialization. `client.id_client` is both its primary key and a foreign key to `app_user.id_user`.
- `site` to `client`: one-to-many; each client row has one required `id_site`.
- `workout_program` to `muscle_group`: many-to-many through `covers`.
- `exercise_type`, `muscle_group`, and `trainer` to `exercise`: each referenced catalog/trainer row may be associated with many exercises; each exercise has one required row in each relationship.
- `trainer` to `workout_program`: many-to-many through `authorises`, with permission and validity attributes.
- `client` to `workout_program`: many-to-many through `inscribed`, with enrollment date.
- `workout_program` and `trainer` to `routine`: each routine has one required program and one required creator. A routine may also reference one client through nullable `routine.id_client`.
- `routine` to `parameters_routine`: one-to-zero-or-one in the DDL; the shared `id_routine` primary/foreign key prevents more than one parameter row.
- `routine` to `routine_structure`: one-to-zero-or-one in the DDL; `id_routine` is both primary and foreign key. The application design expects the routine and structure to be persisted atomically.
- `routine` to `exercise`: many-to-many through `contains`, which stores order, sets, repetitions, and rest.
- `routine` to `validate`: one-to-many as declared, but creation of `validate` is blocked by its foreign key to the absent `room_chief` table.
- `routine` to `client`: many-to-many through `assignment`; `assignment` has its own identity key and records assignment dates.
- `assignment` to `session`: one-to-many; a session references an assignment, not a client directly. The client is reached through `assignment.id_client`.
- `client`, `routine`, and `trainer` to `request`: each request references one of each.
- `request` to `adjustment_result`: one-to-zero-or-one; `adjustment_result.id_request` is its primary and foreign key.

## 4. Referential actions

The actions below are those explicitly written in the table-creation scripts:

- Script 001: specialization and site references use `ON UPDATE RESTRICT ON DELETE RESTRICT`.
- Script 002: `covers` foreign keys omit an action clause, so PostgreSQL's default `NO ACTION` applies.
- Script 003: exercise, authorization, and enrollment foreign keys use `ON UPDATE RESTRICT ON DELETE RESTRICT`.
- Script 004: routine, parameter, composition, and JSONB-structure foreign keys use `ON UPDATE RESTRICT ON DELETE RESTRICT`.
- Script 005: validation, assignment, session, request, and adjustment-result foreign keys use `ON UPDATE CASCADE ON DELETE RESTRICT`.

No table-creation script defines an `ON DELETE CASCADE` relationship. Historical records are therefore protected from deletion through these references.

## 5. Inline primary, unique, and check constraints

The following constraints are present directly in scripts 001–005:

| Table | Constraint or key | Declared rule |
|---|---|---|
| `site` | `uq_site_name` | Unique site name |
| `site` | `chk_site_name_not_empty` | Trimmed name is not empty |
| `site` | `chk_site_address_not_empty` | Trimmed address is not empty |
| `app_user` | `uq_app_user_email` | Unique email |
| `app_user` | `chk_app_user_name_not_empty` | Trimmed name is not empty |
| `app_user` | `chk_app_user_email_not_empty` | Trimmed email is not empty |
| `app_user` | `chk_app_user_role` | Role is `ADMIN`, `TRAINER`, or `CLIENT` |
| `trainer` | `chk_trainer_specialty_not_empty` | Trimmed specialty is not empty |
| `client` | `chk_client_age` | Age is between 14 and 100 inclusive |
| `muscle_group` | `uq_muscle_group_name`, `chk_muscle_group_name` | Unique, non-empty name |
| `exercise_type` | `uq_exercise_type_name`, `chk_exercise_type_name` | Unique, non-empty name |
| `workout_program` | `uq_workout_program_name`, name/objective checks | Unique name; name and objective are non-empty |
| `covers` | Composite primary key | One row per program/muscle-group pair |
| `authorises` | Composite primary key | One row per trainer/program pair |
| `authorises` | `chk_authorises_dates` | End date is null or not before start date |
| `authorises` | `chk_authorises_at_least_one_permission` | At least one of `can_generate` or `can_validate` is true |
| `inscribed` | Composite primary key | One row per client/program pair |
| `exercise` | `chk_exercise_name_not_empty` | Trimmed exercise name is not empty |
| `parameters_routine` | `chk_parameters_routine_total_exercises` | Total exercises is greater than zero |
| `parameters_routine` | `chk_parameters_routine_intensity_not_empty` | Intensity text is not empty |
| `parameters_routine` | `chk_parameters_routine_ratios` | Cardio and strength ratios are non-negative and sum to at most 100 |
| `contains` | Composite primary key | Unique routine/exercise/order tuple |
| `contains` | `chk_contains_execution_order` | Execution order is positive |
| `contains` | `chk_contains_sets` | Sets is positive |
| `contains` | `chk_contains_repetitions` | Repetitions is positive |
| `contains` | `chk_contains_rest_time` | Rest time is zero or greater |
| `routine` | `chk_routine_status` | Status is one of `DRAFT`, `PENDING_REVIEW`, `APPROVED`, `REJECTED` |
| `routine_structure` | `chk_routine_structure_json_object` | `structure_json` must be a JSON object |
| `validate` | Primary key | `id_validation` |
| `assignment` | Primary key | `id_assignment` |
| `session` | Primary key | `id_session` |
| `request` | Primary key | `id_request` |
| `adjustment_result` | Primary key | `id_request`; also its foreign key to `request` |

The primary-key and foreign-key definitions for every table are also summarized in §3 and expanded in [data-dictionary.md](data-dictionary.md).

## 6. Indexes declared in the table scripts

These explicit secondary indexes are declared in scripts 001, 003, and 004:

| Index | Table and columns | Source |
|---|---|---|
| `idx_client_site` | `client(id_site)` | 001 |
| `idx_exercise_trainer_creator` | `exercise(id_trainer_creator)` | 003 |
| `idx_exercise_muscle_group` | `exercise(id_muscle_group)` | 003 |
| `idx_exercise_type` | `exercise(id_exercise_type)` | 003 |
| `idx_authorises_workout_program` | `authorises(id_workout_program)` | 003 |
| `idx_inscribed_workout_program` | `inscribed(id_workout_program)` | 003 |
| `idx_routine_workout_program` | `routine(id_workout_program)` | 004 |
| `idx_routine_trainer_creator` | `routine(id_trainer_creator)` | 004 |
| `idx_routine_client` | `routine(id_client)` | 004 |
| `idx_contains_exercise` | `contains(id_exercise)` | 004 |

Primary keys and unique constraints also create their supporting unique indexes in PostgreSQL.

### Report-specific indexes

No report-specific index has been added in this documentation task. Add those only after the corresponding report SQL and filters are defined, using representative data and measured query plans (for example, `EXPLAIN (ANALYZE, BUFFERS)`). Do not infer an index solely from a report name.

## 7. Unresolved mismatches in script 006

Script 006 is not aligned with the physical columns and relation names created by scripts 001–005. These are implementation blockers, not silently applied schema facts:

| Statement in script 006 | Physical DDL in 001–005 | Required reconciliation |
|---|---|---|
| `ALTER TABLE "user"` | The table is named `app_user`. | Target the agreed physical table name. |
| `ALTER TABLE intensity_level` | No `intensity_level` table is created. | Decide whether this catalog relation is required or whether intensity remains a routine parameter attribute; then align DDL and documentation. |
| `contains.rest_seconds` | Column is `contains.rest_time_seconds`. | Use the declared column name and agree whether zero seconds is valid; script 004 currently allows zero. |
| `session.intensity_perceived` | Column is `session.intensidad_percibida` (`VARCHAR(30)`). | Align name, type, and permitted range with the requirement before adding a CHECK. |
| `routine.state` | Column is `routine.status`. | Use the declared column name. |
| `routine.intensity_level` | No such column exists on `routine`; the current scalar is `parameters_routine.intensity_level`. | Decide the authoritative location and reference before adding an index. |
| `assignment.end_date`, `assignment.assignment_date` | Columns are `fecha_fin` and `fecha_asignacion`. | Align temporal checks with the declared names. |
| `session.start_time`, `session.end_time`, `session.session_date` | Columns are `hora_inicio`, `hora_fin`, and `fecha_sesion`. | Align temporal checks and indexes with the declared names. |

Additional semantic conflicts:

- Script 006 labels `UNIQUE(exercise.name, id_exercise_type, id_muscle_group)` as U-4. The requirements catalogue identifies the original exercise duplicate rule as U-12: `(exercise name, id_muscle_group)`. These are different uniqueness rules.
- Script 006 labels session uniqueness as `UNIQUE(id_session, id_assignment)`. Since `id_session` is already the primary key, this does not enforce one session per assignment and date. The original rule describes uniqueness on `(id_assignment, fecha_sesion)`.
- Script 006's `uq_routine_structure_routine` is redundant with `routine_structure.id_routine` already being the primary key.
- Script 006's `chk_parameters_counts_positive` permits zero, while script 004's inline constraint requires `total_exercises > 0`.
- Script 006 does not add a validation-before-routine-creation constraint; its `chk_validation_consistency` block is a placeholder containing only `NULL`.
- The script's claimed uniqueness numbering does not match the source requirement numbering U-1 through U-12 in `docs/requirements/informational-requirements.md`.

Because the first statement in 006 targets the absent `user` table, the script cannot complete against the schema created by the preceding scripts as written. Its later statements must not be represented as installed constraints or indexes until the script is reconciled and executed.

## 8. Trigger behavior in script 007

Script 007 declares these trigger mechanisms:

1. `trg_check_trainer_user_role` on `trainer`: verifies that the referenced `app_user.role` is `TRAINER`.
2. `trg_check_client_user_role` on `client`: verifies that the referenced `app_user.role` is `CLIENT`.
3. `trg_sync_routine_status` on `validate`: accepts validation only while a routine is `PENDING_REVIEW`, then changes `routine.status` to `APPROVED` or `REJECTED`.
4. `trg_verify_adjustment_trainer` on `adjustment_result`: verifies that the resolver is the trainer selected by the corresponding `request`.

Script 007 does not define a `room_chief` table. This is important because script 005's `validate.id_room_chief` foreign key references that missing table. Script 007 also does not declare a Redis/cache-invalidation trigger, notwithstanding older environment-document wording.

The current `routine.status` CHECK allows only `DRAFT`, `PENDING_REVIEW`, `APPROVED`, and `REJECTED`; it does not allow `REPLACED`. The lifecycle requirement for a replaced routine therefore needs a schema decision before it can be stored.

## 9. Other physical gaps to keep visible

The following requirement/schema differences are visible when the table DDL is compared with the current requirements catalogue:

- `app_user` has no active/inactive column, although RI-01 calls for account active state.
- There is no physical `room_chief` table. `trainer.specialty` can contain text such as `ROOM_CHIEF`, while authorization capability is represented by `authorises.can_validate`; script 005 still expects a `room_chief` foreign key.
- There is no physical `intensity_level` catalog table. `parameters_routine.intensity_level` is free text.
- `parameters_routine` stores only `cardio_ratio` and `strength_ratio`; it has no flexibility ratio or explicit muscle-group-coverage column.
- `exercise` has no intensity column or foreign key. This follows the script 002 note that intensity is a routine attribute, but the older RI-11 text associates intensity with exercise information.
- `routine` has no source-routine/origin column and its status CHECK has no `REPLACED` value, although the lifecycle requirements describe regeneration lineage.
- Script 002 uses `BIGINT` identity keys for programs and muscle groups, while related identifiers declared in scripts 003 and 004 are `INTEGER`. Confirm and standardize key widths before treating the schema as final.

These gaps are recorded for reconciliation; this documentation issue does not alter SQL or invent new columns.

## 10. Verification and maintenance

### Static review completed for this documentation change

- Compared table declarations and columns in scripts 001–005.
- Compared the 21 original relation names in the project mapping with the current physical table declarations.
- Compared script 006 constraint and index statements with the table/column names declared in scripts 001–005.
- Compared script 007 trigger targets and references with the declared relations.
- Recorded the two original relations that have no independent physical table, the additional JSONB table, and the incompatible statements.

### Live PostgreSQL verification still required

Run these queries against a database initialized from the numbered scripts after the SQL blockers above are resolved:

```sql
-- Physical tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Columns, PostgreSQL types, nullability and defaults
SELECT table_name, ordinal_position, column_name, data_type,
       character_maximum_length, numeric_precision, numeric_scale,
       is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- Primary, foreign, unique and check constraints
SELECT conrelid::regclass AS table_name,
       conname,
       contype,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace
ORDER BY conrelid::regclass::text, conname;

-- Indexes actually present in PostgreSQL
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Triggers actually present in PostgreSQL
SELECT event_object_table AS table_name, trigger_name,
       action_timing, event_manipulation, action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;
```

Record the PostgreSQL version, the exact script sequence used, command output, and any remaining deviations when this live verification is performed. Update these three documents alongside any later approved SQL changes.

## References

- SQL DDL: `backend/database/scripts/001_identity_and_sites.sql` through `005_validation_assignments_sessions_adjustments.sql`.
- Constraint declarations: `backend/database/scripts/006_integrity_constraints.sql`.
- Trigger declarations: `backend/database/scripts/007_consistency_triggers.sql`.
- Requirement catalogue: `docs/requirements/informational-requirements.md`.
- Approved design-relation mapping and project storage decision: [schema-mapping.md](schema-mapping.md).
- Field-level definitions: [data-dictionary.md](data-dictionary.md).
