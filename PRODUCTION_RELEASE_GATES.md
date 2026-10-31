# Geminio OS — Production Release Gates

This checklist is an evidence register, not a claim that the repository currently passes.

## Gate 0 — Repository integrity
- [ ] Documented runtime versions and lockfiles are committed.
- [ ] One supported install/build command works from a clean clone.
- [ ] No secrets, personal access tokens, hard-coded admin passwords, or live credentials in Git history.
- [ ] Existing CHIXUS edge-control modules are separated from Geminio OS product modules.
- [ ] Architecture docs match actual routes, services, and database migrations.

## Gate 1 — Identity and account security
- [ ] Sign-up, verification, sign-in, password reset and sign-out are implemented.
- [ ] Passwords use Argon2id/scrypt; session cookies are Secure, HttpOnly and SameSite.
- [ ] CSRF, CORS, session rotation, expiry, revocation and brute-force controls are tested.
- [ ] MFA and recovery flow are tested.
- [ ] User enumeration is prevented.
- [ ] Object-level authorization and workspace isolation have negative tests.

## Gate 2 — Product workflows
- [ ] Project CRUD, template creation, files, version history and activity work end-to-end.
- [ ] AI plan, approval, execution, cancellation, diff review and test report work end-to-end.
- [ ] User code runs only in hardened ephemeral sandbox.
- [ ] AI budget/credits are estimated, reserved and settled atomically.
- [ ] Provider outage, rate limit, timeout, cancellation and fallback behavior are tested.

## Gate 3 — Money and integrations
- [ ] Payment initialization is server-side and amount is derived from server pricing.
- [ ] Webhook verifies signature against raw body and rejects invalid/replayed events.
- [ ] Idempotency covers duplicate and out-of-order events.
- [ ] Double-entry ledger constraints and reconciliation reports pass.
- [ ] Refund, reversal, chargeback and failed settlement are tested.
- [ ] Provider secrets are write-only and rotated; never shipped in web/mobile bundles.

## Gate 4 — Quality, reliability and privacy
- [ ] Unit, integration, end-to-end and contract tests pass in CI.
- [ ] Accessibility audit includes keyboard and screen reader checks.
- [ ] Load/soak tests, queue recovery, DB restore and disaster recovery pass.
- [ ] Logs/metrics/traces and actionable alerts are configured.
- [ ] Export, deletion, retention, consent and incident-response processes are approved.
- [ ] Dependency, secret, container and static-analysis scans are clean.

## Gate 5 — Launch
- [ ] Staging acceptance by product owner and test users.
- [ ] Rollback, feature kill switches and on-call ownership are documented.
- [ ] Provider test-mode evidence and payment reconciliation are reviewed.
- [ ] Legal terms/privacy and support channels are live.
- [ ] Production domain, TLS, backups, monitoring and incident contacts are configured.
- [ ] Release manager records go/no-go decision.

## Known repository risks to resolve before launch
- The current repository includes legacy CHIXUS backend files that contain a hard-coded privileged credential string. Treat it as compromised: remove it from source and rotate/revoke the credential. If it was ever used outside a local demo, investigate access logs and exposure. Do not copy the value into new configuration.
- Root README is currently minimal and there is no confirmed dependency manifest/lockfile at repository root in the inspected branch.
- Existing backend files use SQLite/FastAPI patterns while Phase 2 server files use TypeScript/Drizzle/Redis/BullMQ patterns. Choose and document one primary API/runtime boundary or define a deliberate service split; do not run two competing wallet/auth authorities.
- Existing connected wallet UI includes demo-style interaction boundaries. Do not treat UI state as payment settlement.
- Previous Phase 2 code depends on modules/routes and infrastructure that have not yet been verified as present or tested.
- No production build, CI test suite, security assessment, staging deployment, or live provider test has been evidenced in this branch.

## Release status
**NOT CERTIFIED FOR PRODUCTION.** A production release requires evidence for every applicable gate above. Do not switch on live payment keys or expose arbitrary code execution before independent security review.
