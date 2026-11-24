# Informational Report Queries

The read-only query contracts and PostgreSQL adapters for REP-01 through REP-06
are separate from the routine and validation write repositories. They return
report DTOs and leave HTTP routing to the report API issue.

| Report | Filters | Date applied to | Results |
|---|---|---|---|
| REP-01 | Required program, optional start/end dates | Routine creation date | Every routine with its trainer and generation-parameter snapshot |
| REP-02 | Required program, optional start/end dates | Routine creation date | Exercise-use counts grouped by exercise, target routine intensity, and muscle group |
| REP-03 | Required reviewer, optional start/end dates | Validation date | One row per validation event, including decision and observations |
| REP-04 | Required routine | Assignment and session records | Exercises, routine intensity, per-client sessions and completion rate |
| REP-05 | None | Current routines | Exercise-use counts by program, muscle group and routine intensity |
| REP-06a | None | Client sessions | Pearson correlation by program using intensity scores 1/2/3 |
| REP-06b | None | Not calculated | Explicit `DEFINITION_PENDING`; no ranking until the abandonment rate is approved |
| REP-06c | None | Client sessions and adjustment requests | Adjustment-client completion average versus site average by program |

The source does not fully define “final routine” for REP-02. This implementation
uses `APPROVED` as the final state. The schema stores intensity on
`parameters_routine`, not on `exercise`, so REP-02 reports the routine's target
intensity for each exercise use. The source does not specify whether REP-03
should show only the latest review; this implementation returns every review
event so earlier decisions and observations remain visible.

Date bounds are inclusive. Reversed ranges and invalid identifiers are rejected
by the query DTOs. Every SQL value is passed as a parameter. No report-specific
index is added: execution plans are exercised with
`EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` in the PostgreSQL integration test, and
the fixture is too small to justify additional indexes.

REP-04 reports one row per assigned client (and one null-client row when a
routine has no assignments). Completion rate is completed sessions divided by
recorded sessions; no sessions yields `NULL`. REP-05 includes programs without
routines with zero counts. Since numeric balance thresholds are unspecified,
it returns `balance_criteria_met = NULL` and `CRITERIA_UNSPECIFIED`.

REP-06a maps the existing ordered intensity values (`bajo/low`, `medio/medium`,
`alto/high`) to 1, 2, and 3, then correlates that score with each client's
completion rate for an assigned routine. PostgreSQL `corr()` returns NULL when
there are too few observations or no variance; a status distinguishes these
cases. REP-06b deliberately returns no ranked rows: `session.completada`
describes an entire session, so it cannot support exercise-level abandonment
without an instructor-approved definition. REP-06c averages each client's
completion fraction within a program and compares adjustment clients with the
site average for that same program.
