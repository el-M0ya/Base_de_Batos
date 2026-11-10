# Conceptual-to-physical schema mapping

**Parent epic:** #17 — [E1] Database and SQL Infrastructure  
**Issue:** #29 — E1-11 Document the Physical Schema and Mapping to the Approved Design  
**GitHub Project:** `planificacion`  
**Physical source:** `backend/database/scripts/001_*` through `005_*`  
**Integrity sources:** `backend/database/scripts/006_integrity_constraints.sql` and `007_consistency_triggers.sql`

## 1. Purpose and mapping rules

The approved design identifies 21 original relations. This file maps every one of those relation identifiers to the PostgreSQL implementation currently declared in the repository. The mapping is evidence-based: a physical relation is only marked as implemented as a table when a `CREATE TABLE` statement exists in scripts 001–005.

Three implementation decisions affect the mapping:

- **User specializations:** the current DDL uses `app_user` as the account supertype and `trainer` / `client` as 1:1 specializations. The SQL comments say room-chief is represented as a trainer specialty, not as a separate table.
- **Intensity:** script 002 explicitly says intensity is an attribute of a routine, not a separate catalog. The actual DDL places the value in `parameters_routine.intensity_level`; it does not create an `intensity_level` catalog table or put intensity on `routine`.
- **Variable routine blocks:** the additional `routine_structure` table stores a JSONB document in PostgreSQL, with a one-to-one primary-key/foreign-key relationship to `routine`.

The current scripts are not fully aligned with each other. In particular, script 005 still references `room_chief`, even though scripts 001–004 do not create that table. Script 006 also contains stale table and column names. These are recorded in the mapping; they are not silently treated as resolved.

## 2. Mapping of the 21 original relations

| Original ID | Original design relation | Current physical representation | SQL source | Mapping status and notes |
|---|---|---|---|---|
| R1 | `USER` | `app_user` | 001 | **Mapped with renamed table.** The physical table stores the account identifier, name, email, password hash, role, and registration date. It has no active/inactive column in the current DDL, although RI-01 calls for that state. |
| R2 | `TRAINER` | `trainer` | 001 | **Mapped.** A 1:1 specialization of `app_user`; `id_trainer` is both PK and FK to `app_user.id_user`. Specialty is stored in `specialty`. |
| R3 | `ROOMCHIEF` | No independent table; partially represented by `trainer.specialty` | Comment in 001; reference in 005 | **Not fully mapped.** Script 001 comments that `ROOM_CHIEF` is integrated as a trainer specialty. Script 005 nevertheless declares `validate.id_room_chief` as an FK to `room_chief(id_room_chief)`, a relation that is not created by the checked-in table scripts. The DDL sequence therefore has an unresolved missing referenced table. The `authorises.can_validate` flag separately models validation capability by program; this is not a substitute FK target for `validate.id_room_chief`. |
| R4 | `SITE` | `site` | 001 | **Mapped.** Physical name is unchanged. |
| R5 | `CLIENT` | `client` | 001 | **Mapped.** A 1:1 specialization of `app_user`; includes age and required site FK. |
| R6 | `WORKOUTPROGRAM` | `workout_program` | 002 | **Mapped.** Physical table stores unique name and objective. Its key is `BIGINT`. |
| R7 | `COVERS` | `covers` | 002 | **Mapped.** Associative table between workout programs and muscle groups; composite PK is the pair of FKs. |
| R8 | `MUSCLEGROUP` | `muscle_group` | 002 | **Mapped.** Physical name is singular snake_case. Its key is `BIGINT`. |
| R9 | `EXERCISETYPE` | `exercise_type` | 002 | **Mapped.** Physical name is singular snake_case. Its key is `BIGINT`. |
| R10 | `INTENSITYLEVEL` | No independent catalog table; value stored as `parameters_routine.intensity_level` | Design note in 002; column in 004 | **Not mapped as an independent relation.** Script 002 states that intensity is an attribute of a routine and omits an `intensity_level` table. Script 004 stores a free-text intensity value in `parameters_routine`, not in a referenced catalog and not in `routine` itself. The design relation and the physical implementation differ. |
| R11 | `EXERCISE` | `exercise` | 003 | **Mapped with implementation differences.** The physical row references exercise type, muscle group, and creating trainer. It has no intensity column; script 002's note treats intensity as routine-level. |
| R12 | `AUTHORISES` | `authorises` | 003 | **Mapped.** Composite PK is trainer/program; stores generation and validation flags and a validity period. |
| R13 | `INSCRIBED` | `inscribed` | 003 | **Mapped.** Composite PK is client/program; stores enrollment date. |
| R14 | `ROUTINE` | `routine` | 004 | **Mapped with gaps.** Stores program, creator, optional client, creation date, and status. No source-routine/origin FK is declared; status CHECK does not include `REPLACED`. |
| R15 | `PARAMETERSROUTINE` | `parameters_routine` | 004 | **Mapped with reduced parameter fields.** One row per routine. Stores total count, target intensity, cardio ratio, and strength ratio. No flexibility ratio or separate muscle-group-coverage value is declared. |
| R16 | `CONTAINS` | `contains` | 004 | **Mapped.** Associative routine/exercise table with execution order, sets, repetitions, and rest seconds. Composite PK includes routine, exercise, and execution order. |
| R17 | `VALIDATE` | `validate` | 005 | **Table declared, but FK dependency is unresolved.** Stores routine, room-chief reference, validation date, decision, and observations. Its FK points to the missing `room_chief` table. |
| R18 | `ASSIGNMENT` | `assignment` | 005 | **Mapped.** Assignment has its own identity PK, routine/client FKs, assignment date, and nullable end date. |
| R19 | `SESION` | `session` | 005 | **Mapped with translated column names.** References assignment, not client directly. Stores date, start/end time, perceived intensity text, completion flag, and observations. |
| R20 | `REQUEST` | `request` | 005 | **Mapped with translated column names.** References client, routine, and selected trainer; stores date, reason, and status. |
| R21 | `ADJUSTMENTRESULT` | `adjustment_result` | 005 | **Mapped with translated column names.** `id_request` is both PK and FK; stores response date, adjustment description, resulting routine, and resolving trainer. |

