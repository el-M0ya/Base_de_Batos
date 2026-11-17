# Informational Report Queries

The read-only query contract and PostgreSQL adapter for REP-01 through REP-03
are separate from the routine and validation write repositories. They return
report DTOs and leave HTTP routing to the report API issue.

| Report | Filters | Date applied to | Results |
|---|---|---|---|
| REP-01 | Required program, optional start/end dates | Routine creation date | Every routine with its trainer and generation-parameter snapshot |
| REP-02 | Required program, optional start/end dates | Routine creation date | Exercise-use counts grouped by exercise, target routine intensity, and muscle group |
| REP-03 | Required reviewer, optional start/end dates | Validation date | One row per validation event, including decision and observations |

The source does not fully define “final routine” for REP-02. This implementation
uses `APPROVED` as the final state. The schema stores intensity on
`parameters_routine`, not on `exercise`, so REP-02 reports the routine's target
intensity for each exercise use. The source does not specify whether REP-03
should show only the latest review; this implementation returns every review
event so earlier decisions and observations remain visible.

Date bounds are inclusive. Reversed ranges and invalid identifiers are rejected
by the query DTOs. Every SQL value is passed as a parameter. No report-specific
index is added in this change: execution plans are exercised with
`EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` in the PostgreSQL integration test, and
the fixture is too small to justify additional indexes.
