-- Add persisted routine replacement lineage and lifecycle status (issue #122).
-- A source routine may have at most one successor. Validation rows are retained.

BEGIN;

ALTER TABLE routine
    ADD COLUMN IF NOT EXISTS id_routine_origin INTEGER;

ALTER TABLE routine
    DROP CONSTRAINT IF EXISTS chk_routine_status;

ALTER TABLE routine
    ADD CONSTRAINT chk_routine_status
    CHECK (status IN ('DRAFT', 'PENDING_REVIEW', 'APPROVED', 'REJECTED', 'REPLACED'));

DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_routine_origin'
    ) THEN
        ALTER TABLE routine
            ADD CONSTRAINT fk_routine_origin
            FOREIGN KEY (id_routine_origin)
            REFERENCES routine (id_routine)
            ON UPDATE RESTRICT
            ON DELETE RESTRICT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_routine_not_own_origin'
    ) THEN
        ALTER TABLE routine
            ADD CONSTRAINT chk_routine_not_own_origin
            CHECK (id_routine_origin IS NULL OR id_routine_origin <> id_routine);
    END IF;
END
$$;

CREATE UNIQUE INDEX IF NOT EXISTS uq_routine_successor_origin
    ON routine (id_routine_origin)
    WHERE id_routine_origin IS NOT NULL;

COMMENT ON COLUMN routine.id_routine_origin IS
    'Source routine replaced by this successor; NULL for an original routine.';
COMMENT ON COLUMN routine.status IS
    'Lifecycle status, including REPLACED for reviewed routines with a successor.';

COMMIT;
