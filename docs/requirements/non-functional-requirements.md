# Non-Functional Requirements

## Source and identifier policy

The authoritative requirement identifiers are those in the team's Database Design Report, Section 2.2: **RNF-01 through RNF-12** (printed page 8). They are preserved exactly. No new NFR-01 numbering scheme is substituted.

**Primary source (S3):** *Informe — Diseño de la Base de Datos: Gestión para la generación automática de planes de entrenamiento*, Section 2.2, p. 8. **Supporting source (S2):** *Orientaciones Metodológicas — Bases de Datos II, Curso 2026–2027*, especially pp. 2–4.

## Requirements

### RNF-01
The solution shall be a web application that runs across different operating systems and browsers.

**Concern:** Cross-platform web application. **Implementation/verification tracking:** Frontend and deployment issues TBD. **Test identifier:** TC-RNF-01.

### RNF-02
The user interface shall be friendly, intuitive, and easy to use.

**Concern:** Usability. **Implementation/verification tracking:** Frontend/usability issue TBD. **Test identifier:** TC-RNF-02.

### RNF-03
A client's active routine shall be available practically immediately during the training session.

**Concern:** Active-routine availability. **Implementation/verification tracking:** Performance issue TBD; #37. **Test identifier:** TC-RNF-03.

### RNF-04
Performance shall be maintained when multiple users are connected simultaneously.

**Concern:** Scalability and concurrency. **Implementation/verification tracking:** Performance/load-test issue TBD. **Test identifier:** TC-RNF-04.

### RNF-05
The application shall use a decoupled architecture separating frontend and backend to facilitate extensibility and maintenance.

**Concern:** Architecture quality. **Implementation/verification tracking:** #30, #33, #34. **Test identifier:** TC-RNF-05.

### RNF-06
The solution shall implement at least two software design patterns.

**Concern:** Design patterns. **Implementation/verification tracking:** #42, #43. **Test identifier:** TC-RNF-06.

### RNF-07
Code shall follow good programming practices and contain structured comments/documentation.

**Concern:** Code quality and documentation. **Implementation/verification tracking:** PR review checklist; implementation issues. **Test identifier:** TC-RNF-07.

### RNF-08
Unit tests shall be implemented for both frontend and backend.

**Concern:** Unit testing. **Implementation/verification tracking:** #41; frontend unit-test issue TBD. **Test identifier:** TC-RNF-08.

### RNF-09
Development shall use version control, with frequent atomic commits that reflect each team member's contribution.

**Concern:** Version control and contribution evidence. **Implementation/verification tracking:** #5, #6. **Test identifier:** TC-RNF-09.

### RNF-10
Project planning shall use a CASE/project-planning tool.

**Concern:** Project planning. **Implementation/verification tracking:** #7. **Test identifier:** TC-RNF-10.

### RNF-11
All relevant operations shall be permanently stored to preserve historical traceability of information.

**Concern:** Persistence and historical traceability. **Implementation/verification tracking:** #20, #22-#29. **Test identifier:** TC-RNF-11.

### RNF-12
PDF export and dynamic result-column sorting shall be available to every user type.

**Concern:** Cross-user report functionality. **Implementation/verification tracking:** Frontend/report issues TBD. **Test identifier:** TC-RNF-12.

## Database II and project-deliverable constraints

These are separate course/process constraints, not additional RNF identifiers. They are documented separately so that the original RNF numbering remains unchanged.

### BD2-DEL-01 — Required contents of the database design report
The Database II guidance says the design report must contain: team name and each member's name/group; project title; an enriched analysis/reformulation of functional and informational requirements; the Extended Relational-Conceptual Model (MERX); a specification of integrity constraints; and an assessment of database-design correctness. **Source:** S2, “Informe: Diseño de la base de datos,” p. 3.

### BD2-DEL-02 — Test dataset for information queries
A test dataset must be prepared to verify the correctness and effectiveness of the informational queries. The source does not mandate an exact record count. **Source:** S2, “Características del proyecto,” p. 2. Related reports: REP-01 through REP-06.

### BD2-DEL-03 — Submission and revision process
The methodological guidance states that submissions identified in the course are collected in the course group on Tuesdays at 10:00 a.m.; documents must be submitted as PDF; corrections requested after instructor review must be delivered no later than one week after that review. The published schedule places the database design report in week 5, the progress checkpoint in week 8, complete technical documentation in week 11, and project discussion/review in weeks 11–12. Confirm later changes against instructor announcements. **Source:** S2, pp. 2–3.

### BD2-DEL-04 — Repository and reproducibility guidance
The repository should be public and include the instructors and all team members as collaborators. The team should preserve readable commit history (no force-push/history rewriting of shared branches), maintain meaningful atomic commits, include a README with setup steps and environment/dependency files, maintain the dependency list, use a .gitignore for generated files and secrets, and never commit credentials or private configuration. **Source:** S2, p. 4.

### BD2-DEL-05 — Software Engineering pass gate
The problem statement lists eight Software Engineering project criteria and says the first six are indispensable for passing. Requirements 7 and 8 (decoupled/maintainable architecture and frontend/backend unit tests) still remain stated requirements even though the document distinguishes the first-six pass gate. **Source:** S1, p. 3.

## Open issues and decisions

- **Team-size discrepancy:** S1 says the team may have up to five members and S2 says teams consist of five students, while the submitted design report lists six team members. Confirm the instructor's approval/exception rather than silently changing the source.
- **Technology conflict:** the database design report Section 4.9 proposes MongoDB and Redis for variable routine structure/cache, but the project's accepted architecture constraints say PostgreSQL only and explicitly reject both technologies. This must be reconciled with the instructors/team before implementation; it is not silently changed in this requirements catalogue.
- **Performance metric:** RNF-03 and RNF-04 state “practically immediate” availability and concurrent-user performance, but provide no measurable latency/concurrency target. An acceptance threshold and test environment are needed.
- **The separate Software Technical Report guide:** the Database II guidance refers to “Documento Técnico. Informe Técnico de Software” as a document to be provided later. Its detailed requirements are not derivable from the current source set until that document is available.
