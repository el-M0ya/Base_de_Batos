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

### NFR-11 — Use version control and preserve meaningful history

The project shall use a version-control system. The shared commit history must remain readable and must not be altered by force-pushing or rewriting shared history. Commit messages should be descriptive, commits reasonably atomic, and the history should reflect actual individual contributions rather than one oversized commit or many insignificant commits.

**Original source identifiers:** Engineering Software condition 1, S1, p. 3; Database II implementation guidance, S2, p. 4.
**Sources:** S1 and S2.

### NFR-12 — Project planning with a CASE/planning tool

The team shall carry out project planning using a planning/CASE tool such as GitHub, Jira, or Gantt software.

**Original source identifier:** Engineering Software condition 2, S1, p. 3.  
**Source:** S1. The project's existing GitHub Project named planificacion is the intended tracking location; no duplicate project is required.

### NFR-13 — Satisfy the stated functional requirements

The delivered application shall implement the functional requirements extracted from the problem statement, including all six informational queries and the shared table/chart, PDF-export, and sortable-column requirements.

**Original source identifier:** Engineering Software condition 4, S1, p. 3.
**Source:** S1. Use FR-01 through FR-19 and REP-01 through REP-06 as the traceable catalogue; this requirement does not replace those individual acceptance criteria.

## Database II and course deliverable constraints

These are coursework/deliverable constraints rather than runtime quality attributes. They are included here because E0-05 explicitly requires requirements to be traced to the specific Database II guidance.

### BD2-DEL-01 — Include the required sections in the database design report

The database design report shall include:
1. team name and the name/group of each team member;
2. project title;
3. an enriched analysis and reformulation of functional and informational requirements;
4. the Extended Relational-Conceptual Model (MERX);
5. a specification of identified/established integrity constraints; and
6. an assessment of database-design correctness.

**Source:** S2, “Informe: Diseño de la base de datos”, p. 3.

### BD2-DEL-02 — Prepare test data for the informational queries

The team shall create a test dataset that allows the correctness and effectiveness of the six informational queries to be checked. Test records should cover the relevant paths and boundary cases established by the approved report definitions; the source does not prescribe exact record counts.

**Source:** S2, “Características del proyecto”, p. 2. Related requirements: REP-01 through REP-06.

### BD2-DEL-03 — Follow the documented report-submission and correction process

The methodological guidance states that reports and specified information are submitted to the course group on Tuesdays at 10:00 a.m., and that reports must be submitted as PDF. After instructor review, requested corrections are due no later than one week after that review. Its published schedule lists the database design report in week 5, a progress checkpoint in week 8, complete technical documentation in week 11, and project discussion/review in weeks 11–12.

**Source:** S2, “Programación de actividades de la asignatura” and “Informe: Diseño de la base de datos”, pp. 2–3. Verify dates and any later changes against current instructor announcements before scheduling actual submissions.

### BD2-DEL-04 — Respect the explicit Software Engineering grading gate

The problem statement lists eight Software Engineering project requirements and states that the first six are indispensable for passing the course. Requirements 7 and 8 (maintainable/decoupled architecture and unit tests for both backend and frontend) remain stated requirements even though the document distinguishes the first-six pass gate.

**Source:** S1, “Requisitos particulares de la asignatura Ingeniería de Software”, p. 3.

## Verification notes and open decisions

- The problem statement says the team may have up to five members, while the Database II guidance says teams consist of five students. The project has separately reported a six-person team. Obtain instructor confirmation or document an approved exception rather than silently changing either source.
- The complete approved Database Design Report/MERX and the full text of constraints U-1 through U-12 were not found in the available context. Request the approved report before claiming that every database-specific constraint has been extracted and individually verified.
- The separate “Documento Técnico. Informe Técnico de Software” is referenced as a future course document; its detailed technical-documentation requirements cannot yet be extracted. Update this catalogue when that document is supplied.
- NFR-02 needs an agreed compatibility matrix (OS/browser versions) before a definitive platform test can be written.
- NFR-03 needs a measurable response-time target, a concurrency target, and a reproducible load-test environment. Do not invent these values.
- NFR-04 needs an agreed usability review method.
- NFR-08 requires frontend test issues and test setup to be tracked when that work is planned; the currently identified E2 unit-test issue is backend-focused.
- NFR-09's public repository status can be observed, but instructor collaborator access must be verified separately.
- NFR-10 and NFR-11 should be checked as part of pull-request review and the final release checklist.