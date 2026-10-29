import {
  SEED_EXERCISES,
  SEED_EXERCISE_TYPES,
  SEED_INTENSITY_LEVELS,
  SEED_MUSCLE_GROUPS,
  SEED_USERS,
  type SeedExercise,
  type SeedExerciseType,
  type SeedIntensityLevel,
  type SeedMuscleGroup,
  type SeedUser,
} from './seed';

/**
 * In-memory database backing the mock API implementation.
 */
export class MockDatabase {
  private users: SeedUser[] = [...SEED_USERS];
  private muscleGroups: SeedMuscleGroup[] = [...SEED_MUSCLE_GROUPS];
  private exerciseTypes: SeedExerciseType[] = [...SEED_EXERCISE_TYPES];
  private intensityLevels: SeedIntensityLevel[] = [...SEED_INTENSITY_LEVELS];
  private exercises: SeedExercise[] = SEED_EXERCISES.map((exercise) => ({ ...exercise }));

  /** Returns all demo users. */
  getUsers(): SeedUser[] {
    return this.users.map((user) => ({ ...user }));
  }

  /** Finds a user by email. */
  findUserByEmail(email: string): SeedUser | undefined {
    const user = this.users.find((item) => item.email.toLowerCase() === email.toLowerCase());
    return user ? { ...user } : undefined;
  }

  /** Returns all muscle groups. */
  getMuscleGroups(): SeedMuscleGroup[] {
    return this.muscleGroups.map((item) => ({ ...item }));
  }

  /** Returns all exercise types. */
  getExerciseTypes(): SeedExerciseType[] {
    return this.exerciseTypes.map((item) => ({ ...item }));
  }

  /** Returns all intensity levels. */
  getIntensityLevels(): SeedIntensityLevel[] {
    return this.intensityLevels.map((item) => ({ ...item }));
  }

  /** Returns all exercises. */
  getExercises(): SeedExercise[] {
    return this.exercises.map((item) => ({ ...item }));
  }

  /** Finds an exercise by id. */
  findExerciseById(id: string): SeedExercise | undefined {
    const exercise = this.exercises.find((item) => item.id === id);
    return exercise ? { ...exercise } : undefined;
  }

  /** Finds an exercise by name and muscle group (duplicate check). */
  findExerciseByNameAndMuscleGroup(name: string, muscleGroupId: string): SeedExercise | undefined {
    const exercise = this.exercises.find(
      (item) => item.name.toLowerCase() === name.toLowerCase() && item.muscleGroupId === muscleGroupId,
    );
    return exercise ? { ...exercise } : undefined;
  }

  /** Inserts an exercise, returning the created record. */
  insertExercise(input: Omit<SeedExercise, 'id' | 'createdAt'>): SeedExercise {
    const exercise: SeedExercise = {
      ...input,
      id: `ex-${this.exercises.length + 1}`,
      createdAt: new Date().toISOString(),
    };
    this.exercises.push(exercise);
    return { ...exercise };
  }
}

/**
 * Shared mock database instance.
 */
export const mockDatabase = new MockDatabase();