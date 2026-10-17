# Contributing Guide

This guide defines a simple workflow for team contributions. If a convention is not automated by GitHub, contributors must follow it manually.

## 1. Before You Start

1. Look for an existing issue or create one using the appropriate template: **Feature Request**, **Bug Report**, or **Technical Task**.
2. Make sure the objective, acceptance criteria, and related requirements are clear.
3. Avoid duplicate work. If the scope changes significantly, update the issue before proceeding.

## 2. Branch Naming

Create one branch per issue and avoid working directly on `main`. Use short, descriptive branch names:

- `feature/<number>-<summary>`: new functionality.
- `fix/<number>-<summary>`: bug fixes.
- `task/<number>-<summary>`: technical or documentation tasks.
- `chore/<number>-<summary>`: repository configuration and maintenance.

Examples: `feature/24-training-plan`, `fix/31-form-validation`, `task/18-document-api`.

Use lowercase letters, hyphens, and the issue number when one exists.

## 3. Commit Messages

Use concise commit messages with a prefix that describes the intent of the change:

- `feat: add training plan generation`
- `fix: correct exercise validation`
- `docs: update installation instructions`
- `test: cover duration calculation`
- `refactor: simplify planning service`
- `chore: configure GitHub templates`

Include the issue number when it adds clarity, for example: `docs: document installation (#24)`. Each commit should represent one coherent change. Avoid vague messages such as `changes`, `fixes`, or `final`.

## 4. Pull Requests and Reviews

1. Open a Pull Request from your branch into `main`.
2. Complete the PR template: goal, related issue, changes, tests, and verification steps.
3. Link the issue using `Closes #N` when the PR completes it; use `Relates to #N` if it is only related.
4. Request a review from the person responsible for the relevant area. Check `.github/CODEOWNERS` to identify area owners.
5. Distribute reviews manually using this rotation:
   - **Frontend:** Bryan (@el-M0ya) and Fabio (@Fabio-Pilot), alternating on each PR.
   - **Backend:** Cuervo (@AlexCuervo), Hector (@HectorDuarte911), and Gabriel (@GaboPS1016), following that order.
   - **Database:** Gabriel (@GaboPS1016).
   - **QA and documentation:** Alejandro (@Kaik0405).
6. Address review comments, make the necessary changes, and wait for the approvals required by repository rules before merging.

CODEOWNERS can help request reviews, but it does not automatically rotate reviewers. Approval requirements depend on the protection rules configured for `main`.

## 5. Testing and Quality

- Run the tests relevant to your change and record their results in the PR.
- If you cannot run a test, say so and explain why; do not claim that it passed.
- Manually verify UI changes or workflows when appropriate.
- Update affected documentation and examples.
- Do not commit passwords, tokens, private keys, sensitive personal data, or local configuration files containing secrets.

## 6. Definition of Done

A task is ready for review when it meets its acceptance criteria, includes test results or an explanation of pending tests, and has the necessary documentation updates. It is complete when the changes have been reviewed and merged and the issue has been updated or closed as appropriate.

## 7. Keeping This Guide Useful

If the team agrees to change branch naming, commit conventions, or the review workflow, update this document and communicate the change. Keep the rules simple and realistic for the team's size.
