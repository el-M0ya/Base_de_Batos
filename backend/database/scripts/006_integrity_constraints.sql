-- -----------------------------------------------------------------------------
-- This script implements uniqueness constraints U-1 through U-12, domain
-- CHECK constraints, temporal constraints and supporting indexes as defined
-- in the approved design.
--
-- Design notes:
--   - User email must be unique (U-1)
--   - Catalog names and workout program names must be unique (U-2/U-3)
--   - No duplicate exercises (U-4)
--   - No duplicate enrollments (U-5) and no duplicate authorizations (U-6)
--   - No duplicate exercise in the same routine composition (U-7)
--   - No duplicate routine assignment to the same client (U-8)
--   - No duplicate session for the same assignment (U-9)
--   - No duplicate adjustment result for the same request (U-10)
--   - Routine structure is stored as JSONB in routine_structure (issue #23)
--   - Intensity is modeled as an attribute of the routine (updated MERX)
--   - Room Chief is a specific type of trainer that validates and guides
--     routine creation but does NOT create routines directly
-- -----------------------------------------------------------------------------

BEGIN;

-- -----------------------------------------------------------------------------
-- U-1: Unique user email
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'uq_user_email'
  ) THEN
    ALTER TABLE "user"
      ADD CONSTRAINT uq_user_email UNIQUE (email);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-2: Unique catalog names
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_muscle_group_name') THEN
    ALTER TABLE muscle_group ADD CONSTRAINT uq_muscle_group_name UNIQUE (name);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_exercise_type_name') THEN
    ALTER TABLE exercise_type ADD CONSTRAINT uq_exercise_type_name UNIQUE (name);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_intensity_level_name') THEN
    ALTER TABLE intensity_level ADD CONSTRAINT uq_intensity_level_name UNIQUE (name);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_site_name') THEN
    ALTER TABLE site ADD CONSTRAINT uq_site_name UNIQUE (name);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-3: Unique workout program name
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_workout_program_name') THEN
    ALTER TABLE workout_program ADD CONSTRAINT uq_workout_program_name UNIQUE (name);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-4: No duplicate exercises
-- Rationale: prevent registering the same exercise with identical identity
--           by name and classification context
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_exercise_identity') THEN
    ALTER TABLE exercise
      ADD CONSTRAINT uq_exercise_identity UNIQUE (name, id_exercise_type, id_muscle_group, id_intensity_level);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-5: No duplicate enrollments
-- Handled by composite PK (id_client, id_workout_program) on inscribed
-- Add explicit uniqueness guard if needed in future, PK is sufficient
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- U-6: No duplicate authorizations
-- Handled by composite PK (id_trainer, id_workout_program) on authorises
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- U-7: No duplicate exercise in the same routine composition
-- One exercise cannot appear twice in CONTAINS for the same routine
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_contains_routine_exercise') THEN
    ALTER TABLE contains
      ADD CONSTRAINT uq_contains_routine_exercise UNIQUE (id_routine, id_exercise);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-8: No duplicate routine assignment to the same client
-- Prevent assigning the same routine twice to the same client
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_assignment_routine_client') THEN
    ALTER TABLE assignment
      ADD CONSTRAINT uq_assignment_routine_client UNIQUE (id_routine, id_client);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-9: No duplicate session for the same assignment
-- A session is tied to a specific assignment; enforce uniqueness of session identity
-- per assignment context as per design
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_session_assignment') THEN
    ALTER TABLE session
      ADD CONSTRAINT uq_session_assignment UNIQUE (id_session, id_assignment);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-10: No duplicate adjustment result for the same request
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_adjustment_result_request') THEN
    ALTER TABLE adjustment_result
      ADD CONSTRAINT uq_adjustment_result_request UNIQUE (id_request);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- U-11/U-12: Additional business uniqueness guards
-- Ensure routine structure integrity when present (JSONB model)
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_routine_structure_routine') THEN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'routine_structure') THEN
      ALTER TABLE routine_structure
        ADD CONSTRAINT uq_routine_structure_routine UNIQUE (id_routine);
    END IF;
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- Domain CHECK constraints
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
  -- Client age > 0
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_client_age_positive') THEN
    ALTER TABLE client ADD CONSTRAINT chk_client_age_positive CHECK (age > 0);
  END IF;

  -- Routine composition: sets, repetitions and rest must be > 0
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_contains_sets_positive') THEN
    ALTER TABLE contains ADD CONSTRAINT chk_contains_sets_positive CHECK (sets > 0);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_contains_repetitions_positive') THEN
    ALTER TABLE contains ADD CONSTRAINT chk_contains_repetitions_positive CHECK (repetitions > 0);
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_contains_rest_positive') THEN
    ALTER TABLE contains ADD CONSTRAINT chk_contains_rest_positive CHECK (rest_seconds > 0);
  END IF;

  -- Parameters routine: proportions and counts must be >= 0 where applicable
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_parameters_counts_positive') THEN
    ALTER TABLE parameters_routine ADD CONSTRAINT chk_parameters_counts_positive CHECK (total_exercises >= 0);
  END IF;

  -- Authorization permissions
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_authorises_at_least_one_permission') THEN
    ALTER TABLE authorises ADD CONSTRAINT chk_authorises_at_least_one_permission CHECK (can_generate = TRUE OR can_validate = TRUE);
  END IF;

  -- Session completed flag logic aid
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_intensity_perceived_range') THEN
    ALTER TABLE session ADD CONSTRAINT chk_session_intensity_perceived_range CHECK (intensity_perceived BETWEEN 1 AND 10);
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- Temporal constraints
-- -----------------------------------------------------------------------------
DO
$$
BEGIN
-- Assignment: end_date >= assignment_date if present
IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_assignment_dates') THEN
    ALTER TABLE assignment ADD CONSTRAINT chk_assignment_dates CHECK (end_date IS NULL OR end_date >= assignment_date);
  END IF;

  -- Authorization: end_date >= start_date if present
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_authorises_dates_range') THEN
    ALTER TABLE authorises ADD CONSTRAINT chk_authorises_dates_range CHECK (end_date IS NULL OR end_date >= start_date);
  END IF;

  -- Session: end_time >= start_time
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_time_range') THEN
    ALTER TABLE session ADD CONSTRAINT chk_session_time_range CHECK (end_time >= start_time);
  END IF;

  -- Validation: routine must not be validated before creation (business rule)
  -- Enforced where possible; complex cases may require triggers/use-case validation
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_validation_consistency') THEN
    -- Placeholder for future temporal validation; documented in integrity-constraints.md
    NULL;
  END IF;
END
$$;

-- -----------------------------------------------------------------------------
-- Supporting indexes for constraint-related lookups
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_routine_state ON routine (state);
CREATE INDEX IF NOT EXISTS idx_routine_intensity ON routine (intensity_level);
CREATE INDEX IF NOT EXISTS idx_assignment_client_routine ON assignment (id_client, id_routine);
CREATE INDEX IF NOT EXISTS idx_session_assignment_date ON session (id_assignment, session_date);

COMMIT;

-- End of script