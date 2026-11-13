-- -----------------------------------------------------------------------------
-- Persist the complete routine-generation parameters required by R8.
--
-- The original parameters_routine table only stored the cardio and strength
-- percentages. Routine generation also accepts a flexibility proportion and
-- must preserve the muscle groups covered by the program at generation time.
-- New databases receive these columns from this script; existing databases get
-- them through the same idempotent ALTER statements.
-- -----------------------------------------------------------------------------

BEGIN;

ALTER TABLE parameters_routine
    ADD COLUMN IF NOT EXISTS flexibility_ratio NUMERIC(5,2) NOT NULL DEFAULT 0;

ALTER TABLE parameters_routine
    ADD COLUMN IF NOT EXISTS covered_muscle_group_ids INTEGER[] NOT NULL DEFAULT '{}';

-- Replace the old two-ratio check so the three exercise-type proportions are
-- validated together.
ALTER TABLE parameters_routine
    DROP CONSTRAINT IF EXISTS chk_parameters_routine_ratios;

ALTER TABLE parameters_routine
    ADD CONSTRAINT chk_parameters_routine_ratios
    CHECK (
        cardio_ratio >= 0
        AND strength_ratio >= 0
        AND flexibility_ratio >= 0
        AND (cardio_ratio + strength_ratio + flexibility_ratio) <= 100
    );

COMMENT ON COLUMN parameters_routine.flexibility_ratio
    IS 'Percentage of flexibility exercises requested during generation.';

COMMENT ON COLUMN parameters_routine.covered_muscle_group_ids
    IS 'Snapshot of the program muscle groups covered when the routine was generated.';

COMMIT;
