# Informational Requirements, Reports, and Database Integrity

## Source and identifier policy

The authoritative informational requirement IDs are **RI-01 through RI-35**, as defined in the team's Database Design Report, Section 2.3, printed pages 9–12. They are preserved exactly and describe data that the database must store or provide. The six original report requests under “Funcionalidades” are tracked separately as **REP-01 through REP-06**, retaining source item numbers 1–6. Database integrity rules are also captured below using the source's exact identifiers (U-1 through U-12 and R1 through R13) or clearly marked project tracking IDs where the source supplies no identifier.

**Primary source (S3):** *Informe — Diseño de la Base de Datos: Gestión para la generación automática de planes de entrenamiento*, Sections 2.3, 4.2–4.8, printed pp. 9–12 and 18–24. **S1:** original problem statement. **S2:** Database II methodological guidance.

## Informational requirements (RI-01 through RI-35)

### RI-01
Store each user's unique identifier, name, email, password, role, and active/inactive state.

**Supporting schema relations in the source report:** USER. **Test identifier:** TC-RI-01.

### RI-02
Store each trainer's specialty.

**Supporting schema relations in the source report:** TRAINER. **Test identifier:** TC-RI-02.

### RI-03
Store each client's age and assigned site.

**Supporting schema relations in the source report:** CLIENT, SITE. **Test identifier:** TC-RI-03.

### RI-04
Store each gym site's identifier and name.

**Supporting schema relations in the source report:** SITE. **Test identifier:** TC-RI-04.

### RI-05
Store each training program's unique identifier, name, and objective.

**Supporting schema relations in the source report:** WORKOUT PROGRAM. **Test identifier:** TC-RI-05.

### RI-06
Store the muscle groups each training program must cover during its cycle.

**Supporting schema relations in the source report:** COVERS, WORKOUT PROGRAM, MUSCLE GROUP. **Test identifier:** TC-RI-06.

### RI-07
Store the domain catalog of muscle groups.

**Supporting schema relations in the source report:** MUSCLE GROUP. **Test identifier:** TC-RI-07.

### RI-08
Store the exercise-type catalog (strength, cardio, flexibility).

**Supporting schema relations in the source report:** EXERCISE TYPE. **Test identifier:** TC-RI-08.

### RI-09
Store the intensity-level catalog (low, medium, high).

**Supporting schema relations in the source report:** INTENSITY LEVEL. **Test identifier:** TC-RI-09.

### RI-10
Store each exercise's identifier, name, description, and registration date.

**Supporting schema relations in the source report:** EXERCISE. **Test identifier:** TC-RI-10.

### RI-11
Store each exercise's type, intensity level, and muscle group.

**Supporting schema relations in the source report:** EXERCISE, EXERCISE TYPE, INTENSITY LEVEL, MUSCLE GROUP. **Test identifier:** TC-RI-11.

### RI-12
Store the trainer who authored each exercise.

**Supporting schema relations in the source report:** EXERCISE, TRAINER. **Test identifier:** TC-RI-12.

### RI-13
Maintain the information needed to identify and prevent duplicate exercises under the defined duplicate-detection criterion.

**Supporting schema relations in the source report:** EXERCISE. **Test identifier:** TC-RI-13.

### RI-14
For each trainer-program authorization, store whether the trainer may generate routines, validate routines, or do both, and the authorization validity period.

**Supporting schema relations in the source report:** AUTHORISES. **Test identifier:** TC-RI-14.

### RI-15
Store each client's enrollment in each training program, including enrollment date.

**Supporting schema relations in the source report:** INSCRIBED. **Test identifier:** TC-RI-15.

### RI-16
Store each routine's identifier, creation date, status, training program, and creator.

**Supporting schema relations in the source report:** ROUTINE. **Test identifier:** TC-RI-16.

### RI-17
Store routine-generation parameters: target intensity, proportions of exercise types, muscle-group coverage, and total exercise count.

**Supporting schema relations in the source report:** PARAMETERS ROUTINE. **Test identifier:** TC-RI-17.

### RI-18
Store each routine's composition, including each exercise's order, sets, repetitions, and rest time.

**Supporting schema relations in the source report:** CONTAINS. **Test identifier:** TC-RI-18.

### RI-19
Store routine review/validation status and preserve a reference to the routine that originated a new generation.

