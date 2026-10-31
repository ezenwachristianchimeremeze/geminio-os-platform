# Security Remediation Note — Credential Exposure

## Finding
A repository review found legacy edge-control administrator and operator credentials embedded in source comments, Python authentication checks, test fixtures and dashboard defaults. This branch removes those literals from the current branch contents, requires the administrator secret to be supplied through the CHIXUS_ADMIN_PASSKEY environment variable, uses constant-time comparison for the protected health/ledger checks, replaces test values with clearly test-only defaults, and stops the dashboard from persisting operator credentials in browser localStorage.

## Required owner actions — do these immediately
1. Treat every credential that was committed as compromised, even if it was intended only for local use.
2. Rotate/revoke the administrator passkey and operator/access token in the real deployment and any related systems.
3. Set a new unique CHIXUS_ADMIN_PASSKEY through the server's secret manager or protected environment configuration. Do not commit the value.
4. Remove any old credentials from deployment variables, Termux shell history, CI variables and password managers where appropriate.
5. Review access logs for unexpected use during the exposure window.
6. If repository history has been shared or is public, arrange a coordinated history rewrite to purge the old literals from all reachable refs, forks, cached clones and releases. A normal source-file edit does not erase prior Git commits. Coordinate this carefully because history rewriting changes commit IDs and disrupts collaborators.
7. Do not re-use any exposed value.

## Verification still required
- Run the Python test suite and add tests for missing/incorrect/correct environment credentials.
- Confirm no production deployment is relying on the removed default.
- Review dashboard transport: credentials are still sent to the configured API endpoint; use HTTPS outside local development and a properly secured operator session.
- Run secret scanning over all branches, tags, commit history and release artifacts.
- The changes here are a remediation step, not a security certification.
