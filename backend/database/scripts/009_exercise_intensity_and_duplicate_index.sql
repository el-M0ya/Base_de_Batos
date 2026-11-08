-- 009_exercise_intensity_and_duplicate_index.sql
-- PostgreSQL
-- Aligns the `exercise` table with the domain model used by E2-04/E2-06:
--
--   1. an exercise has an intensity level (RF-12), so the column and its
--      foreign key are added;
--   2. the duplicate identity is the *normalized* name plus the muscle group
--      (U-12), replacing the previous (name, exercise_type, muscle_group)
--      constraint, which compared raw values.
--
-- The normalization mirrors app.domain.entities.exercise.normalize_exercise_name:
-- lowercase, remove Spanish diacritics and collapse whitespace. The unique
-- index is what the repository relies on when two concurrent requests try to
-- register the same exercise.

BEGIN;

-- 1. Intensity level of the exercise -----------------------------------------

ALTER TABLE exercise
    ADD COLUMN IF NOT EXISTS id_intensity_level INTEGER;

-- Backfill existing rows (if any) before enforcing NOT NULL.
UPDATE exercise e
   SET id_intensity_level = il.id_intensity_level
  FROM intensity_level il
 WHERE e.id_intensity_level IS NULL
   AND il.name = 'medio';

DO
$$
BEGIN
    IF EXISTS (
        SELECT 1 FROM exercise WHERE id_intensity_level IS NULL
    ) THEN
        RAISE EXCEPTION 'Cannot set exercise.id_intensity_level NOT NULL: '
                        'there are exercises without intensity and no "medio" '
                        'intensity level to use as default.';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_exercise_intensity_level'
    ) THEN
        ALTER TABLE exercise
            ALTER COLUMN id_intensity_level SET NOT NULL;

        ALTER TABLE exercise
            ADD CONSTRAINT fk_exercise_intensity_level
            FOREIGN KEY (id_intensity_level)
            REFERENCES intensity_level (id_intensity_level)
            ON UPDATE RESTRICT
            ON DELETE RESTRICT;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_exercise_intensity ON exercise (id_intensity_level);

-- 2. Normalized duplicate identity ------------------------------------------

ALTER TABLE exercise DROP CONSTRAINT IF EXISTS uq_exercise_identity;

CREATE UNIQUE INDEX IF NOT EXISTS uq_exercise_normalized_identity
    ON exercise (
        lower(
            btrim(
                regexp_replace(
                    translate(name, 'áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN'),
                    '\s+',
                    ' ',
                    'g'
                )
            )
        ),
        id_muscle_group
    );

COMMIT;
