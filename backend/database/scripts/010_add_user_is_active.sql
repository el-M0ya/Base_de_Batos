-- -----------------------------------------------------------------------------
-- Add the account active/inactive state required by RI-01.
--
-- The column is added for databases created before E4-01. New databases already
-- receive it from 001_identity_and_sites.sql, so this script is idempotent.
-- -----------------------------------------------------------------------------

BEGIN;

ALTER TABLE app_user
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

COMMENT ON COLUMN app_user.is_active
    IS 'Whether the account can authenticate and be used (RI-01).';

COMMIT;
