# Domain Glossary

This glossary defines the shared vocabulary for the automatic training-plan generation system. Use these terms consistently in requirements, code, API contracts, and tests.

| Term | Definition |
|---|---|
| User | An authenticated person interacting with the system; a user may hold one or more domain roles. |
| Trainer | A user who prepares, reviews, adjusts, and assigns training programs to clients. |
| Gym manager | A user responsible for gym-level configuration, staff coordination, and oversight of training services. |
| Client | A person for whom a training program or routine is prepared and assigned. |
| Location | A gym, branch, or other place where a client performs a training session. |
| Training program | A planned set of routines and scheduling information intended to guide training over a period. |
| Exercise | A reusable description of a physical activity and its relevant prescription details. |
| Routine | An ordered set of exercises with prescription data such as sets, repetitions, duration, rest, and notes. |
| Generation parameters | Inputs and constraints used to request a generated program, such as goal, experience, available equipment, schedule, and limitations. |
| Assignment | Association of an approved training program with a client, optionally including an effective date and schedule. |
| Session | A scheduled or recorded occurrence of a client performing part of an assigned program. |
| Adjustment request | A request to change a generated or assigned routine, including a reason and requested changes. |

## Actor responsibilities

- **Client:** consult assigned programs, view routines and schedules, record or review sessions where supported, and submit adjustment requests.
- **Trainer:** provide or review generation parameters, request generation, inspect results, manually adjust routines, return a proposal for correction, approve a suitable program, and assign it to a client.
- **Gym manager:** manage gym-level operations and oversee trainer/client relationships according to application permissions.
- **System:** validate inputs, generate a proposal, preserve lifecycle state, and enforce authorization and persistence rules.

## Lifecycle vocabulary

Generated content is a proposal until a trainer reviews it. The trainer may review, approve, return it for correction, or manually adjust it before approval. Assignment makes an approved program available to the selected client. Generation is not approval.

## Usage rules

1. Use **training program** for the broader plan and **routine** for an ordered set of exercises within it.
2. Use **generation parameters** for inputs, not for the generated result.
3. Keep role names independent from implementation details such as frontend components or database tables.
