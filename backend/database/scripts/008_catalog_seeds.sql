-- 008_catalog_seeds.sql
-- PostgreSQL
-- Initial fixed data for the exercise-type and intensity-level catalogs.
--
-- Prerequisites:
--   - exercise_type and intensity_level have already been created.
--   - Each catalog has a UNIQUE constraint on its "name" column.
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

-- Intensity levels defined by the approved data model.
INSERT INTO intensity_level (name)
VALUES
    ('bajo'),
    ('medio'),
    ('alto')
ON CONFLICT (name) DO NOTHING;

COMMIT;

-- Verification queries (run manually after executing this script).
-- Expected: 3 rows for each catalog, with the values listed above.
--
-- SELECT name
-- FROM exercise_type
-- WHERE name IN ('fuerza', 'cardio', 'flexibilidad')
-- ORDER BY name;
--
-- SELECT name
-- FROM intensity_level
-- WHERE name IN ('bajo', 'medio', 'alto')
-- ORDER BY name;