**Supporting schema relations in the source report:** ROUTINE, VALIDATE. **Test identifier:** TC-RI-19.

### RI-20
For every routine review, store the room chief, review date, observations, and decision.

**Supporting schema relations in the source report:** VALIDATE. **Test identifier:** TC-RI-20.

### RI-21
Store the criteria specified by the room chief when requesting a new routine and preserve the relationship between the review and the resulting routine.

**Supporting schema relations in the source report:** VALIDATE, ROUTINE. **Test identifier:** TC-RI-21.

### RI-22
Store routine assignments to clients, including the client, assigned routine, assignment date, and end date where applicable.

**Supporting schema relations in the source report:** ASSIGNMENT. **Test identifier:** TC-RI-22.

### RI-23
Store every session recorded by a client for an assigned routine, including date, start/end times, perceived intensity, completion status, and observations.

**Supporting schema relations in the source report:** SESION, ASSIGNMENT. **Test identifier:** TC-RI-23.

### RI-24
Provide the information needed to identify and prevent repeated assignment of the same routine to the same client.

**Supporting schema relations in the source report:** ASSIGNMENT. **Test identifier:** TC-RI-24.

### RI-25
For every adjustment request, store the requesting client, routine, selected trainer, request date, reason, and status.

**Supporting schema relations in the source report:** REQUEST. **Test identifier:** TC-RI-25.

### RI-26
Store the trainer who resolves an adjustment request, response date, result, and resulting routine.

**Supporting schema relations in the source report:** ADJUSTMENT RESULT, REQUEST, ROUTINE. **Test identifier:** TC-RI-26.

### RI-27
Preserve the relationship between an adjustment request, the original routine, and the resulting routine.

**Supporting schema relations in the source report:** REQUEST, ADJUSTMENT RESULT, ROUTINE. **Test identifier:** TC-RI-27.

### RI-28
Provide the data needed to list automatically generated routines for a program, including creator, creation date, and generation parameters.

**Supporting schema relations in the source report:** ROUTINE, PARAMETERS ROUTINE. **Test identifier:** TC-RI-28.

### RI-29
Provide the data needed to identify the most-used exercises in final routines for a program, classified by intensity and muscle group.

**Supporting schema relations in the source report:** ROUTINE, CONTAINS, EXERCISE. **Test identifier:** TC-RI-29.

### RI-30
Provide the data needed to list routines validated by a specified reviewer, including validation date and observations.

**Supporting schema relations in the source report:** VALIDATE, ROUTINE. **Test identifier:** TC-RI-30.

### RI-31
Provide the data needed for routine-performance reports, grouping exercises by intensity and comparing completion rates.

**Supporting schema relations in the source report:** SESION, ASSIGNMENT, CONTAINS, EXERCISE. **Test identifier:** TC-RI-31.

### RI-32
Provide the data needed to compare routines across programs by exercise distribution over muscle groups and intensity, and determine whether balance criteria were met.

**Supporting schema relations in the source report:** ROUTINE, CONTAINS, EXERCISE, WORKOUT PROGRAM. **Test identifier:** TC-RI-32.

### RI-33
For each program, provide exercise intensity, average performance measured as completion rate, and the correlation between those indicators.

**Supporting schema relations in the source report:** EXERCISE, SESION, ASSIGNMENT, WORKOUT PROGRAM. **Test identifier:** TC-RI-33.

### RI-34
Provide the data needed to identify the ten exercises with the highest abandonment rate, including creator and training program.

**Supporting schema relations in the source report:** EXERCISE, TRAINER, CONTAINS, ROUTINE, WORKOUT PROGRAM. **Test identifier:** TC-RI-34.

### RI-35
Provide the data needed to compare the performance of clients who requested routine adjustments with the general completion average at their sites for the same programs.

**Supporting schema relations in the source report:** REQUEST, ADJUSTMENT RESULT, SESION, ASSIGNMENT, CLIENT, SITE, WORKOUT PROGRAM. **Test identifier:** TC-RI-35.

## Six report requirements (REP-01 through REP-06)

### REP-01 — Original report item 1
List automatically generated routines for a selected training program, including creator name, creation date, and generation parameters.

**Functional/informational links:** RF-35; RI-28. **Test identifier:** TC-REP-01.

**Open point:** Routine inclusion is described as automatically generated; confirm which lifecycle statuses count if this distinction affects the query.

