/**
 * Seed data used by the in-browser mock API.
 */

/** Demo user seed. */
export interface SeedUser {
  id: string;
  email: string;
  password: string;
  name: string;
  role: 'administrador' | 'entrenador' | 'jefe_sala' | 'cliente';
}

/** Muscle group seed. */
export interface SeedMuscleGroup {
  id: string;
  name: string;
}

/** Exercise type seed. */
export interface SeedExerciseType {
  id: string;
  name: string;
}

/** Intensity level seed. */
export interface SeedIntensityLevel {
  id: string;
  name: string;
  level: number;
}

/** Exercise seed. */
export interface SeedExercise {
  id: string;
  name: string;
  description: string;
  muscleGroupId: string;
  typeId: string;
  intensityId: string;
  createdAt: string;
}

/** Demo users, one per role. */
export const SEED_USERS: SeedUser[] = [
  { id: 'u-admin', email: 'admin@gym.local', password: 'admin123', name: 'Administrador Demo', role: 'administrador' },
  { id: 'u-trainer', email: 'entrenador@gym.local', password: 'entrenador123', name: 'Entrenador Demo', role: 'entrenador' },
  { id: 'u-chief', email: 'jefe@gym.local', password: 'jefe123', name: 'Jefe de Sala Demo', role: 'jefe_sala' },
  { id: 'u-client', email: 'cliente@gym.local', password: 'cliente123', name: 'Cliente Demo', role: 'cliente' },
];

/** Muscle groups. */
export const SEED_MUSCLE_GROUPS: SeedMuscleGroup[] = [
  { id: 'mg-chest', name: 'Pecho' },
  { id: 'mg-back', name: 'Espalda' },
  { id: 'mg-legs', name: 'Piernas' },
  { id: 'mg-shoulders', name: 'Hombros' },
  { id: 'mg-arms', name: 'Brazos' },
  { id: 'mg-core', name: 'Core' },
];

/** Exercise types. */
export const SEED_EXERCISE_TYPES: SeedExerciseType[] = [
  { id: 'et-strength', name: 'Fuerza' },
  { id: 'et-cardio', name: 'Cardio' },
  { id: 'et-mobility', name: 'Movilidad' },
  { id: 'et-hiit', name: 'HIIT' },
];

/** Intensity levels. */
export const SEED_INTENSITY_LEVELS: SeedIntensityLevel[] = [
  { id: 'il-low', name: 'Baja', level: 1 },
  { id: 'il-medium', name: 'Media', level: 2 },
  { id: 'il-high', name: 'Alta', level: 3 },
  { id: 'il-extreme', name: 'Extrema', level: 4 },
];

/** Seed exercises. */
export const SEED_EXERCISES: SeedExercise[] = [
  {
    id: 'ex-1',
    name: 'Press de banca',
    description: 'Empuje horizontal con barra.',
    muscleGroupId: 'mg-chest',
    typeId: 'et-strength',
    intensityId: 'il-high',
    createdAt: '2026-01-10T10:00:00.000Z',
  },
  {
    id: 'ex-2',
    name: 'Sentadilla',
    description: 'Flexión de rodillas con barra.',
    muscleGroupId: 'mg-legs',
    typeId: 'et-strength',
    intensityId: 'il-high',
    createdAt: '2026-01-11T10:00:00.000Z',
  },
  {
    id: 'ex-3',
    name: 'Remo con barra',
    description: 'Tracción horizontal.',
    muscleGroupId: 'mg-back',
    typeId: 'et-strength',
    intensityId: 'il-medium',
    createdAt: '2026-01-12T10:00:00.000Z',
  },
  {
    id: 'ex-4',
    name: 'Plancha',
    description: 'Isométrico de core.',
    muscleGroupId: 'mg-core',
    typeId: 'et-mobility',
    intensityId: 'il-low',
    createdAt: '2026-01-13T10:00:00.000Z',
  },
];