# Geminio OS — End-to-End Product & System Architecture

**Document status:** implementation baseline / review required  
**Product:** Geminio OS — AI-first development and productivity ecosystem  
**Repository:** `ezenwachristianchimeremeze/geminio-os-platform`

## 1. Product definition

Geminio OS is a secure, AI-assisted workspace for planning, building, testing, documenting, and operating software projects. It is an application platform, not a replacement for a device operating system. Its core promise is one traceable workflow from a project idea to a reviewed, tested, deployable artifact.

### Product principles
1. **Human approval at consequential boundaries:** review before publishing, deploying, spending credits, deleting data, or changing account security.
2. **No fake integrations:** every integration shows Connected, Needs setup, Degraded, or Demo. A mock response is never represented as a live provider response.
3. **Secure by default:** server-only secrets, tenant isolation, least privilege, audit trails, rate limits, and safe execution sandboxes.
4. **Explainable AI actions:** show plan, files changed, tools invoked, tests, cost estimate, and approval points.
5. **Resilient UX:** loading, empty, offline, permission-denied, retry, and partial-failure states are first-class.
6. **Accessible and responsive:** keyboard support, screen-reader labels, sufficient contrast, reduced motion, and mobile/tablet/desktop layouts.

## 2. Information architecture

### Public / identity
- Brand splash and logo animation
- Welcome / product overview
- Sign in
- Create account
- Email verification
- Forgot password
- Reset password
- Terms, privacy, cookie preferences
- Status / service availability

### Authenticated workspace
- Home / Overview
- Discovery / Templates / Marketplace
- Projects
- Project overview
- AI Builder
- AI Chat / Assistant
- Code workspace
- File manager
- Preview and test results
- Deployments
- Documentation
- Integrations
- Notifications / Activity
- Wallet / Credits / Billing history
- Profile and preferences
- Security and sessions
- Help and feedback

### Administration (role-gated)
- Admin overview
- User and organization management
- Roles and permissions
- Plans, usage and credit policy
- Provider/integration health
- Payment reconciliation
- Audit events
- Feature flags
- Incident and support tools

## 3. Global navigation and responsive behavior

### Desktop
- Left rail: logo, Home, Discover, Projects, AI Builder, Chat, Files, Deployments, Integrations, Wallet, Settings.
- Main header: breadcrumb, global search, command palette, help, notifications, workspace switcher, avatar.
- Content area: 12-column responsive grid; persistent project context where relevant.
- Right inspector (contextual): AI task details, file metadata, run logs, or settings. Collapses to a drawer.

### Tablet
- Collapsible 72 px icon rail; labels appear on selection/hover.
- Header retains workspace switcher, search, notifications, profile.
- Right inspector becomes a slide-over drawer.
- Two-column cards collapse to one column at narrow tablet widths.

### Mobile
- Top bar: logo/active workspace and avatar.
- Bottom navigation: Home, Discover, Build, Projects, More.
- More opens a full-height sheet containing Chat, Files, Deployments, Integrations, Wallet, Notifications, Settings, Help.
- Primary action is a full-width bottom CTA only when the screen has one clear primary action; otherwise actions remain contextual.
- Forms use one-column layouts; tables become cards; destructive actions remain in confirmation dialogs.

### Navigation rules
- Preserve the previous screen and scroll position when returning from detail views.
- Deep links open the correct workspace/project after authentication.
- If access is denied, show an explanation and request-access path; never silently redirect to an unrelated screen.
- Unsaved changes trigger a leave-confirmation dialog.
- Browser back returns to the previous in-app location when possible.

## 4. End-to-end screen inventory and interaction contracts

Each screen must define: purpose, entry point, visible controls, action result, loading state, empty state, error state, and permission requirements.

### A. Brand and account journey
1. **Splash / logo:** Geminio symbol, wordmark, subtle progress indicator. Resolve session and app configuration. Route to Welcome or Home; on failure show Retry and Status.
2. **Welcome:** concise product value, Sign in, Create account, Explore demo. Demo is visibly labelled and cannot access private data.
3. **Sign in:** email, password, show/hide password, remember-device choice, submit, forgot password, create account. Success routes to Home; invalid credentials show field-safe error; throttling shows retry time.
4. **Create account:** name, email, password, confirm password, terms acceptance. Validate inline; create pending account; route to verification.
5. **Verify email:** masked destination, resend with cooldown, change email. Verified users proceed to onboarding.
6. **Forgot password:** email entry; always use a non-enumerating response; show check-email state.
7. **Reset password:** token validation, new password, confirmation, revoke other sessions option; success routes to Sign in.
8. **Onboarding:** role/use case, skill level, preferred stack, workspace name, optional invite. Skip is allowed; preferences are editable later.
9. **Workspace setup:** create personal/team workspace, invite members, select starter template. Show progress and retryable failures.

