# Geminio OS — Master Product and Technical Architecture

**Status:** Design baseline; implementation and release certification remain in progress.  
**Product:** AI-first software creation and productivity workspace.  
**Clients:** Responsive web first, installable PWA, then native iOS/Android clients after API and design-system stabilization.

> This document describes the target architecture. It does not claim that every described module currently exists in the repository or is production-ready.

## 1. Product principles
1. One workspace for projects, files, AI conversations, builds, deployments, collaboration, automation and billing.
2. Progressive disclosure: guided first-use experience, efficient expert workflows.
3. Human approval for consequential actions: deployment, deletion, payment, access and external side effects.
4. Safe-by-default AI: generated code is untrusted; secrets never enter client bundles; execution uses isolated sandboxes.
5. Transparent state: asynchronous actions expose status, timestamp, retry and useful error.
6. Accessible and responsive: keyboard, screen reader, reduced motion, contrast and touch targets are first-class.
7. No fake integrations: demos are labelled; unavailable services show setup states.
8. Data portability: export, deletion, retention and account recovery are designed in.

## 2. Information architecture
Global shell: brand/workspace switcher; global search/command palette; Create; notifications/activity; help/docs; profile/security/sign out.

Primary navigation: Home, Discover, Projects, AI Chat, AI Builder, Files, Automations, Integrations, Deployments, Analytics, Wallet & Credits, Team, Settings. Admin Console is role-gated.

Mobile bottom tabs: Home, Discover, Projects, AI, More. More is a bottom sheet for Files, Automations, Integrations, Deployments, Analytics, Wallet, Team, Settings and Help. Tablet uses collapsible rail or drawer. Desktop uses sidebar and optional contextual inspector.

## 3. Complete screen catalogue
### Public and identity
- S00 Splash/Boot: brand, version, session restore, maintenance/update state.
- S01 Welcome: value proposition, Sign in, Create account, read-only demo.
- S02 Sign up: name, email, password, terms/privacy acknowledgement.
- S03 Verify email: masked address, resend cooldown, change email.
- S04 Sign in: credentials, optional passkey, recovery link.
- S05 MFA: authenticator/passkey, recovery code, rate limits.
- S06 Forgot password: privacy-preserving request.
- S07 Reset password: single-use expiring token, revoke sessions.
- S08 Profile setup: name, avatar, locale, timezone, accessibility.
- S09 Workspace setup: create workspace or join invitation.
- S10 Onboarding: first project, Discover, AI Chat, security, invite.
- S11 Invitation acceptance: inviter, workspace, role and expiry.

### Core workspace
- S12 Home: quick actions, recent projects/activity, build/deploy health, usage, onboarding.
- S13 Discover: search and categories for tools, templates, integrations, workflows and learning.
- S14 Discovery detail: preview, compatibility, permissions, pricing, changelog, Add/Launch.
- S15 Global search: grouped authorized results.
- S16 Notifications: unread, mentions, builds, billing and security.
- S17 Activity feed: actor/action/resource/time.
- S18 Help centre: docs, troubleshooting and support.

### Projects and development
- S19 Projects list: grid/list, filters, sort, create/import.
- S20 Create project: blank/template/import, name, visibility, stack and review.
- S21 Template gallery: categories, preview, version and compatibility.
- S22 Repository import: provider OAuth, repo/branch picker, import progress.
- S23 Project overview: status, environment, files, builds, tests, deployments.
- S24 Project settings: repository, visibility, access, environment, archive/delete.
- S25 File explorer: tree, preview, upload/download, rename/move/delete.
- S26 Code editor: tabs, diagnostics, diff, save and isolated terminal.
- S27 Version history: compare and safe revert commit.
- S28 Environment variables: masked, write-only secret management.
- S29 Collaborators: invite, least-privilege roles, removal and audit.

