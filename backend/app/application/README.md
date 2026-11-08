# Application layer

This layer answers *what the system does* for each user request. It orchestrates
domain entities and repository contracts; it does not know about HTTP, FastAPI,
PostgreSQL or psycopg.

```
app/application/
├─ exceptions.py     # ApplicationError and its five concrete errors
├─ dto/              # immutable input/output objects
├─ ports/            # guide for ports (contracts live in app/domain/repositories)
└─ use_cases/        # one class per use case, with a public execute()
```

## Conventions

1. **Errors.** Use the errors in `exceptions.py`: `ResourceNotFound`,
   `DuplicateResource`, `BusinessRuleViolation`, `PermissionDenied` and
   `InvalidInput`. Domain errors are translated to `InvalidInput` at the
   use-case boundary, so callers never depend on the domain hierarchy.
2. **DTOs are immutable.** They are `@dataclass(frozen=True)`; collections are
   tuples. Use cases never mutate their input and always return a new DTO.
3. **The actor is a DTO.** `ActorDTO(id_user, role)` carries the authenticated
   user and the role used for authorization. The layer never imports a framework
   request object.
4. **One class per use case, with an async `execute()`.** Dependencies arrive
   through the constructor (dependency injection); there are no module-level
   singletons and no imports of concrete adapters. `execute` is a coroutine so
   the persistence adapters can use the async psycopg pool of E2-05.
5. **No FastAPI or psycopg imports.** The layer depends on `app.domain` only.

## Example

```python
from app.application.dto.actor import ActorDTO
from app.application.dto.exercise_dto import CreateExerciseInputDTO
from app.application.use_cases.create_exercise import CreateExerciseUseCase
from app.domain.repositories.catalog_repository import CatalogRepository
from app.domain.repositories.exercise_repository import ExerciseRepository

use_case = CreateExerciseUseCase(
    exercise_repository=exercise_repository,   # any ExerciseRepository implementation
    catalog_repository=catalog_repository,     # any CatalogRepository implementation
)

output = await use_case.execute(
    CreateExerciseInputDTO(
        actor=ActorDTO(id_user=7, role="TRAINER"),
        name="Press de banca",
        exercise_type="strength",
        intensity="high",
        muscle_group_id=1,
    )
)
print(output.id_exercise, output.muscle_group_name)
```

The same use case runs unchanged against the in-memory repositories used by the
unit tests and against the PostgreSQL adapters of the infrastructure layer.

## Implemented use cases

| Use case | Rule |
|---|---|
| `CreateExerciseUseCase` | Only trainers create exercises; validates the muscle group; rejects duplicates by normalized name + muscle group |
| `ListExercisesUseCase` | Every authenticated role; filters by muscle group, type and intensity, with ordering |
| `ListExerciseCatalogsUseCase` | Returns muscle groups, exercise types and intensity levels |