### B. Daily workspace
10. **Home / Overview:** welcome, recent projects, continue task, usage/credits, activity, quick actions. Quick actions open Create Project, AI Chat, AI Builder, or Import.
11. **Global Search / Command Palette:** search projects/files/docs/commands. Arrow keys move, Enter opens, Esc closes. Search is scoped to the active workspace and permission-filtered.
12. **Discovery:** curated templates, starter kits, integrations, learning resources. Filter/search/sort; selecting a card opens detail, Preview, or Use Template.
13. **Template Detail:** description, stack, requirements, screenshots, estimated usage, permissions. Use Template creates a draft project after confirmation.
14. **Projects List:** grid/list toggle, search, filters, sort, create/import, archive. Project card opens Project Overview; overflow menu contains rename, duplicate, archive.
15. **Create Project:** name, description, stack, template, visibility. Create draft, then open project overview. Validate slug uniqueness server-side.
16. **Project Overview:** status, activity, branches, tasks, files, latest test/deploy, AI Builder entry. Tabs preserve context.
17. **AI Builder:** goal prompt, requirements, context/files, stack, plan, estimate, Generate. Generated changes are proposed in a reviewable change set; user can accept/reject individual files. No silent production deployment.
18. **AI Chat:** conversation list, new chat, model/provider status, message composer, attachments, voice controls when supported, regenerate, copy, feedback. Tool actions show confirmation and results.
19. **Code Workspace:** file tree, editor, diff, diagnostics, terminal/task output. Save creates a versioned change; run executes in isolated sandbox; commit requires review.
20. **File Manager:** upload, new folder, rename, move, download, delete. Enforce workspace quotas and type/size scanning; deletion uses confirmation and recovery policy.
21. **Preview:** isolated preview URL, device viewport switcher, refresh, console/network diagnostics. Never expose preview secrets or internal service addresses.
22. **Testing & Quality:** test suites, lint, type-check, coverage, accessibility checks. Each run shows commit, environment, duration, logs, and downloadable report.
23. **Documentation:** generated README/API/architecture/release notes. AI drafts remain editable and require approval before publishing.
24. **Deployments:** environments, deployment history, logs, health, rollback. Deploy requires permission, environment selection, change summary, and explicit confirmation.
25. **Activity / Notifications:** filter by project/type/unread; notification click opens the relevant resource; mark read/archive.
26. **Integrations:** provider catalog, connection state, scopes, last sync, disconnect. OAuth tokens remain server-side; disconnect revokes credentials where provider supports it.
27. **Wallet:** balance, ledger, add credits, transaction history. Balance is server-calculated from immutable ledger; no client-side balance mutation.
28. **Credits & Plans:** plan comparison, included usage, top-up, invoices. Show final price, currency, taxes/fees where applicable, and payment status before checkout.
29. **Profile:** name, avatar, email, locale, time zone. Email changes require verification.
30. **Preferences:** theme, density, editor, notifications, accessibility, language. Persist per user; provide reset-to-default.
31. **Security:** password change, MFA, active sessions, sign-out other sessions, recovery methods. Sensitive changes require re-authentication.
32. **Help & Feedback:** search docs, contact support, submit diagnostics with explicit consent, feedback status.
33. **Terms / Privacy:** versioned legal documents, effective date, acceptance record, export/privacy request paths.
34. **Offline / Degraded:** clear offline banner, cached read-only resources, retry queue for safe drafts, sync conflict resolution. Never queue financial or destructive actions for blind replay.

### C. Administration
35. **Admin Overview:** service health, queue, active users, spend, incidents; only aggregate metrics by default.
36. **User Directory:** search, status, role, workspace, suspend/reactivate with reason and audit event.
37. **Workspace & Access:** membership, invitations, role matrix, ownership transfer with confirmation.
38. **Plans & Usage:** plan definitions, limits, usage policy, effective dates; changes require privileged approval and audit.
39. **Provider Health:** provider status, latency, failures, configured/not configured. Secret values are write-only and never retrievable.
40. **Payment Operations:** verified webhook events, idempotency, settlement state, refunds/reconciliation. No manual balance edit; adjustments use audited ledger entries.
41. **Audit Log:** actor, action, target, timestamp, request ID, outcome; tamper-resistant retention policy.
42. **Feature Flags:** scoped rollout, percentage, allowlist, kill switch; every change audited.
43. **Support / Incidents:** severity, owner, timeline, customer impact, runbook, post-incident review.

## 5. Core journeys

### First-time user
Splash → Welcome → Create Account → Verify Email → Onboarding → Workspace Setup → Home → Create Project → Project Overview → AI Builder → Review Plan → Generate → Review Diff → Run Tests → Preview → Approve Deployment.

