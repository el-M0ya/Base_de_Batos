# Integrity, Uniqueness, and Domain Constraints

**Issue:** #25  
**Parent Epic:** #17 - Database and SQL Infrastructure  
**Script:** `backend/database/scripts/006_integrity_constraints.sql`

## Purpose

This document details all integrity constraints implemented by `006_integrity_constraints.sql`, including uniqueness rules (U-1 through U-12), domain CHECK constraints, temporal constraints, and rules that must be enforced by application logic/use cases due to cross-entity complexity.

## Design Alignment

- **Routine structure:** Stored as **JSONB** in `routine_structure` (one-to-one with `routine`), saved in a single transaction with the routine as per **issue #23**.
- **Normalization:** Constraints are applied to keep the relational model in line with 3NF.
- **Referential Integrity:** Maintained via FOREIGN KEYs defined in previous scripts.

## Uniqueness Constraints (U-1 to U-12)

| ID | Target | Constraint | Notes |
|---|---|---|---|
| U-1 | `user.email` | `UNIQUE` | Prevents duplicate user accounts. |
| U-2 | `muscle_group.name`, `exercise_type.name`, `intensity_level.name`, `site.name` | `UNIQUE` | Ensures catalog consistency. |
| U-3 | `workout_program.name` | `UNIQUE` | Prevents duplicate training programs. |
| U-4 | `exercise` (name, exercise_type, muscle_group, intensity_level) | `UNIQUE` | Prevents duplicate exercises in the catalog. |
| U-5 | `inscribed` (id_client, id_workout_program) | `PRIMARY KEY` | Prevents duplicate client enrollments in the same program. |
| U-6 | `authorises` (id_trainer, id_workout_program) | `PRIMARY KEY` | Prevents duplicate trainer authorizations for the same program. |
| U-7 | `contains` (id_routine, id_exercise) | `UNIQUE` | Prevents adding the same exercise twice to the same routine composition. |
| U-8 | `assignment` (id_routine, id_client) | `UNIQUE` | Prevents assigning the same routine twice to the same client. |
| U-9 | `session` (id_session, id_assignment) | `UNIQUE` | Prevents duplicate sessions for the same assignment. |
| U-10 | `adjustment_result` (id_request) | `UNIQUE` | One adjustment result per request. |
| U-11 | `routine_structure` (id_routine) | `UNIQUE` | One JSONB structure per routine (one-to-one). |
| U-12 | Reserved for design-level uniqueness | Documented/covered | See business rules below. |

## Domain CHECK Constraints

| Table | Constraint | Rule |
|---|---|---|
| `client` | `chk_client_age_positive` | `age > 0` |
| `contains` | `chk_contains_sets_positive` | `sets > 0` |
| `contains` | `chk_contains_repetitions_positive` | `repetitions > 0` |
| `contains` | `chk_contains_rest_positive` | `rest_seconds > 0` |
| `parameters_routine` | `chk_parameters_counts_positive` | `total_exercises >= 0` |
| `authorises` | `chk_authorises_at_least_one_permission` | `can_generate = TRUE OR can_validate = TRUE` |
| `session` | `chk_session_intensity_perceived_range` | `intensity_perceived BETWEEN 1 AND 10` |

## Temporal Constraints

| Table | Constraint | Rule |
|---|---|---|
| `assignment` | `chk_assignment_dates` | `end_date IS NULL OR end_date >= assignment_date` |
| `authorises` | `chk_authorises_dates_range` | `end_date IS NULL OR end_date >= start_date` |
| `session` | `chk_session_time_range` | `end_time >= start_time` |

## Rules Requiring Use-Case / Trigger Validation

The following rules cannot be fully enforced by simple CHECKs or UNIQUE constraints and must be validated by triggers or application logic:

| Rule | Rationale | Suggested Enforcement |
|---|---|---|
| **Room Chief restrictions** | Room Chief is a specific trainer type that **validates routines and guides their creation, but does not create routines directly**. | Trigger on `routine`/`exercise`: reject `INSERT/UPDATE` that sets `id_trainer_creator` to a Room Chief. Enforce via role checks. |
| **Trainer authorization validity** | A trainer can only generate/validate routines if they have an active, non-expired entry in `authorises` for that `workout_program`. | Triggers on `routine` creation/validation and `validate` table. |
| **Routine validation flow** | Only authorized trainers with `can_validate = TRUE` can validate routines. Room Chief is allowed to validate but not create. | Trigger `BEFORE INSERT/UPDATE` on `validate` cross-checking `authorises` and `user.role`. |
| **Muscle group coverage** | Routines must satisfy the required muscle group coverage for the target program. | Use-case validation or trigger comparing `contains` against program requirements. |
| **Session consistency** | A session can only be logged for an active assignment and must respect temporal coherence. | Trigger on `session` enforcing assignment state and dates. |
| **Adjustment flow** | An adjustment result must reference an existing request and be issued by a valid resolver in line with permissions. | Trigger on `adjustment_result` validating `request`, `trainer` role and authorization. |
| **Routine origin/history** | `routine.id_routine_origin` and generation history must remain consistent. | Trigger to prevent invalid self-references and invalid history chains. |
| **Cache invalidation** | Changes to routine state must invalidate the active routine cache (Redis). | Trigger on `routine` state changes (documented here; implementation in `007_consistency_triggers.sql`). |

## Verification

```sql
-- Check applied constraints
SELECT conname, contype
FROM pg_constraint
WHERE conrelid IN (
  'user'::regclass,'client'::regclass,'trainer'::regclass,'room_chief'::regclass,'site'::regclass,
  'workout_program'::regclass,'muscle_group'::regclass,'exercise_type'::regclass,'intensity_level'::regclass,
  'exercise'::regclass,'authorises'::regclass,'inscribed'::regclass,
  'routine'::regclass,'parameters_routine'::regclass,'contains'::regclass,'routine_structure'::regclass,
  'validate'::regclass,'assignment'::regclass,'session'::regclass,'request'::regclass,'adjustment_result'::regclass
)
ORDER BY conrelid, conname;

-- Check unique indexes
SELECT indexname, tablename
FROM pg_indexes
WHERE indexname LIKE 'uq_%' OR indexname LIKE 'idx_%'
ORDER BY tablename, indexname;