# Functional Requirements

## Source and identifier policy

The authoritative numbering for functional requirements is the numbering in the team's Database Design Report, Section 2.1, **RF-01 through RF-45** (printed pages 5–8). These are preserved exactly; this document does not replace them with a new FR numbering scheme. The problem statement's six original informational queries are also tracked separately as REP-01 through REP-06, with original item numbers 1–6 retained.

**Primary source (S3):** *Informe — Diseño de la Base de Datos: Gestión para la generación automática de planes de entrenamiento*, Section 2.1, pp. 5–8. The related problem statement and Database II methodological guidance are in the repository under `docs/`.

## Requirements

### RF-01
Allow users to authenticate with email address and password.

**Feature:** User authentication. **Implementation tracking:** #30, #34, frontend/API issue TBD. **Test identifier:** TC-RF-01.

### RF-02
Manage user roles and restrict available functions according to the administrator, trainer, room-chief, and client roles.

**Feature:** Role and access management. **Implementation tracking:** #30, #34, #40. **Test identifier:** TC-RF-02.

### RF-03
Allow the administrator to register, modify, and deactivate user accounts.

**Feature:** User account administration. **Implementation tracking:** #20, #30, frontend issue TBD. **Test identifier:** TC-RF-03.

### RF-04
Manage trainer information, including unique identifier, name, specialty, and the training programs in which the trainer is authorized to generate or validate routines.

**Feature:** Trainer administration and authorization. **Implementation tracking:** #20, #22. **Test identifier:** TC-RF-04.

### RF-05
Manage client information, including unique identifier, name, age, and assigned site.

**Feature:** Client administration. **Implementation tracking:** #20. **Test identifier:** TC-RF-05.

### RF-06
Manage gym sites so each client belongs to one site and reports can group results by site.

**Feature:** Site and client-site relationship. **Implementation tracking:** #20. **Test identifier:** TC-RF-06.

### RF-07
Separate administrator, trainer, room-chief, and client functions so users can access only operations appropriate to their role.

**Feature:** Authorization enforcement. **Implementation tracking:** #30, #34, #40. **Test identifier:** TC-RF-07.

### RF-08
Manage training programs, including a unique identifier, name, objective, and the muscle groups to cover during the cycle.

**Feature:** Training programs. **Implementation tracking:** #21. **Test identifier:** TC-RF-08.

### RF-09
Allow muscle groups in the domain catalog to be created, modified, and deleted.

**Feature:** Muscle-group catalog. **Implementation tracking:** #21. **Test identifier:** TC-RF-09.

### RF-10
Allow users to assign to a training program the muscle groups it must cover and consult that assignment.

**Feature:** Program muscle-group coverage. **Implementation tracking:** #21. **Test identifier:** TC-RF-10.

### RF-11
Allow trainers to register exercises in the existing bank, including name, description, and registration date.

**Feature:** Exercise bank. **Implementation tracking:** #22, #36, #39. **Test identifier:** TC-RF-11.

### RF-12
Allow a trainer to classify exercises authored by that trainer by muscle group, exercise type (strength, cardio, flexibility), and intensity (low, medium, high).

**Feature:** Exercise classification. **Implementation tracking:** #22, #25, #36. **Test identifier:** TC-RF-12.

### RF-13
Allow all users to consult the system's exercise bank.

**Feature:** Exercise catalog query. **Implementation tracking:** #22, #36, #40. **Test identifier:** TC-RF-13.

### RF-14
Allow the administrator to identify and prevent duplicate exercises according to the system's defined duplicate-detection criterion.

**Feature:** Duplicate-exercise prevention. **Implementation tracking:** #22, #25. **Test identifier:** TC-RF-14.

### RF-15
Ensure that only the trainer who authored an exercise can modify its classification.

**Feature:** Exercise authorship and authorization. **Implementation tracking:** #22, #25. **Test identifier:** TC-RF-15.

### RF-16
Allow a trainer to be assigned training programs for which they may generate routines, validate routines, or do both.

**Feature:** Trainer-program authorization. **Implementation tracking:** #22, #25. **Test identifier:** TC-RF-16.

### RF-17
Register a client's enrollment in each training program in which the client participates, including enrollment date.

**Feature:** Program enrollment. **Implementation tracking:** #22. **Test identifier:** TC-RF-17.

### RF-18
Prevent a trainer from generating a routine for a program for which the trainer is not authorized.

**Feature:** Generation authorization check. **Implementation tracking:** #25, #32, #39. **Test identifier:** TC-RF-18.

### RF-19
Allow a trainer to consult routines created by other trainers when they serve the same training program.

**Feature:** Program-scoped routine query. **Implementation tracking:** #37, #40. **Test identifier:** TC-RF-19.

### RF-20
Allow a trainer to generate routines automatically from selected exercises.

**Feature:** Automatic routine generation. **Implementation tracking:** #23, #32, #37, #42. **Test identifier:** TC-RF-20.

### RF-21
Allow routine-generation criteria to be set: target intensity, proportions of exercise types, muscle-group coverage, and total number of exercises.

**Feature:** Generation parameterization. **Implementation tracking:** #23, #32, #42. **Test identifier:** TC-RF-21.

### RF-22
Store the parameterization used to generate each routine alongside that routine.

**Feature:** Generation parameter persistence. **Implementation tracking:** #23, #37. **Test identifier:** TC-RF-22.

### RF-23
Record each generated routine's training program, creator, and creation date.

**Feature:** Routine provenance. **Implementation tracking:** #23, #32. **Test identifier:** TC-RF-23.

### RF-24
Record the exercises in each routine, including each exercise's order, number of sets, repetitions, and rest time.

