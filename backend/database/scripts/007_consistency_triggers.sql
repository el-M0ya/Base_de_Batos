-- -----------------------------------------------------------------------------
-- This script creates the triggers and PL/pgSQL functions for Module 7:
-- Consistency Triggers (Épica 1 / Issue E1-08)
--
-- Functions & Triggers created:
--   1. trg_check_trainer_user_role / check_trainer_user_role()
--      - Guarantees that a user added to 'trainer' has role = 'TRAINER' in 'app_user'.
--   2. trg_check_client_user_role / check_client_user_role()
--      - Guarantees that a user added to 'client' has role = 'CLIENT' in 'app_user'.
--   3. trg_sync_routine_status / sync_routine_status_on_validation()
--      - Enforces that only routines in 'PENDING_REVIEW' state can be validated.
--      - Automatically syncs routine.status to 'APPROVED' or 'REJECTED' based on validation decision.
--   4. trg_verify_adjustment_trainer / verify_adjustment_trainer_match()
--      - Guarantees that the trainer resolving an adjustment in 'adjustment_result'
--        matches the trainer assigned in the original 'request'.
--
-- Design notes:
--   - Executed within an atomic transaction block (BEGIN; ... COMMIT;).
--   - Uses RAISE EXCEPTION with detailed error messages for invalid operations.
--   - Uses DROP TRIGGER IF EXISTS / CREATE OR REPLACE FUNCTION for idempotency.
-- -----------------------------------------------------------------------------

BEGIN;

-- =============================================================================
-- 1. USER ROLE & SPECIALIZATION CONSISTENCY TRIGGERS
-- =============================================================================

-- Function: Check trainer user role
CREATE OR REPLACE FUNCTION check_trainer_user_role()
RETURNS TRIGGER AS $$
DECLARE
    v_role VARCHAR(20);
BEGIN
    SELECT role INTO v_role
    FROM app_user
    WHERE id_user = NEW.id_trainer;

    IF v_role IS NULL THEN
        RAISE EXCEPTION 'Cannot insert/update trainer: User ID % does not exist in app_user.', NEW.id_trainer;
    ELSIF v_role <> 'TRAINER' THEN
        RAISE EXCEPTION 'Consistency Error: User ID % has role ''%'' in app_user, but must be ''TRAINER'' to be added to trainer table.', NEW.id_trainer, v_role;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_trainer_user_role() IS 'Verifies that a user referenced in trainer has role = TRAINER in app_user.';

DROP TRIGGER IF EXISTS trg_check_trainer_user_role ON trainer;
CREATE TRIGGER trg_check_trainer_user_role
    BEFORE INSERT OR UPDATE ON trainer
    FOR EACH ROW
    EXECUTE FUNCTION check_trainer_user_role();


-- Function: Check client user role
CREATE OR REPLACE FUNCTION check_client_user_role()
RETURNS TRIGGER AS $$
DECLARE
    v_role VARCHAR(20);
BEGIN
    SELECT role INTO v_role
    FROM app_user
    WHERE id_user = NEW.id_client;

    IF v_role IS NULL THEN
        RAISE EXCEPTION 'Cannot insert/update client: User ID % does not exist in app_user.', NEW.id_client;
    ELSIF v_role <> 'CLIENT' THEN
        RAISE EXCEPTION 'Consistency Error: User ID % has role ''%'' in app_user, but must be ''CLIENT'' to be added to client table.', NEW.id_client, v_role;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_client_user_role() IS 'Verifies that a user referenced in client has role = CLIENT in app_user.';

DROP TRIGGER IF EXISTS trg_check_client_user_role ON client;
CREATE TRIGGER trg_check_client_user_role
    BEFORE INSERT OR UPDATE ON client
    FOR EACH ROW
    EXECUTE FUNCTION check_client_user_role();


-- =============================================================================
-- 2. ROUTINE LIFECYCLE & VALIDATION CONSISTENCY TRIGGER
-- =============================================================================

-- Function: Sync routine status on validation
CREATE OR REPLACE FUNCTION sync_routine_status_on_validation()
RETURNS TRIGGER AS $$
DECLARE
    v_current_status VARCHAR(30);
BEGIN
    -- Check current routine status
    SELECT status INTO v_current_status
    FROM routine
    WHERE id_routine = NEW.id_routine;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Cannot validate routine: Routine ID % does not exist.', NEW.id_routine;
    ELSIF v_current_status <> 'PENDING_REVIEW' THEN
        RAISE EXCEPTION 'Consistency Error: Routine ID % is in status ''%'', but only routines in ''PENDING_REVIEW'' can be validated.', NEW.id_routine, v_current_status;
    END IF;

    -- Update routine status according to validation decision ('APPROVED' or 'REJECTED')
    IF NEW.decision IN ('APPROVED', 'REJECTED') THEN
        UPDATE routine
        SET status = NEW.decision
        WHERE id_routine = NEW.id_routine;
    ELSE
        RAISE EXCEPTION 'Consistency Error: Invalid validation decision ''%''. Expected APPROVED or REJECTED.', NEW.decision;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sync_routine_status_on_validation() IS 'Ensures routine is PENDING_REVIEW before validation and updates routine.status to APPROVED or REJECTED.';

DROP TRIGGER IF EXISTS trg_sync_routine_status ON validate;
CREATE TRIGGER trg_sync_routine_status
    BEFORE INSERT OR UPDATE ON validate
    FOR EACH ROW
    EXECUTE FUNCTION sync_routine_status_on_validation();


-- =============================================================================
-- 3. ADJUSTMENT REQUEST & RESOLUTION TRAINER MATCH TRIGGER
-- =============================================================================

-- Function: Verify adjustment trainer match
CREATE OR REPLACE FUNCTION verify_adjustment_trainer_match()
RETURNS TRIGGER AS $$
DECLARE
    v_assigned_trainer INTEGER;
BEGIN
    -- Retrieve assigned trainer from request table
    SELECT id_trainer INTO v_assigned_trainer
    FROM request
    WHERE id_request = NEW.id_request;

    IF v_assigned_trainer IS NULL THEN
        RAISE EXCEPTION 'Cannot record adjustment result: Request ID % does not exist.', NEW.id_request;
    ELSIF v_assigned_trainer <> NEW.id_trainer THEN
        RAISE EXCEPTION 'Consistency Error: Trainer ID % resolving the adjustment does not match Trainer ID % assigned to request %.', NEW.id_trainer, v_assigned_trainer, NEW.id_request;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verify_adjustment_trainer_match() IS 'Ensures the trainer resolving an adjustment matches the trainer assigned in the request.';

DROP TRIGGER IF EXISTS trg_verify_adjustment_trainer ON adjustment_result;
CREATE TRIGGER trg_verify_adjustment_trainer
    BEFORE INSERT OR UPDATE ON adjustment_result
    FOR EACH ROW
    EXECUTE FUNCTION verify_adjustment_trainer_match();

COMMIT;
