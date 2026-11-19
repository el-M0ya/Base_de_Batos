## Summary

Implements trainer-to-training-program authorization management, with separate generation and validation permissions and a defined validity period.

## Changes

- Adds API operations to create, retrieve, filter, update, and delete authorizations.
- Persists authorizations in `authorises` and reports duplicate trainer-program pairs as conflicts.
- Checks generation or validation permissions for a specific program and date.
- Derives room-chief capability from `can_validate` without adding a persisted role.
- Adds unit tests for combined permissions and authorization validity dates.

## Verification

- [x] `python -m unittest tests.unit.domain.test_authorisation -v` (7 tests pass)
- [x] `git diff --check`
- [ ] Full test suite: not run; `psycopg`, required to import the integration tests, is not installed in this environment.

## Related issue

Closes #112

## Review notes

- Authorization checks are available through the API; routine generation and validation flows are not yet implemented in the application.
- Review administrative authorization when authentication is integrated; this currently follows the temporary pattern used by site management.
