# Geminio OS — Production Readiness Gates

**Release status: NOT CERTIFIED FOR PRODUCTION.** Mark an item complete only with evidence such as a CI run, test report, deployment record or signed operational review.

## Repository and build
- [ ] One declared application architecture and supported runtime.
- [ ] Package manifests and lockfiles; reproducible clean install.
- [ ] Build, lint, format, type-check and test commands documented.
- [ ] CI on every pull request and protected branch.
- [ ] No unresolved compiler/type errors or dependency conflicts.
- [ ] Routes and navigation covered by tests.
- [ ] No duplicate app roots or mixed legacy product identities.

## Identity and access
- [ ] Email verification and secure password reset.
- [ ] MFA/passkey enrollment and recovery.
- [ ] Session rotation, expiry, revocation and device management.
- [ ] Server-side authorization on every resource operation.
- [ ] Workspace/tenant isolation tests.
- [ ] Brute-force protection and suspicious-login notifications.
- [ ] No hard-coded passkeys, tokens, credentials or default admin passwords.

## Data and privacy
- [ ] PostgreSQL migrations tested from an empty database.
- [ ] Foreign keys, unique constraints, tenant ownership and indexes.
- [ ] Encryption in transit and at rest.
- [ ] Private object storage, expiring signed URLs and upload scanning.
- [ ] Export, deletion, retention and consent flows tested.
- [ ] Backup restoration drill and approved recovery objectives.
- [ ] Logs redact tokens, prompts, personal data and payment details.

## AI and execution
- [ ] Provider adapter and server-side secrets only.
- [ ] Quotas, budgets, model allowlist and abuse controls.
- [ ] Prompt injection and untrusted attachment handling.
- [ ] Output schema validation and safe rendering.
- [ ] Durable queue, idempotent lifecycle, retries and dead-letter queue.
- [ ] Build event persistence, authenticated stream and reconnect support.
- [ ] Sandbox isolation reviewed and image scanned.
- [ ] CPU, memory, disk, process, time and output caps tested.
- [ ] Network egress and secret isolation tested.
- [ ] Generated diffs require human review before merge/deploy.

## Payments and wallet
- [ ] Server-side price catalog and payment intent creation.
- [ ] Raw-body webhook signature verification.
- [ ] Unique provider event/reference constraints.
- [ ] Pending intent amount, currency, customer and status verification.
- [ ] Balanced immutable ledger transactions.
- [ ] Duplicate, out-of-order and retry webhook tests.
- [ ] Reconciliation job and mismatch queue.
- [ ] Refund/reversal and dispute procedures.
- [ ] Paystack test-mode evidence before live mode.
- [ ] No client balance mutation or redirect-trusted payment success.

## UX and quality
- [ ] All screens in the UX spec implemented or explicitly excluded from launch.
- [ ] Every button/menu action has a tested destination/result.
- [ ] Loading, empty, offline, error, retry and permission-denied states.
- [ ] Mobile/tablet/desktop QA.
- [ ] WCAG 2.2 AA audit.
- [ ] Keyboard-only and screen-reader testing.
- [ ] Supported-device performance and crash testing.
- [ ] Browser and native end-to-end flows.

## Operations and release
- [ ] Production environment and secret manager configured.
- [ ] TLS, domain, CORS, CSP and security headers reviewed.
- [ ] Monitoring, tracing, alerting and on-call ownership.
- [ ] Incident response, customer communication and escalation runbooks.
- [ ] Load, soak and failure-injection tests.
- [ ] Dependency, SAST, secret and container scanning.
- [ ] Penetration test and critical/high remediation.
- [ ] Rollback and disaster recovery rehearsed.
- [ ] Privacy/legal/compliance review signed off.
- [ ] Release owner signs exact commit and deployment artifact.

## Repository observations from the inspected branch
- The repo contains a small Expo/React Native app folder with three connected example screens, a separate Python FastAPI backend, a standalone HTML dashboard, TypeScript backend building blocks, tests and PDFs.
- The Python health/ledger modules identify themselves as CHIXUS edge-control services. They must not be treated as Geminio OS user-facing APIs without architecture reconciliation and security review.
- Root index.html is a personal portfolio page, not the Geminio OS application shell; it must not be overwritten as the product UI.
- The wallet/credits/AI Builder screens contain placeholder behavior and refer to tRPC modules not visible in the inspected repository tree.
- The Paystack webhook imports a settlement module not present in the inspected tree. Do not enable live wallet crediting until settlement and reconciliation are implemented and tested.
- The inspected tree did not expose a root package manifest, Expo app configuration, complete route tree or verified deployable app entry point.

## Release decision
Until applicable checks have evidence, status remains **design/integration in progress**. Do not advertise a production launch or process live customer funds.