### Returning user
Splash → session validation → Home → recent project → resume task. Expired sessions return to Sign in with a safe return URL.

### Add credits
Wallet → Add Credits → choose amount → server creates payment intent → provider checkout → signed webhook → idempotent ledger credit → Wallet refresh. Browser redirect alone never credits the wallet.

### AI build
Prompt → requirements clarification → plan → cost/permission estimate → approval → queued job → isolated execution → incremental logs → tests → diff review → accept/reject → versioned save. Deployment is a separate approval.

## 6. Reference system architecture

### Client
- Web: accessible React application, typed API client, route guards, design tokens, error boundary.
- Mobile: Expo/React Native client sharing API contracts and design tokens.
- State: server state cache plus minimal local UI state; avoid duplicating authoritative wallet/auth data.
- Offline: encrypted/limited local cache; queue only idempotent safe draft operations.

### API and services
- API gateway / BFF: request IDs, schema validation, auth, authorization, rate limits.
- Identity: verified email, secure session cookies or short-lived access tokens plus rotating refresh tokens, MFA, session revocation.
- Workspace: tenancy, membership, roles and invitations.
- Projects: metadata, versioning, source artifact references.
- AI orchestration: provider routing, budgets, retries, cancellation, tool permissions, prompt-injection boundaries.
- Job queue: durable jobs, deduplication, leases, retries, dead-letter queue.
- Sandbox: ephemeral isolated containers/VMs, no default network, resource limits, artifact scanning.
- Files: object storage, signed URLs, malware scanning, retention.
- Billing: payment provider adapter, signed webhook verification, immutable double-entry ledger.
- Notifications: in-app/email/push delivery with preferences.
- Audit: append-only security and business events.

### Data layer
- PostgreSQL as source of truth.
- Redis for rate limits, ephemeral cache, job coordination only.
- Object storage for user artifacts; metadata in PostgreSQL.
- Migrations are versioned, reviewed, reversible where possible.
- Tenant-owned tables include workspace/tenant key and composite constraints; authorization is enforced server-side.

## 7. Security baseline
- Never commit API keys, passwords, signing secrets, personal access tokens, or production data.
- Rotate any credential that has ever appeared in source code, logs, screenshots, or documentation.
- Password hashing: Argon2id or scrypt with reviewed parameters; never reversible encryption.
- CSRF protection for cookie-authenticated mutations; secure, HttpOnly, SameSite cookies.
- Strict CORS allowlist; CSP; HSTS; secure headers; request body and upload limits.
- Object-level authorization on every resource read/write.
- Parameterized SQL; schema validation; output encoding.
- Webhook signature validation over raw body, timestamp/replay checks, idempotency.
- Rate limits by IP, account, workspace, and operation cost.
- Audit admin, billing, auth, key, export, deletion, and deployment actions.
- Backups encrypted and restore-tested; defined RPO/RTO.
- Sandbox isolation, no Docker socket exposure, no privileged containers, egress allowlist, resource quotas.
- Dependency, secret, container, and static analysis scans in CI.

## 8. Reliability and operations
- Structured logs with request/job IDs; redact tokens, prompts with secrets, and personal data.
- Metrics: latency, error rate, queue age, provider failures, payment reconciliation, sandbox exits.
- Traces across API → queue → worker → provider.
- Health endpoints distinguish liveness from readiness.
- Retries use exponential backoff + jitter and bounded attempts; dead-letter review process.
- Feature flags and kill switches for AI generation, payments, deployments, and integrations.
- Runbooks for provider outage, payment mismatch, queue backlog, data restore, credential rotation, and security incident.
- Staged rollout: local → CI → staging → limited pilot → production; rollback plan for each release.

## 9. Production exit criteria (must be evidenced)
- Clean install from documented lockfile on supported Node/Python versions.
- CI passes lint, format, type checks, unit/integration/e2e tests, accessibility, dependency and secret scans.
- Database migrations apply to empty and previous-version databases; backup restore verified.
- Tenant isolation and role-based authorization tests pass.
- Auth, MFA, session expiry/revocation, CSRF and abuse tests pass.
- AI provider failure, timeout, cancellation, budget enforcement and prompt injection tests pass.
- Sandbox escape/egress/resource exhaustion tests pass in a hardened environment.
- Payment signature, replay, duplicate, out-of-order, refund and reconciliation tests pass in provider test mode.
- Load, soak, disaster recovery, monitoring and alerting exercises pass.
- Legal, privacy, support, incident, retention, deletion and export workflows approved.
- Product owner signs off on staging acceptance and production launch.

**Status:** This document defines the target architecture. It does not assert that these controls or integrations are already deployed.
