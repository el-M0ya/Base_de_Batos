-- 008_catalog_seeds.sql
-- PostgreSQL
-- Initial fixed data for the exercise-type catalog.
--
-- Prerequisites:
--   - exercise_type has already been created and has unique names.
--
-- This file intentionally contains catalog values only. Test users, exercises
-- and routines belong in separate fixture/seed files.

BEGIN;

-- Exercise types defined by the approved data model.
INSERT INTO exercise_type (name)
VALUES
    ('fuerza'),
    ('cardio'),
    ('flexibilidad')
ON CONFLICT (name) DO NOTHING;

COMMIT;

-- Verification queries (run manually after executing this script).
-- Expected: 3 rows in the exercise-type catalog.
--
-- SELECT name
-- FROM exercise_type
-- WHERE name IN ('fuerza', 'cardio', 'flexibilidad')
-- ORDER BY name;
--
