# Development Workflow

## Issue lifecycle

Use the existing GitHub Project status values:

**Backlog → Ready → In Progress → Review → QA → Done**

- **Backlog:** captured but not yet ready to start.
- **Ready:** Definition of Ready is satisfied.
- **In Progress:** implementation or documentation work is active.
- **Review:** a pull request is open and awaiting peer review.
- **QA:** acceptance criteria and relevant behavior are being verified.
- **Done:** Definition of Done is satisfied and the change is integrated.

Move an issue back to an earlier status if review or QA discovers work that must be corrected. Keep status synchronized with the actual PR and verification state.

## Branches and commits

- Create a focused branch from the current target branch for each coherent task or small related group.
- Use descriptive names such as docs/e0-06-domain-glossary or feature/program-assignment.
- Keep commits focused and describe the change in imperative, specific language.
- Do not commit secrets, local environment files, build output, or unrelated changes.

## Pull requests

1. Link the PR to its issue(s) using GitHub keywords such as Closes #9 when the PR fully satisfies that issue.
2. Describe the purpose, main changes, tests/verification, and limitations.
3. Keep the diff reviewable and request a relevant peer reviewer.
4. Address review feedback and keep issue/Project status accurate.
5. Merge only after required checks and review policies are satisfied.

## Testing and evidence

Choose verification appropriate to the change: unit tests for domain rules, use-case tests for application behavior, integration tests for database/API boundaries, and UI tests for frontend behavior. Documentation changes should be checked for accurate paths, consistent terminology, and renderable Mermaid syntax. If a test cannot be run or is not applicable, explain why.

## Definition of Ready and Done

Use Definition of Ready before moving work into Ready, and Definition of Done before closing an issue. An issue should not be closed merely because a branch or draft PR exists.
