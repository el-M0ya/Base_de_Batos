# Functional Requirements

## Purpose and identification rules

This document translates the available assignment into verifiable functional requirements for the Training Plan Automatic Generation Management System.

The source problem statement does not assign identifiers to most narrative requirements. Therefore, identifiers **FR-01** onward are stable project identifiers introduced by this document; they do not replace or renumber any source identifier. The six numbered informational queries remain numbered 1–6 in the source and are catalogued separately as **REP-01** through **REP-06** in `informational-requirements.md`.

## Sources

- **S1 — Problem statement:** *Gestión para la generación automática de planes de entrenamiento*, especially “Descripción del problema” and “Funcionalidades”, pp. 1–3. Repository copy: [docs/4_Gestión_para_la_generación_automática_de_planes_de_entrenamiento.pdf](../4_Gestión_para_la_generación_automática_de_planes_de_entrenamiento.pdf).
- **S2 — Database II course guidance:** *Orientaciones metodológicas — Bases de Datos II, Curso 2026–2027*, especially the project and implementation guidance, pp. 1–5. Repository copy: [docs/BD2 - Orientaciones metodológicas.pdf](../BD2%20-%20Orientaciones%20metodológicas.pdf).
- **S3 — Approved database design:** The approved MERX, integrity-constraint specification, and final Database II design report were not identified among the available project documents during this requirements pass. Design-specific rules must be reconciled against the approved deliverable before being treated as definitive.

## Requirements

### FR-01 — Register exercises

A trainer shall be able to add exercises to the existing exercise bank.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-02 — Classify trainer-authored exercises

A trainer shall be able to classify exercises authored by that trainer by muscle group, exercise type (strength, cardio, or flexibility), and intensity level (low, medium, or high).

**Source:** S1, “Descripción del problema”, p. 1.

### FR-03 — Generate routines automatically

A trainer shall be able to generate routines automatically from selected available exercises. Generation criteria described by the source include intensity, exercise type, muscle-group coverage across the training cycle, exercise-type proportions, and the total number of exercises. Exact validation rules and algorithms must be specified in the approved design or implementation issues; they must not be inferred from this summary.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-04 — View routines for a shared program

A trainer shall be able to view routines created by other trainers who work with the same training program.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-05 — Prevent duplicate exercises

The system administrator shall be able to prevent duplicate exercises from being registered in the exercise bank.

**Source:** S1, “Descripción del problema”, p. 1. The precise duplicate-detection key or comparison rule needs confirmation from the approved database design.

### FR-06 — Prevent double assignment of routines

The system shall prevent a routine from being assigned twice to the same client when this would constitute a duplicate assignment. The exact uniqueness scope and whether re-assignment is permitted after a routine expires or is replaced must follow the approved database design and be confirmed by the team.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-07 — Access assigned routines

A client shall be able to access routines assigned to that client.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-08 — Record completed training sessions

The system shall store each session registered for an executed routine and preserve the association between the session and that routine's assignment or execution context.

**Source:** S1, “Descripción del problema”, p. 1. The exact session fields and completion semantics require the approved data design.

### FR-09 — Consult progress information

Trainers and clients shall be able to consult progress reports. Client progress shall be available by training program.

**Source:** S1, “Descripción del problema”, pp. 1–2, and “Funcionalidades”, p. 2. Report-specific requirements are REP-01–REP-06.

### FR-10 — Request a routine adjustment

A client shall be able to submit a routine-adjustment request online and specify the trainer who is to carry out the adjustment.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-11 — Preserve adjustment history and results

The system shall store the adjustment-request process and the result of the manual adjustment.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-12 — Review, approve, or return generated routines

A room chief shall be able to review and approve a generated routine or request the preparation of another routine according to the room chief's criteria.

**Source:** S1, “Descripción del problema”, p. 1. The precise lifecycle states, permitted transitions, and meaning of a returned routine must be agreed and documented.

### FR-13 — Preserve generation parameters

The system shall store the parameterization used to generate a routine together with that routine.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-14 — Respect program-specific trainer authorization

The system shall represent the training programs for which each trainer is authorized to generate or validate routines and enforce that authorization in the corresponding operations.

**Source:** S1, “Descripción del problema”, p. 1.

### FR-15 — Maintain client, site, and program associations

The system shall maintain each client's assigned site and enrollment in training programs, and support access to the client's progress for each enrolled program.

**Source:** S1, “Descripción del problema”, pp. 1–2.

### FR-16 — Preserve each routine's variable structure

The system shall manage the variable, potentially nested block structure of each routine, including warm-ups, circuits, sets, and rests. The source requires that this structure be managed independently rather than forced into the common fixed structure of the other tables. The storage technology is an architectural decision and is not prescribed by this functional requirement.

**Source:** S1, “Descripción del problema”, p. 2.

### FR-17 — Present informational results as tables and charts

The system shall provide results for the six informational queries in a tabular and graphical form.

**Source:** S1, “Funcionalidades”, p. 2. See REP-01–REP-06.

### FR-18 — Export displayed results to PDF

Every type of system user shall be able to export the information displayed by the application to PDF files.

**Source:** S1, “Funcionalidades”, p. 2.

### FR-19 — Sort result columns

Users shall be able to sort each column of displayed results according to their needs.

**Source:** S1, “Funcionalidades”, p. 2.

## Outstanding functional decisions

1. Confirm the duplicate-exercise comparison rule and the precise scope of a duplicate routine assignment.
2. Define session fields and what constitutes a completed, partially completed, or abandoned session; these definitions affect REP-04 and REP-06.
3. Approve the routine lifecycle, including the effect of returning a routine and the relationship between a replacement routine and its source routine.
4. Publish or link the approved MERX and integrity-constraint specification. Constraint identifiers and database-specific requirements must retain the identifiers in that approved source; they must not be reconstructed from the issue descriptions alone.
5. Define the generation criteria and how each criterion is checked, without assuming numerical thresholds that the source does not give.