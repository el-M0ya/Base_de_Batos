# Non-Functional and Project Constraints

## Purpose and identification rules

The source assigns original numbers to several Engineering Software conditions. Those numbers are retained below in the **Original source identifier** field. The NFR identifiers introduced here are stable tracking identifiers only; they do not replace the source numbering.

## Sources

- **S1 — Problem statement:** *Gestión para la generación automática de planes de entrenamiento*, pp. 1–3.
- **S2 — Database II course guidance:** *Orientaciones metodológicas — Bases de Datos II, Curso 2026–2027*, pp. 1–5.

Repository copies: [problem statement](../4_Gestión_para_la_generación_automática_de_planes_de_entrenamiento.pdf) and [Database II guidance](../BD2%20-%20Orientaciones%20metodológicas.pdf).

## Requirements

### NFR-01 — Web application

The delivered system shall be a web application.

**Original source identifier:** Problem statement, “Descripción del problema”, p. 1.  
**Source:** S1.

### NFR-02 — Multiplatform operation

The software shall be multiplatform.

**Original source identifier:** Engineering Software condition 3, S1, p. 3.  
**Source:** S1. The supported operating systems, browsers, and minimum versions are not specified and need agreement.

### NFR-03 — Practical availability of the active routine

The active routine information shall be available practically immediately during a client's training session, regardless of the number of simultaneously connected users.

**Original source identifier:** Narrative performance requirement, S1, p. 2.  
**Source:** S1. The source gives no numeric response-time target, concurrency level, test environment, or measurement procedure. Those acceptance thresholds must be agreed before performance compliance can be objectively tested.

### NFR-04 — Intuitive user interaction

The application shall provide an intuitive and user-friendly interaction experience.

**Original source identifier:** Project description, S1, p. 1.  
**Source:** S1. The team must define how usability will be reviewed; the source does not provide a specific usability score or user-test threshold.

### NFR-05 — Decoupled, extensible, maintainable architecture

The application shall use an architecture that allows components to be decoupled, functionality to be extended, and the system to be maintained.

**Original source identifier:** Engineering Software condition 7, S1, p. 3.  
**Source:** S1.

### NFR-06 — Programming quality and documentation

The project shall follow good programming practices, including comments/docstrings throughout the code, logical organization of folders and modules, clear names, and separation of responsibilities.

**Original source identifier:** Engineering Software condition 5, S1, p. 3; implementation guidance, S2, p. 4.  
**Source:** S1 and S2.

### NFR-07 — Use at least two design patterns

The implementation shall include at least two design patterns.

**Original source identifier:** Engineering Software condition 6, S1, p. 3.  
**Source:** S1. Documenting a pattern is not sufficient evidence of implementation; its use must be visible in code and verified through review/tests.

### NFR-08 — Unit tests for both application sides

Unit tests shall be implemented for both the backend and the frontend.

**Original source identifier:** Engineering Software condition 8, S1, p. 3.  
**Source:** S1. The source does not prescribe a specific test framework or coverage percentage.

### NFR-09 — Public repository and contribution traceability

The repository shall be public; the instructors and all team members shall be repository collaborators. Commit history shall remain interpretable and shall not be altered by force-pushing or rewriting shared history. Commits should provide meaningful evidence of each member's contribution.

**Original source identifier:** Database II implementation guidance, S2, p. 4.  
**Source:** S2.

### NFR-10 — Reproducible setup and dependency documentation

The repository shall include a README with the steps needed to run the system, necessary environment/setup files (including Docker files where required), and a dependency list. A .gitignore shall exclude virtual environments, installed dependencies, generated/temporary files, credentials, and other files that should not be versioned. Real secrets must not be committed; environment variables or example configuration files should be used instead.

**Original source identifier:** Database II implementation guidance, S2, p. 4.  
**Source:** S2.

### NFR-11 — Meaningful, controlled version history

The team shall use clear, descriptive, reasonably atomic commits that reflect real progress. Neither a single oversized commit nor a large number of insignificant commits should be used as a substitute for evidence of contribution.

**Original source identifier:** Database II implementation guidance, S2, p. 4.  
**Source:** S2.

### NFR-12 — Project planning with a CASE/planning tool

The team shall carry out project planning using a planning/CASE tool such as GitHub, Jira, or Gantt software.

**Original source identifier:** Engineering Software condition 2, S1, p. 3.  
**Source:** S1. The project's existing GitHub Project named planificacion is the intended tracking location; no duplicate project is required.

## Verification notes and open decisions

- NFR-02 needs an agreed compatibility matrix (OS/browser versions) before a definitive platform test can be written.
- NFR-03 needs a measurable response-time target, a concurrency target, and a reproducible load-test environment. Do not invent these values.
- NFR-04 needs an agreed usability review method.
- NFR-08 requires frontend test issues and test setup to be tracked when that work is planned; the currently identified E2 unit-test issue is backend-focused.
- NFR-09's public repository status can be observed, but instructor collaborator access must be verified separately.
- NFR-10 and NFR-11 should be checked as part of pull-request review and the final release checklist.