### REP-02 — Original report item 2
Identify the most-used exercises in final routines for a selected training program, classified by intensity level and muscle group.

**Functional/informational links:** RF-36; RI-29. **Test identifier:** TC-REP-02.

**Open point:** The source does not define the number of results, tie handling, analysis time window, or the precise meaning of final routine.

### REP-03 — Original report item 3
List routines validated by a specified reviewer, including validation date and observations.

**Functional/informational links:** RF-37; RI-30. **Test identifier:** TC-REP-03.

**Open point:** Confirm whether the report lists all validation events or only the latest validation for each routine.

### REP-04 — Original report item 4
Report client performance for a routine, group exercises by intensity, and compare completion rates.

**Functional/informational links:** RF-38; RI-31. **Test identifier:** TC-REP-04.

**Open point:** The design defines session fields, including completion status, but does not define the aggregation formula for every presentation of the rate.

### REP-05 — Original report item 5
Compare routines generated for different training programs by muscle-group and intensity distribution and show whether balance criteria were met.

**Functional/informational links:** RF-39; RI-32. **Test identifier:** TC-REP-05.

**Open point:** The criteria for balance are referenced but no numeric thresholds are specified in the source excerpts; link the approved algorithm/criteria before implementing a verdict.

### REP-06 — Original report item 6
For each training program, correlate exercise intensity with average client performance; identify the ten exercises with the highest abandonment rate, their creator and program; and compare adjustment-requesting clients with the general completion average at their sites for the same programs.

**Functional/informational links:** RF-40, RF-41, RF-42; RI-33, RI-34, RI-35. **Test identifier:** TC-REP-06.

**Open point:** The source defines average performance as completion rate in RI-33, but does not define the correlation method or all denominator/time-window details for abandonment and the adjustment cohort. Confirm these before implementation.

## Database integrity requirements

### Uniqueness constraints (original identifiers U-1 through U-12)

- **U-1 (USER):** A user's email address must be unique.
- **U-2 (WORKOUT PROGRAM):** A training-program name must be unique.
- **U-3 (MUSCLE GROUP, EXERCISE TYPE, INTENSITY LEVEL):** Catalog names must be unique within their respective catalog.
- **U-4 (INSCRIBED):** The pair (idClient, idWorkoutProgram) must be unique; a client cannot enroll in the same program twice.
- **U-5 (AUTHORISES):** The pair (idTrainer, idWorkoutProgram) must be unique; the source describes no duplicate authorization for a trainer/program pair.
- **U-6 (CONTAINS):** The pair (idRoutine, idExercise) must be unique; an exercise cannot occur more than once in a routine.
- **U-7 (CONTAINS):** The pair (idRoutine, order) must be unique; two exercises cannot occupy the same position in one routine.
- **U-8 (PARAMETERS ROUTINE):** idRoutine must be unique; each routine has exactly one parameterization.
- **U-9 (ASSIGNMENT):** The pair (idRoutine, idClient) must be unique; the same routine cannot be assigned to the same client more than once.
- **U-10 (SESION):** The pair (idAssignment, fechaSesion) must be unique; a client cannot record two sessions on the same day for the same assignment.
- **U-11 (ADJUSTMENT RESULT):** idRequest must be unique in ADJUSTMENT RESULT; each request can have at most one result.
- **U-12 (EXERCISE):** The combination (exercise name, idMuscleGroup) must be unique to prevent duplicate exercises.

### Semantic and business constraints (original identifiers R1 through R13)

- **R1 — Exercise bank:** Prevent duplicate exercises using the approved criterion.
- **R2 — Exercise classification:** Only the trainer who authored an exercise may change its muscle-group, type, and intensity classification.
- **R3 — Trainer authorization:** A trainer may generate or validate routines only for programs where the trainer has the corresponding authorization.
- **R4 — Cross-trainer routine access:** A trainer may consult routines from other trainers only when the trainers serve the same program.
- **R5 — Routine assignment:** Prevent assigning the same routine twice to a client when it represents the same active assignment within the program.
- **R6 — Client enrollment:** A routine may be assigned only to a client enrolled in the routine's training program.
- **R7 — Session registration:** A session may be registered only for a routine assigned to the client who performed the session.
- **R8 — Generation provenance:** Every automatically generated routine must preserve its generation parameters, including exercise-type proportions, muscle-group coverage, and total exercise count.
- **R9 — Muscle-group coverage:** Muscle groups in a routine must be consistent with the muscle groups the associated program is meant to cover.
- **R10 — Routine approval:** A routine must be approved by a room chief authorized for the program; store approval date and observations, and require observations for an unfavorable decision.
- **R11 — Re-generation lineage:** When a room chief requests another routine, the resulting routine must reference the originating review and the previous routine must be marked as superseded.
- **R12 — Adjustment request lifecycle:** The client must select the trainer; retain the result linked to its request; do not allow a new adjustment request for the same routine while a request is pending.
- **R13 — Associative entity uniqueness:** AUTHORISES, INSCRIBED, and CONTAINS must not contain duplicate rows for the same participant combination.

