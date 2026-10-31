# Security Policy

## Reporting a vulnerability
Do not open a public issue containing exploit details, credentials, personal data, or payment information. Contact the repository maintainer privately through the GitHub profile and include the affected commit/component, impact, safe reproduction steps, and sanitized logs.

## Credential exposure response
1. Revoke or rotate the credential immediately at the issuing provider.
2. Review provider and application audit logs for unauthorized use.
3. Replace it with a server-side environment secret.
4. Remove it from current source and add secret scanning to CI.
5. Decide whether Git history must be rewritten. A source edit does not erase prior commits, forks, caches, or clones.
6. Re-deploy affected services and verify the old credential no longer works.

## Security expectations
- Least-privilege authorization and workspace-level object access checks.
- Secure sessions, CSRF defenses where cookie auth is used, strict CORS and security headers.
- Server-side secret storage; no credentials in browser storage or mobile bundles.
- Validated webhook signatures, replay protection and idempotent settlement.
- Isolated, resource-limited execution for untrusted project code.
- Dependency and secret scanning, audit logs, backups and tested recovery.

Security issues are release blockers until assessed and mitigated.