### AI
- S30 AI Chat: conversations, model/provider disclosure, streaming, stop/regenerate, copy, feedback, attachments.
- S31 Chat context: explicit workspace/project/files selection.
- S32 Builder prompt: goal, project, stack, constraints, acceptance criteria.
- S33 Requirements review: assumptions, questions, risks and user approval.
- S34 Build plan review: tasks, affected files, permissions, estimate and rollback.
- S35 Build monitor: queue, progress, sanitized logs, cancel/retry/reconnect.
- S36 Change review: diff, rationale, per-file accept/reject, apply to branch.
- S37 Test results: suites, pass/fail, logs and rerun.
- S38 Preview: isolated responsive preview, console, expiring share.
- S39 AI usage history: provider/model, project, request ID, usage and cost.
- S40 AI settings: provider/model, privacy, retention, quotas and fallback.

### Automation and operations
- S41 Automations list: enabled state, trigger, owner, last/next run.
- S42 Automation builder: trigger, conditions, actions, scopes, dry-run, approval.
- S43 Automation run detail: timeline, redacted I/O, safe retry.
- S44 Integrations catalogue: providers, capabilities and scopes.
- S45 Integration setup: OAuth/secret manager, test, reconnect, revoke.
- S46 Deployments list: project/environment/commit/status.
- S47 Deployment detail: preflight, build, tests, release, health, rollback.
- S48 Domains/environments: DNS, TLS, mapping.
- S49 Monitoring: API, database, queue, workers, webhooks, sandbox.
- S50 Audit log: append-only, redacted administrative/security events.

### Wallet and account
- S51 Wallet overview: server-derived balance, pending funds and ledger.
- S52 Add credits: server-priced packages and hosted checkout.
- S53 Checkout return: server-verified pending/success/failure.
- S54 Transaction detail: reference, amount, status and receipt.
- S55 Usage/limits: plan, quota, consumption and reset.
- S56 Profile/preferences: identity, locale, theme, accessibility, notifications.
- S57 Security: password, MFA, sessions, devices, recovery.
- S58 Privacy/data: export, retention, consent and account deletion.
- S59 Legal: Terms, Privacy, acceptable use and cookies.
- S60 Support: ticket creation and attachment scanning.

### Administration
- S61 Admin overview: service health, queue, incidents and reconciliation.
- S62 Admin users/workspaces: search, access, suspension and audit.
- S63 Admin billing: unmatched events, settlement mismatch and reconciliation.
- S64 Admin feature flags: staged rollout, owner, expiry and history.
- S65 Admin incidents: severity, impact, timeline and postmortem.

## 4. End-to-end journeys
### First-time user
Splash → Welcome → Sign up → Verify email → MFA if enabled → Profile → Create/join workspace → Onboarding → Home.

### Project creation
Home → Create project → Blank/template/import → Name/visibility → Stack/runtime → Review → Create → Project overview → AI Builder/editor → Diff review → Tests → Preview → explicit deployment preflight → Deploy → health check.

### Discovery
Discover → search/filter → capability detail → permission/pricing review → Try/Add → setup wizard → connected state and audit event.

### AI Builder
Prompt → requirements → plan review → explicit approval → queued build → progress → change review → tests → preview → explicit deploy approval. AI never silently merges or deploys generated code.

### Credits purchase
Usage → package selection → server creates pending intent → hosted Paystack checkout → signed webhook → intent verification → idempotent ledger settlement → reconciliation → refreshed wallet and receipt. Redirect alone never credits an account.

## 5. Interaction contract
Every control defines default/focus/pressed/disabled/loading/success/error states; exact action/destination; reversibility; confirmation; empty/offline/stale/denied states; keyboard/screen-reader label; analytics event without sensitive payload.

- Sidebar changes route while preserving workspace context.
- Search is keyboard navigable; Enter opens selected result, Escape closes.
- Create menu routes to dedicated creation flows.
- Notifications deep-link only after authorization.
- Destructive actions explain impact; account/workspace deletion uses typed confirmation and re-authentication.
- Deploy opens preflight showing commit, branch, environment, tests and secrets state.
- Unsaved forms warn before navigation.
- Retry only repeats idempotent actions.