### Domain constraints (project tracking IDs; source Section 4.2 has no per-rule IDs)

- **DOM-01:** User role must be one of administrator, trainer, room chief, or client.
- **DOM-02:** Intensity must be low, medium, or high for exercise classification, routine target intensity, and perceived session intensity.
- **DOM-03:** Exercise type must be strength, cardio, or flexibility.
- **DOM-04:** Client age must be a positive integer.
- **DOM-05:** Creation, validation, execution, assignment, and routine-modification dates must be valid date values.
- **DOM-06:** Required attributes defined by the model, including names and identifiers, must not be null.
- **DOM-07:** Quantities, percentages, repetitions, times, and other numeric values must not be negative.
- **DOM-08:** A routine's total exercise count must be an integer greater than zero.
- **DOM-09:** Exercise order within a routine must be a positive integer.
- **DOM-10:** Exercise-type proportions must be non-negative and sum to one.

### Temporal constraints (project tracking IDs; source Section 4.8 has no per-rule IDs)

- **TEMP-01:** A routine cannot be validated before it was created.
- **TEMP-02:** A session date cannot precede the date the routine was assigned to the client.
- **TEMP-03:** An adjustment result cannot be recorded before its request.
- **TEMP-04:** Authorization end date cannot precede its start date.
- **TEMP-05:** Assignment end date cannot precede its assignment date.
- **TEMP-06:** A routine generated as the result of a review cannot have a creation date before that review.
- **TEMP-07:** A session end time cannot precede its start time.

### Other integrity families

- **Entity integrity:** every entity/associative relation has a primary key; primary-key attributes are non-null and unique. **Source:** S3, Section 4.1, printed p. 18.
- **Referential integrity:** every foreign key references an existing related occurrence; this includes program enrollments and trainer authorizations, exercise-to-routine composition, routine creator/program, validation and authorization, assignments, sessions linked through assignments, adjustment requests, and adjustment results. Historical parent records must not be deleted if that would lose required history unless an explicit safe deletion/cascade policy is defined. **Source:** S3, Section 4.3, printed pp. 19–20.
- **Nullability:** IDs and primary keys are mandatory; names, program objective, trainer specialty, client age/site, exercise classification/creator, event dates, adjustment reason/result description, and validation decision are required. The report identifies nullable fields including exercise description, authorization/assignment end dates, validation/session observations, perceived session intensity, and routine-origin reference. **Source:** S3, Section 4.5, printed p. 21.
- **Implementation mechanisms:** PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK, database triggers, or application logic depending on the rule's nature. **Source:** S3, Section 4.10, printed pp. 25–26.

## Design references and explicit unresolved conflicts

- The report describes a 21-relation relational core with 31 foreign keys and includes a requirement-to-relation mapping in Table 10 (printed pp. 37–38).
- The report's Section 4.9 proposes MongoDB for nested routine blocks and Redis for a cache. The project's separately agreed implementation constraints are PostgreSQL only, no MongoDB, and no Redis. This is a genuine source/design conflict and must be reconciled before implementation; it is recorded here, not silently resolved.
- In Report REP-02, the source does not define number of results, ties, or analysis period. REP-03 does not settle latest-vs-all validation events. REP-04 requires the report's stated completion-rate comparison but does not specify every aggregation detail. REP-05 references balance criteria without a fully stated numeric threshold. REP-06 gives its high-level correlation and comparison requirements but leaves the specific correlation method/abandonment-rate denominator and analysis window for confirmation.
- The project planning file says E1-07 implements U-1 through U-12 and E1-08 implements three cross-entity consistency mechanisms. Those implementation issues should trace back to this source catalogue; they do not supersede the report's full requirements.
