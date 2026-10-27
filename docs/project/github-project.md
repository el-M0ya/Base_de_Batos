# GitHub Project Workflow

## Project identity and administration

- **Existing project:** `planificacion`
- **Project discovery link:** https://github.com/users/el-M0ya/projects
- **Repository:** https://github.com/el-M0ya/Proyecto_Conjunto_de_Bases_de_Datos_II_e_Ingenier-a_de_Software
- **Expected administrator:** Bryan (@el-M0ya), subject to confirmation in the Project's **Settings → Manage access** page.

> The repository connection confirms that @el-M0ya has administrator permission on the repository, but repository permissions do not prove the same role on a GitHub Project. Open the project from the link above, select its exact URL, and verify the Project access list before treating the administrator assignment as confirmed. Keep using this existing `planificacion` project; do not create a duplicate.

## Status workflow

Use a single-select field named **Status** with these options, in this order:

| Status | Meaning | When to use it |
|---|---|---|
| Backlog | Work has been captured but is not ready to start. | Scope, dependencies, or priority still need clarification. |
| Ready | Work is understood and can be picked up. | Objective and acceptance criteria are clear; dependencies are addressed. |
| In Progress | Someone is actively working on it. | Implementation or task execution has started. |
| Review | Work is awaiting peer review. | A pull request is open and review is needed. |
| QA | Work is being validated. | Review is complete and functional/testing checks are underway. |
| Done | Work is complete. | Acceptance criteria are met and changes are merged or the task is otherwise finished. |

GitHub Projects may provide default status values. Edit the existing field rather than creating a second Status field. Confirm that the options above are present and ordered as shown.

## Fields and agreed options

Create or reuse these fields on the existing project:

| Field | GitHub field type | Values / usage |
|---|---|---|
| Priority | Single select | `P0 - Urgent`, `P1 - High`, `P2 - Normal`, `P3 - Low`. Use P0 only for a blocker or critical issue. |
| Iteration | Iteration | Use the Project's native Iteration field. Agree a consistent iteration length and dates with the team; do not invent iteration dates in issues. Put work without an agreed iteration in the backlog. |
| Estimate | Number | Relative effort in points: `1`, `2`, `3`, `5`, `8`. Leave blank until the team can estimate; use 8 as a signal to consider splitting the work. |
| Area | Single select | `Planning`, `Database`, `Backend`, `Frontend`, `QA`, `Documentation`. Choose the main area responsible for delivery. |
| Requirement | Text | Requirement ID(s), e.g. `FR-01` or `NFR-03`; use a comma-separated list when needed. Leave blank if the work has no identified requirement yet and clarify it before marking Ready when traceability is required. |

If similarly named fields already exist, reuse and adjust them instead of adding duplicates. These are the team's recommended values; confirm them with the team and then keep them consistent.

## Recommended views

Create or adjust these views on `planificacion`:

### Backlog (Table)

- Layout: **Table**
- Filter: `Status is Backlog OR Status is Ready`
- Group by: **Priority** (or sort by Priority, then Estimate)
- Show at least: Title, Status, Priority, Area, Iteration, Estimate, Assignees, Requirement
- Purpose: refine, prioritize, estimate, and schedule upcoming work.

### Kanban

- Layout: **Board**
- Group by: **Status**
- Columns: Backlog, Ready, In Progress, Review, QA, Done
- Show card fields: Priority, Area, Iteration, Estimate, Assignees
- Purpose: visualize active work and move cards as work progresses.

Optional saved filters can be added for a particular area or iteration. Keep the Backlog and Kanban views in the existing project; do not create another Project just to get a different view.

## Adding Issues and pull requests

### Manual procedure

Use this procedure whenever automatic item addition is not enabled or is unavailable:

1. Open the existing `planificacion` project.
2. In a project view, select **Add item** (or the equivalent control).
3. Search for the repository Issue or pull request by title or number.
4. Select the result to add it to the project.
5. Set Status, Priority, Area, Iteration, Estimate, and Requirement when known.
6. Confirm that the item appears in the expected view.

Issues and pull requests can both be tracked as Project items. When a PR implements an Issue, link them in the PR description (for example, `Closes #123`) as well as adding the work to the Project when needed.

### Automatic addition

The repository connector cannot inspect the Project's current workflows, so automatic addition has **not been verified**. Check the Project's **Workflows** settings for an **Auto-add to project** workflow tied to this repository. If available, configure it to add newly opened Issues from this repository; decide separately whether pull requests should also be added. Test with a new Issue and verify it appears. If the workflow is unavailable or fails, continue using the manual procedure above and document that automatic addition is not enabled.

## Updating work and keeping the board healthy

- **Backlog → Ready:** the objective, acceptance criteria, responsible area, and important dependencies are clear.
- **Ready → In Progress:** a team member starts work; assign an owner.
- **In Progress → Review:** implementation is ready and a PR is open.
- **Review → QA:** requested review changes are addressed and review is complete.
- **QA → Done:** verification passes and acceptance criteria are met; merge the PR when applicable.
- If QA finds a defect, return the item to In Progress and describe what needs fixing.
- Reopen or move an item back from Done if the result no longer meets its acceptance criteria.

At least once per work session, update the Status and assignee of active items. Keep titles actionable, avoid duplicate items, and link related issues and PRs. Do not mark an item Done only because a PR was opened.

## Filtering

Use the view's filter controls to narrow work by:

- **Area:** e.g. `Frontend` or `Backend`.
- **Priority:** e.g. `P0 - Urgent` or `P1 - High`.
- **Iteration:** select the current iteration.
- Combine filters when useful, such as `Area = Backend` and `Priority = P1 - High`.

If the field is not visible in the view, add it through the view's field/column settings first.

## Verification checklist

The Project configuration is complete only after a team member verifies the following in GitHub:

- [ ] The existing `planificacion` Project URL is recorded and the administrator is confirmed in **Manage access**.
- [ ] Status contains the six agreed options in the stated order.
- [ ] Priority, Iteration, Estimate, Area, and Requirement fields exist with agreed types and options.
- [ ] A Backlog table view and a Status-grouped Kanban view are available.
- [ ] A test Issue is added and visible in the Project with its Status and Area set.
- [ ] Automatic addition is tested; if unavailable, the team follows the manual procedure.
- [ ] The team knows to update status as work moves through review and QA.

**Current verification note:** this guide documents the intended configuration and a reproducible workflow. The connected repository tools do not expose Project settings, view definitions, access lists, or workflow automation, so the live Project configuration and test-item acceptance criteria must be confirmed in the GitHub Projects UI.
