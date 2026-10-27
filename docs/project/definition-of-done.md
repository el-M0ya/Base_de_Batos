# Definition of Done (DoD)

An issue is **Done** only when the agreed outcome is implemented, verified, reviewed, and integrated. A locally complete change is not sufficient.

## Checklist

- [ ] All acceptance criteria are met, or an exception is explicitly agreed and recorded.
- [ ] Relevant automated tests are added or updated and pass.
- [ ] Manual verification is recorded when automated tests are not appropriate.
- [ ] Changes are reviewed by someone other than the author, according to repository rules.
- [ ] The change is integrated into the intended base branch through the normal pull-request process.
- [ ] Documentation, API contracts, SQL scripts, and diagrams are updated where affected.
- [ ] No secrets, credentials, unsafe SQL concatenation, or unrelated generated artifacts are introduced.
- [ ] Known limitations and follow-up work are recorded in linked issues.

For documentation-only work, verification may include checking links and paths, rendering Mermaid diagrams, reviewing consistency with code/requirements, and confirming the files are present in the PR. Explain any test marked not applicable.