**Feature:** Routine composition. **Implementation tracking:** #23, #37. **Test identifier:** TC-RF-24.

### RF-25
Allow a room chief to review a generated routine and record the review date and observations.

**Feature:** Routine review. **Implementation tracking:** #24, #43. **Test identifier:** TC-RF-25.

### RF-26
Allow a room chief to approve a routine or request creation of another routine under the room chief's criteria.

**Feature:** Routine approval and return/re-generation. **Implementation tracking:** #24, #43. **Test identifier:** TC-RF-26.

### RF-27
Associate each routine generated as the result of a review with the review that originated it.

**Feature:** Routine review lineage. **Implementation tracking:** #23, #24, #43. **Test identifier:** TC-RF-27.

### RF-28
Allow routines to be assigned to clients and prevent duplicate assignment of the same routine to the same client.

**Feature:** Routine assignment. **Implementation tracking:** #24, #25. **Test identifier:** TC-RF-28.

### RF-29
Allow clients to access the routines assigned to them.

**Feature:** Client routine access. **Implementation tracking:** #24, #34, #40. **Test identifier:** TC-RF-29.

### RF-30
Store each session recorded for a routine executed by a client, including date, start time, end time, perceived intensity, and completion status.

**Feature:** Training-session records. **Implementation tracking:** #24. **Test identifier:** TC-RF-30.

### RF-31
Allow clients and trainers to consult client progress reports for training programs in which the clients are enrolled.

**Feature:** Progress reporting. **Implementation tracking:** #24, #40. **Test identifier:** TC-RF-31.

### RF-32
Allow a client to request a routine adjustment online for a routine assigned to that client.

**Feature:** Routine-adjustment requests. **Implementation tracking:** #24. **Test identifier:** TC-RF-32.

### RF-33
Allow the client to specify the trainer who will handle the adjustment request.

**Feature:** Requested trainer selection. **Implementation tracking:** #24. **Test identifier:** TC-RF-33.

### RF-34
Record every adjustment request and the result of the manual adjustment.

**Feature:** Adjustment history and result. **Implementation tracking:** #24. **Test identifier:** TC-RF-34.

### RF-35
For a selected training program, list automatically generated routines with creator name, creation date, and generation parameters.

**Feature:** Report 1: automatically generated routines. **Implementation tracking:** #23, #29, #37, report issue TBD. **Test identifier:** TC-RF-35.

### RF-36
For a selected training program, identify the most-used exercises in final routines, classified by intensity and muscle group.

**Feature:** Report 2: most-used exercises. **Implementation tracking:** #22, #23, #29, report issue TBD. **Test identifier:** TC-RF-36.

### RF-37
List routines validated by a specified reviewer, including validation date and recorded observations.

**Feature:** Report 3: validated routines. **Implementation tracking:** #24, #29, #40, report issue TBD. **Test identifier:** TC-RF-37.

### RF-38
Report client performance for a routine, grouping exercises by intensity and comparing completion rates.

**Feature:** Report 4: routine performance. **Implementation tracking:** #24, #29, #40, report issue TBD. **Test identifier:** TC-RF-38.

### RF-39
Compare routines generated for different training programs by muscle-group and intensity distributions and whether balance criteria were met.

**Feature:** Report 5: routine balance comparison. **Implementation tracking:** #23, #29, #37, report issue TBD. **Test identifier:** TC-RF-39.

### RF-40
For each training program, determine the correlation between exercise intensity and average client performance.

**Feature:** Report 6a: intensity/performance correlation. **Implementation tracking:** #22, #24, #29, report issue TBD. **Test identifier:** TC-RF-40.

### RF-41
Identify the ten exercises with the highest abandonment rate and show their creator and associated training program.

**Feature:** Report 6b: highest exercise abandonment. **Implementation tracking:** #22, #24, #29, report issue TBD. **Test identifier:** TC-RF-41.

### RF-42
Compare the performance of clients who requested a routine adjustment with the general completion average at their sites for the same programs.

**Feature:** Report 6c: adjustment cohort versus site average. **Implementation tracking:** #20, #24, #29, report issue TBD. **Test identifier:** TC-RF-42.

### RF-43
Present query and report results as tables and charts.

**Feature:** Report presentation. **Implementation tracking:** Frontend/report issue TBD. **Test identifier:** TC-RF-43.

### RF-44
Allow every user type to export displayed information to PDF.

**Feature:** PDF export. **Implementation tracking:** Frontend/export issue TBD. **Test identifier:** TC-RF-44.

### RF-45
Allow users to sort every result column according to their needs.

**Feature:** Sortable result columns. **Implementation tracking:** Frontend/table issue TBD. **Test identifier:** TC-RF-45.

## Notes for implementation planning

- Requirement identifiers and descriptions above are source-derived and translated into English. The traceability matrix lists the source page and current issue/test mapping for each item.
- Reports RF-35 through RF-42 comprise the six report requests: report item 6 is represented by RF-40, RF-41, and RF-42 because the source query requires three result groups in one request. REP-06 preserves that as one original report item.
- RF-43 through RF-45 require frontend/report work; dedicated frontend issues have not yet been identified in the repository issue list checked for this pass.
- Exact acceptance formulas not specified by the source (for example, exercise abandonment denominator or routine-balance criteria) are marked for instructor/team confirmation rather than invented.
- The approved database design report proposes a document store and a Redis cache for variable routine blocks (Section 4.9). This conflicts with the project's separately agreed implementation constraints of PostgreSQL only, no MongoDB, and no Redis. Treat that as an unresolved architecture/design conflict; do not interpret the report's technology proposal as an accepted implementation requirement without an explicit reconciliation decision.