## 6. Design system
Premium, calm, technical, trustworthy. Light default, optional dark theme, restrained motion, clear hierarchy.

Tokens:
- Primary #4F46E5; accent #3B82F6.
- Success #10B981; warning #F59E0B; error #EF4444.
- Background #F8FAFC; surface #FFFFFF; text #0F172A; muted #64748B; border #E2E8F0.
- Spacing 4/8/16/24/32; control radius 8, card radius 12, large panel radius 20.
- Inter/system font; type scale 12/14/16/20/28/36.

Responsive:
- Mobile under 640px: one column, bottom nav, full-width actions, sheets.
- Tablet 640–1023px: collapsible nav, touch-first controls, two columns when useful.
- Desktop 1024px+: sidebar, multi-column workspace, optional inspector.
- No horizontal scrolling for core tasks.

Accessibility target WCAG 2.2 AA: visible focus, semantic headings, labelled inputs, error summary, 44px minimum touch target, contrast, reduced motion, non-colour status, keyboard and screen-reader support.

## 7. Permissions
Workspace roles: Owner, Admin, Developer, Editor, Viewer, Billing Manager. Capability checks are server-side on every request; hiding a button is not authorization. Sensitive operations require step-up authentication. Privileged changes create audit events.

## 8. Domain model
Users, identities, sessions, MFA factors, workspaces, memberships, invitations, projects, repositories, environments, files, secrets, conversations, messages, attachments, AI requests, usage events, build jobs/events/artifacts, test runs, deployments, integrations, automation definitions/runs, plans, credit packages, payment intents, provider events, journal transactions/entries, notifications, audit events, support tickets and feature flags.

Use UUID IDs, UTC timestamps, tenant ownership foreign keys, unique idempotency keys, immutable financial/audit records and reviewed migrations.

## 9. Technical target
- Web: React + TypeScript, accessible components, route-level code splitting.
- Mobile: Expo/React Native sharing API contracts and design tokens.
- API: one documented authenticated API boundary; reconcile legacy FastAPI edge-control API deliberately rather than mixing blindly.
- Identity: managed OIDC or reviewed auth; short-lived access tokens, rotating refresh sessions, MFA.
- Data: PostgreSQL migrations, tenant-scoped queries, constraints.
- Cache/queue: Redis plus durable jobs, retry/dead-letter policy.
- AI: provider adapter, server-only keys, quota/policy, schema validation and redaction.
- Execution: ephemeral isolated sandbox, no privileged mode or Docker socket, no network by default, strict resource caps.
- Payments: server-created Paystack intents, raw-body signature verification, unique events, balanced ledger and reconciliation.
- Storage: private object storage, expiring signed URLs, malware scanning.
- Operations: structured redacted logs, metrics, tracing, alerts and runbooks.

## 10. Release targets and gates
Targets to validate after implementation, not claims of current performance: 99.9% monthly availability objective; p95 read API below 400ms under defined load; p95 app shell render below 2.5s on supported mid-range devices; no open critical/high vulnerabilities; all privileged/financial mutations auditable; approved RPO/RTO with rehearsed restore.

Release requires clean install/build/typecheck; unit/API/migration/browser/mobile/E2E tests; auth/tenant isolation; sandbox and secret scanning; Paystack signature/idempotency/ledger/reconciliation tests; backup restore; monitoring/incident runbooks; privacy/legal review; accessibility/performance audit; owner sign-off on exact commit.

## 11. Delivery sequence
P0 architecture reconciliation, credential removal, CI, auth, tenant model, migrations and audit.  
P1 responsive shell, onboarding, projects/files, AI chat and safe build lifecycle.  
P2 wallet/credits, Paystack test reconciliation, integrations and deployment.  
P3 automations, analytics, collaboration, admin and native polish.  
P4 security review, load/failure tests, disaster recovery, compliance and staged launch.