## 3. Additional physical relation: `routine_structure`

`routine_structure` is an additional physical table, not one of the 21 original design relations.

| Attribute | Physical definition |
|---|---|
| Table | `routine_structure` |
| `id_routine` | `INTEGER PRIMARY KEY`, also FK to `routine(id_routine)`; update/delete RESTRICT |
| `structure_json` | `JSONB NOT NULL` |
| Check | `jsonb_typeof(structure_json) = 'object'` |
| Cardinality | At most one structure row per routine; the PK/FK makes it 1:1 |
| Purpose | Stores variable nested block structure, such as warm-ups, circuits, sets, and rests |
| SQL source | `backend/database/scripts/004_routines_and_structure.sql` |

The DDL allows a routine to exist without a corresponding `routine_structure` row; it enforces the direction “every structure belongs to a routine” but does not enforce “every routine has a structure”. The intended application write is atomic across routine and structure, as stated in the script comments and issue #23. Enforce the “exactly one structure per generated routine” rule in the application/transaction or with an explicitly approved database mechanism.

The implementation choice is PostgreSQL JSONB. The requirement to preserve variable nested structure is retained, but the older design proposal for a separate document database is not the current physical implementation.

## 4. Important model-level differences

### 4.1 User and room-chief representation

- Physical table: `app_user`, not `user`.
- Persisted role CHECK values: `ADMIN`, `TRAINER`, `CLIENT`.
- `trainer.specialty` can hold `ROOM_CHIEF` as descriptive specialization according to the script comment.
- `authorises.can_validate` is a trainer/program capability.
- No physical `room_chief` table is created, but `validate.id_room_chief` references it.

The team must decide the single canonical representation for the reviewer FK and align script 005, user role rules, and trigger behavior. Do not claim that the `validate` FK is satisfied by `trainer.specialty`; those are different relation targets.

### 4.2 Intensity representation

- No `intensity_level` table exists in scripts 001–005.
- `parameters_routine.intensity_level` is `VARCHAR(50) NOT NULL`.
- `routine` has no `intensity_level` column.
- `exercise` has no intensity column.
- Script 006 attempts to create an index on `routine.intensity_level`, which is not a declared column.

A normalized intensity catalog would require an approved schema change; this documentation does not invent one.

### 4.3 Generation parameter coverage

`parameters_routine` contains only `cardio_ratio` and `strength_ratio`; the DDL does not store a flexibility ratio or a separate coverage list. Confirm whether the omitted portion is derived (for example, by complement) or whether the schema needs an additional attribute/table before declaring the full parameter requirement satisfied.

### 4.4 Routine lineage and lifecycle

