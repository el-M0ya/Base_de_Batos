# Informational Requirements and Reports

## Purpose and numbering

The problem statement lists six informational queries under “Funcionalidades”, numbered 1 through 6. This document assigns each a stable project identifier, **REP-01** through **REP-06**, while explicitly retaining its original number. The REP identifiers supplement the source numbering; they do not replace it.

**Source:** S1 — *Gestión para la generación automática de planes de entrenamiento*, “Funcionalidades”, p. 2, with context from “Descripción del problema”, pp. 1–2.

## Shared output requirements

All six reports are covered by these common requirements:

- **FR-17:** present report results as tables and charts.
- **FR-18:** allow every type of system user to export displayed information to PDF.
- **FR-19:** allow each displayed result column to be sorted.

The source does not specify chart types, PDF layout, pagination, file naming, or a numeric performance objective for report generation. Those details need a team decision if needed for acceptance tests.

## REP-01 — Automatically generated routines for a selected program

**Original source number:** 1.

For a specified training program, list routines that were generated automatically and show:
- the routine creator's name;
- the creation date;
- the parameters used for generation.

**Source:** S1, “Funcionalidades”, p. 2, item 1.

**Data dependencies:** training program, routine, creator, creation timestamp, generation parameters.

**Validation questions:** define which routine lifecycle states count as “generated automatically” for this report and confirm how a program is selected.

## REP-02 — Most-used exercises in final routines

**Original source number:** 2.

For a selected training program, report the exercises most frequently used in final routines, classified by intensity level and muscle group.

**Source:** S1, “Funcionalidades”, p. 2, item 2.

**Data dependencies:** exercise, routine, program, exercise intensity, muscle group, and a way to identify final routines and count exercise use.

**Validation questions:** the source does not define “final routine”, the number of exercises to return as “most-used”, tie handling, or the period to analyze. These must be agreed rather than assumed.

## REP-03 — Routines validated by a specified reviewer

**Original source number:** 3.

List the routines validated by a specified reviewer and include the validation date and observations recorded during validation.

**Source:** S1, “Funcionalidades”, p. 2, item 3.

**Data dependencies:** routine, reviewer/room chief, validation record, validation date, and observations.

**Validation questions:** confirm whether the report returns only the latest validation per routine or every validation event. The source does not settle this.

## REP-04 — Client performance for a routine

**Original source number:** 4.

Produce a report about client performance for a routine, group exercises by intensity, and compare completion rates.

**Source:** S1, “Funcionalidades”, p. 2, item 4.

**Data dependencies:** client, routine, exercises, intensity, recorded training sessions, and a definition of completion.

**Validation questions:** define the numerator and denominator for a completion rate, how partial sessions are treated, the analysis period, and whether rates are calculated per client, exercise, or routine. The source does not specify these formulas.

## REP-05 — Compare routines across programs and assess balance

**Original source number:** 5.

Compare routines generated for different training programs by showing the distribution of exercises across muscle groups and intensity levels and whether the balance criteria were met.

**Source:** S1, “Funcionalidades”, p. 2, item 5.

**Data dependencies:** training program, routines, exercises, muscle groups, intensity levels, and the applicable balance criteria.

**Validation questions:** the source does not define numerical balance thresholds or the rule for deciding whether a routine meets them. Those rules must be supplied by the instructor/team or an approved requirements/design document before a compliance verdict is implemented.

## REP-06 — Intensity, performance, abandonment, and adjustment comparison

**Original source number:** 6.

For each training program, report the correlation between exercise intensity and average client performance. The same report shall:
1. identify the ten exercises with the highest abandonment rate;
2. show the trainer who created each identified exercise;
3. show the training program to which each exercise belongs; and
4. compare the performance of clients who requested a routine adjustment with the overall average completion rate for their respective sites and the same training programs.

**Source:** S1, “Funcionalidades”, p. 2, item 6.

**Data dependencies:** training program, exercise, intensity, exercise creator, client performance, abandonment, routine-adjustment requests, site, and completion records.

**Validation questions:**
- Define the performance measure and how average performance is calculated.
- Define “abandonment rate”, its denominator, and the time window.
- Specify the correlation method and how intensity levels are encoded or ordered for the calculation.
- Define how clients who requested an adjustment are identified and which sessions/programs enter the comparison.
- Define tie handling when more than ten exercises share a boundary abandonment rate.

These are material calculation rules. They must not be invented by the implementation team without approval.

## Cross-report traceability

| Report ID | Original item | Primary requirement links | Implementation issue |
|---|---:|---|---|
| REP-01 | 1 | FR-13, FR-17–FR-19 | No dedicated report/query implementation issue identified yet |
| REP-02 | 2 | FR-02, FR-03, FR-17–FR-19 | No dedicated report/query implementation issue identified yet |
| REP-03 | 3 | FR-12, FR-17–FR-19 | No dedicated report/query implementation issue identified yet |
| REP-04 | 4 | FR-08, FR-09, FR-17–FR-19 | No dedicated report/query implementation issue identified yet |
| REP-05 | 5 | FR-03, FR-13, FR-17–FR-19 | No dedicated report/query implementation issue identified yet |
| REP-06 | 6 | FR-08–FR-11, FR-14–FR-19 | No dedicated report/query implementation issue identified yet |

The existing database and backend issues lay data foundations but do not, by themselves, demonstrate that any report is implemented. Create dedicated report/query implementation issues when scheduling this work, and link each issue to the corresponding REP identifier.