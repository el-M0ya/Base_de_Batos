# Team Responsibilities

This document records the working allocation supplied for the project. It is a coordination baseline, not a substitute for issue assignment or pull-request review.

## Primary areas

| Team member | Primary area | Expected contribution |
|---|---|---|
| Bryan | Frontend and planning | Frontend implementation, planning coordination, API integration |
| Fabio | Frontend | Frontend components, views, client-side behavior |
| Cuervo | Backend | Backend use cases, API behavior, domain/application implementation |
| Hector | Backend | Backend implementation, API integration, backend tests |
| Gabriel | Database and backend | PostgreSQL schema, SQL queries, data integrity, backend integration |
| Alejandro | QA and documentation | Test planning, verification evidence, quality checks, project documentation |

## Responsibility matrix

| Work area | Primary owner | Review/support |
|---|---|---|
| Frontend UI and React + TypeScript | Bryan / Fabio | Backend owner for API contract; Alejandro for QA |
| Backend use cases and FastAPI endpoints | Cuervo / Hector | Gabriel for persistence integration; Alejandro for QA |
| PostgreSQL schema and direct SQL | Gabriel | Backend owner for query integration; Alejandro for verification |
| Architecture and project documentation | Alejandro | Relevant area owner; Bryan for planning alignment |
| Test strategy and acceptance verification | Alejandro | Developer who owns the affected area |
| Cross-layer integration | Owner of changed layer | Owners of adjacent layers |

Primary ownership may alternate between the two people assigned to an area depending on the issue. Each issue and PR should identify one accountable owner; others may support or review.

## Collaboration rules

- Keep changes focused and link each PR to its issue.
- Request review from someone familiar with the affected area; authors should not be sole reviewers of their own changes.
- Frontend changes must respect the API contract; backend changes must preserve inward dependency direction.
- Database changes must include relevant SQL script updates and verification instructions.
- QA records test outcomes and limitations; documentation is updated when behavior, setup, or decisions change.
- Raise blockers early and identify the decision or help required.

## Open point

The original issue wording mentions a limit of up to five members, while the current allocation lists six. Confirm whether that limit is outdated or whether a role/person should be consolidated. This document preserves all six listed members and does not assume that the discrepancy has been approved.
