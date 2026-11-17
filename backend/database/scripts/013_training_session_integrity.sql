-- Session uniqueness and date rules for issue #129.
-- The assignment remains the sole source of the client identity.

BEGIN;

ALTER TABLE session
    DROP CONSTRAINT IF EXISTS uq_session_assignment_date;

ALTER TABLE session
    ADD CONSTRAINT uq_session_assignment_date
    UNIQUE (id_assignment, fecha_sesion);

CREATE OR REPLACE FUNCTION enforce_session_not_before_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    assignment_start DATE;
BEGIN
    SELECT fecha_asignacion
      INTO assignment_start
      FROM assignment
     WHERE id_assignment = NEW.id_assignment;

    IF assignment_start IS NULL THEN
        RAISE EXCEPTION 'Assignment % does not exist', NEW.id_assignment
            USING ERRCODE = '23503';
    END IF;

    IF NEW.fecha_sesion < assignment_start THEN
        RAISE EXCEPTION 'Session date cannot precede assignment date'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_session_not_before_assignment ON session;
CREATE TRIGGER trg_session_not_before_assignment
    BEFORE INSERT OR UPDATE OF id_assignment, fecha_sesion ON session
    FOR EACH ROW
    EXECUTE FUNCTION enforce_session_not_before_assignment();

COMMENT ON COLUMN session.completada IS
    'Completion flag for the entire training session.';

COMMIT;