- `routine` has no `id_routine_origin` or equivalent source-routine FK.
- `routine.status` permits only `DRAFT`, `PENDING_REVIEW`, `APPROVED`, `REJECTED`.
- The requirements and State design include replaced/superseded routines and source lineage.
- Script 007 synchronizes status from a validation decision, but does not add a `REPLACED` state or lineage field.

The lifecycle requirements therefore exceed the current physical DDL.

### 4.5 Numeric identifier widths

Script 002 declares `workout_program.id_workout_program` and `muscle_group.id_muscle_group` as `BIGINT`. The referencing columns in scripts 003 and 004 are `INTEGER`. Review and standardize identifier widths for consistency across the schema and repository DTOs.

## 5. Requirements-to-relation traceability

| Data requirement | Original relation(s) | Current physical table(s) or field(s) |
|---|---|---|
| User identity, email, password, role | USER | `app_user` |
| Trainer specialization | TRAINER | `trainer` |
| Room-chief review identity | ROOMCHIEF, VALIDATE | Partly `trainer.specialty`; `validate.id_room_chief` FK currently unresolved |
| Client age and site | CLIENT, SITE | `client`, `site` |
| Program objective | WORKOUTPROGRAM | `workout_program` |
| Program muscle-group coverage | COVERS, WORKOUTPROGRAM, MUSCLEGROUP | `covers`, `workout_program`, `muscle_group` |
| Exercise type catalog | EXERCISETYPE | `exercise_type` |
| Intensity catalog | INTENSITYLEVEL | No catalog; free-text `parameters_routine.intensity_level` |
| Exercise identity, author and classification | EXERCISE | `exercise`, with type/muscle-group FKs and trainer creator |
| Trainer permissions | AUTHORISES | `authorises` |
| Client enrollment | INSCRIBED | `inscribed` |
| Routine provenance and status | ROUTINE | `routine`; no source-routine field and no `REPLACED` status |
| Routine generation parameters | PARAMETERSROUTINE | `parameters_routine`; two ratios only |
| Ordered routine contents | CONTAINS | `contains` |
| Variable nested routine blocks | Additional implementation table | `routine_structure.structure_json` (JSONB) |
| Review/decision history | VALIDATE | `validate`, but missing `room_chief` FK target |
| Client routine assignment | ASSIGNMENT | `assignment` |
| Training session | SESION | `session` |
| Adjustment request | REQUEST | `request` |
| Adjustment result | ADJUSTMENTRESULT | `adjustment_result` |

## 6. Integrity numbering: use the requirement catalogue as the reference

Use the original identifiers in `docs/requirements/informational-requirements.md` when documenting requirements. The current script 006 comments use a shifted/mismatched mapping in several places. The authoritative list in that requirements document defines:

- U-1: unique user email.
- U-2: unique workout-program name.
- U-3: unique names within muscle-group, exercise-type, and intensity-level catalogs.
- U-4: unique client/program enrollment.
- U-5: unique trainer/program authorization pair.
- U-6: unique routine/exercise pair in `contains`.
- U-7: unique routine/execution-order pair in `contains`.
- U-8: one parameter row per routine.
- U-9: unique routine/client assignment.
- U-10: unique assignment/session-date pair.
- U-11: one adjustment result per request.
- U-12: unique exercise name/muscle-group pair.

The physical DDL partially enforces some of these through primary/unique keys. Script 006 does not implement the complete source list accurately. See [schema.md](schema.md) §7 for the statement-by-statement SQL discrepancies.

## 7. Files consulted

The mapping was prepared from the actual contents of:

- `backend/database/scripts/001_identity_and_sites.sql`
- `backend/database/scripts/002_catalogs_and_programs.sql.sql`
- `backend/database/scripts/003_exercises_authorisations_enrolments.sql`
- `backend/database/scripts/004_routines_and_structure.sql`
- `backend/database/scripts/005_validation_assignments_sessions_adjustments.sql`
- `backend/database/scripts/006_integrity_constraints.sql`
- `backend/database/scripts/007_consistency_triggers.sql`
- `docs/requirements/functional-requirements.md`
- `docs/requirements/informational-requirements.md`
- `docs/database/integrity-constraints.md`
- `docs/database/consistency-triggers.md`
- `docs/database/storage-adaptation.md`

For column-level detail, see [data-dictionary.md](data-dictionary.md). For the full physical table and key inventory, see [schema.md](schema.md).
