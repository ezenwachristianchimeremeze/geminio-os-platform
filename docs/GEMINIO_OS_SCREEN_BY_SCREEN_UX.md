# Geminio OS — Screen-by-Screen UX and Interaction Specification

This document is the interaction contract for the product. Screen IDs are stable references for design, implementation, analytics and QA. It describes the intended product; it is not proof that every route or service is already implemented.

## Global application shell

### Desktop
- Left navigation: brand/workspace switcher, Home, Discover, Projects, AI Chat, AI Builder, Files, Automations, Integrations, Deployments, Analytics, Wallet, Team.
- Bottom of sidebar: Help, Settings, collapse control.
- Top bar: breadcrumb, global search, Create menu, notifications, avatar.
- Main content: responsive page canvas. Optional right inspector for properties, activity or build status.
- Admin Console is visible only to authorized administrators.

### Mobile and tablet
- Top bar: logo, workspace selector, notifications and avatar.
- Bottom tabs: Home, Discover, Projects, AI, More.
- More opens a labelled bottom sheet containing Files, Automations, Integrations, Deployments, Analytics, Wallet, Team, Settings and Help.
- Tablet uses a collapsible rail or navigation drawer; do not squeeze the desktop sidebar into a narrow viewport.
- Back closes an open sheet first, then navigates to the previous route.
- All touch controls have at least 44 by 44 CSS pixel hit areas.

### Global control behavior
- Workspace switcher: list memberships and roles; switching reloads tenant-scoped data and clears stale cached data.
- Search: opens grouped results for projects, files, chats, people, docs, builds and deployments. Enter opens the selected authorized result; Escape closes.
- Create: menu for Project, Chat, AI Build, Automation and Invite member. Each item opens a dedicated creation flow.
- Notifications: opens inbox; selecting a notification checks current access before opening its destination.
- Avatar: Profile, Preferences, Security, Help and Sign out.
- Unsaved changes: show Stay / Save / Discard.
- Delete, deploy, payment and access changes: explain impact and require explicit confirmation.
- Retry: only repeat safe idempotent operations; never blindly repeat a payment or external side effect.

## Identity and onboarding

### S00 — Splash / Boot
Logo mark, Geminio OS name, version and short status. Restore secure session and check maintenance/update state. Valid session goes to workspace/Home; no session goes to Welcome; forced update and maintenance show dedicated states. Retry is available for recoverable failures. Never expose stack traces.

### S01 — Welcome
Logo, concise product value proposition, Create account, Sign in and Explore demo. Footer links to Terms, Privacy and Help. Demo is clearly labelled read-only.

### S02 — Sign up
Full name, email, password, confirm password and required Terms/Privacy acknowledgement. Validate inline; support password managers. Create account submits once and goes to email verification. Existing-account responses must not disclose sensitive account existence.

### S03 — Verify email
Masked email, instructions, expiry and resend cooldown. Verify link continues onboarding; resend shows a cooldown; Change email returns to editable sign-up details.

### S04 — Sign in
Email, password, show/hide password, passkey option when configured, Forgot password and Create account. Success routes to workspace selection or Home. Invalid credentials use generic wording; throttling shows wait guidance.

### S05 — MFA challenge
Authenticator or passkey challenge, alternate method and recovery-code route. Attempts are rate-limited. Success establishes the session; suspicious attempts trigger notification.

### S06 — Forgot password
Email input and privacy-preserving confirmation message. Back returns to Sign in.

### S07 — Reset password
New password and confirmation. Consume a single-use expiring token, revoke other sessions and return to Sign in. Expired links offer a new request.

### S08 — Profile setup
Display name, optional avatar, locale, timezone and accessibility preferences. Continue to workspace setup; optional fields may be skipped.

### S09 — Workspace setup
Create workspace or join by invitation. Creation collects workspace name, unique slug and supported region. Joining shows inviter and requested role before acceptance.

### S10 — Onboarding
Checklist: create first project, explore Discover, try AI Chat, review security and invite a teammate. Each action deep-links to the relevant screen. Skip remains available and progress persists.

### S11 — Invitation acceptance
Show inviter, workspace, role, expiry and permission summary. Accept joins workspace; Decline confirms; expired invitations offer a request-new-invite path.

## Home and discovery

### S12 — Home
Greeting and workspace name; quick actions Create project and Start AI build; recent projects; recent activity; build/deployment health; usage/credits; onboarding checklist. Project card opens Project Overview; build card opens Build Monitor; usage card opens Usage. Empty workspace shows templates and import. Offline state shows last-updated time and Retry.

### S13 — Discover
Search, categories, featured and recently added. Categories include AI tools, templates, integrations, automations, learning and community resources. Cards show title, description, compatibility, maintainer and pricing label. Selecting a card opens detail.

### S14 — Discovery detail
Description, use cases, preview, compatibility, permissions/scopes, data handling, pricing and changelog. Try opens a safe demo; Add starts setup; Learn more opens documentation. Show exact requested permissions before connection.

### S15 — Global search
Grouped results: Projects, Files, Chats, People, Docs, Builds and Deployments. Filters narrow results. Selecting a result checks permission. Empty state offers clear filters or create.

### S16 — Notifications
All, Unread, Mentions, Builds, Billing and Security filters. Open notification, Mark read and Mark all read. Revoked access shows a neutral no-access message.

### S17 — Activity feed
Actor, action, resource, timestamp and workspace/project. Filter and export when permitted. Never include secret values.

### S18 — Help centre
Searchable articles, categories, troubleshooting and contact support. Article opens documentation; Contact opens Support.

## Projects, files and code

### S19 — Projects list
Grid/list toggle, search, status/owner filters, sorting, Create and Import. Cards show name, stack, last update, branch, build status and collaborators. Open goes to Project Overview. Archive and Delete live in overflow; Delete requires typed project slug and impact summary.

### S20 — Create project
Step 1: Blank, Template or Import. Step 2: name, description and visibility. Step 3: stack, runtime and branch. Step 4: review configuration and resource use. Create shows progress then Project Overview. Cancel preserves draft.

### S21 — Template gallery
Filter by category, stack, maintained version and skill level. Preview is read-only. Use template opens Create Project with the template preselected.

### S22 — Import repository
Connect provider, authorize scopes, choose repository and branch, preview import, choose destination, then import. Progress is persisted; failure gives a retry and support reference. Revoke access from Integration Setup.

### S23 — Project overview
Header with name, visibility, branch, environment and status. Tabs: Overview, Files, AI, Builds, Tests, Deployments and Settings. Actions: Open editor, AI build, Run tests and Deploy. Deploy opens preflight, not immediate production release.

### S24 — Project settings
General, repository, access, environment, notifications, archive and delete. Save shows confirmation and audit event. Archive removes from active list. Delete requires re-authentication and typed slug.

### S25 — File explorer
Tree, breadcrumbs, search, file type, size and modified time. File tap opens editor; Upload opens picker and scanning state; Download uses expiring signed URL; Rename/Move use dialogs; Delete confirms. Name conflicts offer compare/replace, never silent overwrite.

### S26 — Code editor
File tree, tabs, editor, diagnostics, save indicator and bottom output panel. Save persists to working branch; Format previews diff; Find searches; Compare opens history; Ask AI opens chat with selected context only after consent. Save conflict offers compare/reload. Terminal runs only in isolated workspace.

### S27 — Version history
Commit list, author, message, time and changed-file count. Compare opens diff. Restore creates a new revert commit after confirmation; do not rewrite history automatically.

### S28 — Environment variables
Key, environment and updated time; values are masked and write-only. Add/Edit never returns secret values. Rotate and Delete require confirmation. Secrets are never placed in client bundles.

### S29 — Collaborators
Members, email, role, invitation state and last active. Invite collects email and least-privilege role. Role change and removal require confirmation and audit. Final workspace owner cannot be removed.

## AI chat and builder

### S30 — AI Chat
Conversation list, provider/model disclosure, context selector, message timeline and composer. Composer supports text, attachments and optional voice input. Send streams; Stop cancels; Regenerate shows usage impact; Copy copies; Feedback records rating. New chat opens context setup. States cover offline, provider unavailable, quota reached, timeout and safety refusal.

### S31 — Chat context
Workspace/project, selected files, branch and permission scope. Add/remove context; Apply returns to chat. Never silently include private files.

### S32 — AI Builder prompt
Goal, project, stack, constraints and acceptance criteria. Continue opens requirements review; Save Draft persists; Cancel returns. Warn about likely credentials in prompt.

### S33 — Requirements review
Generated requirements, assumptions, open questions and risks. Edit, answer questions, regenerate or Approve. No code execution yet.

### S34 — Build plan review
Ordered tasks, files affected, permissions, risks, estimated usage and rollback plan. Approve and Queue starts a job; Edit Plan returns to requirements; Cancel discards. Sensitive changes require separate approval.

### S35 — Build monitor
Timeline: queued, preparing, generating, validating, testing, ready for review, failed or cancelled. Show sanitized logs and persisted progress. Cancel confirms; Retry creates a new idempotent job; reconnect reloads events by build ID.

### S36 — Change review
File tree, unified diff, rationale and generated-code warnings. Accept/reject per file, request revision or apply approved changes to branch. Show target branch and exact changed-file count. Never auto-deploy.

### S37 — Test results
Suite summary, pass/fail/skipped, duration, logs and environment. Rerun failed; open failing file; copy sanitized report. Only show success when server reports completed tests.

### S38 — Preview
Responsive viewport, expiring preview URL, runtime console and error overlay. Change viewport, refresh, share with expiry or report issue. Preview has no production secrets.

### S39 — AI usage history
Date, provider/model, project, request ID, usage, credits/cost and status. Filter/export/open metadata. Sensitive prompt content is not exposed in admin views.

### S40 — AI settings
Default provider/model, privacy mode, retention, usage caps and fallback policy. Save, test or disable provider. API keys are stored server-side and never echoed to client.

## Automations, integrations and deployments

### S41 — Automations list
Name, trigger, enabled/paused, last/next run and owner. Create opens builder; open shows run detail; pause/resume updates status; delete confirms.

### S42 — Automation builder
Trigger, conditions, actions, connected accounts, scopes, schedule and failure policy. Validate, dry-run, Save Draft and Enable after explicit review. External actions require least privilege and idempotency.

### S43 — Automation run detail
Timeline, step status, redacted input/output and retry count. Retry only safe idempotent steps; disable automation; open integration.

### S44 — Integrations catalogue
Provider, capabilities, scopes, data access and setup requirements. Learn more or Connect. Unsupported providers show unavailable state honestly.

### S45 — Integration setup
Explain scopes, OAuth or secret-manager flow, validate callback, test connection, show connected summary. Reconnect, Rotate and Revoke are available with audit events.

### S46 — Deployments list
Project, environment, branch/commit, status, time and initiator. Open detail; filter; Start deployment opens preflight.

### S47 — Deployment detail
Stages: preflight, build, tests, artifact, release and health check. View logs, cancel before release, rollback to prior healthy release or open preview. Rollback requires authorization and reason.

### S48 — Domains and environments
Domains, DNS verification, TLS and environment mapping. Add domain shows DNS instructions; Verify checks server-side; Remove confirms. Never claim TLS is active before verification.

### S49 — Monitoring
API health, latency, errors, queues, workers, database, webhook and sandbox. Filter time range and export. Restrict infrastructure details by role.

### S50 — Audit log
Actor, action, target, result, timestamp and privacy-governed device metadata. Filter/export. Append-only and redacted.

## Wallet, account and admin

### S51 — Wallet overview
Currency, server-derived available/pending balance and ledger history. Add credits opens package selection; transaction opens detail; Refresh fetches server state. Client arithmetic is never authoritative.

### S52 — Add credits
Server-priced packages, fees/taxes where applicable, terms and payment methods. Select package then review; Continue asks server to create payment intent and hosted Paystack URL. Disable duplicate taps.

### S53 — Checkout return
Show Verifying, Verified, Pending or Failed based on server reconciliation. Refresh status, return to Wallet or contact support with reference. Redirect query parameters never settle money.

### S54 — Transaction detail
Reference, amount, currency, status, time, fees and receipt. Download receipt or report issue. Pending state explains next steps.

### S55 — Usage and limits
Plan, credits, usage breakdown, limits, reset date and alerts. Change plan, manage limits or view history. Prices and limits come from server.

### S56 — Profile and preferences
Identity, avatar, locale/timezone, theme, accessibility and notifications. Save syncs across clients.

### S57 — Security
Password, MFA/passkeys, sessions/devices and recovery codes. Revoke session; enable/disable factor with step-up authentication; regenerate recovery codes only after identity verification.

### S58 — Privacy and data
Request export → queued job and download notification. Account deletion → impact summary, re-authentication, typed confirmation and applicable cooling-off period. Allow cancellation while pending and show completion status.

### S59 — Legal
Terms, Privacy, acceptable use and cookies with version/effective date. Record acceptance version and timestamp.

### S60 — Support
Category, subject, description and optional attachment. Submit returns ticket ID. Scan attachments and warn users not to include secrets.

### S61 — Admin overview
Aggregate service health, queues, incidents, payment reconciliation and usage. Role-gated; never display customer secrets.

### S62 — Admin users/workspaces
Search, inspect access, suspend with reason, restore and audit. Every privileged action requires authorization and confirmation.

### S63 — Admin billing/reconciliation
Unmatched events, pending intents, amount/currency mismatches and ledger alerts. Inspect, retry safe reconciliation or escalate. No direct balance editing; corrections use reversing entries and approval.

### S64 — Admin feature flags
Flag, environment, rollout percentage, owner and expiry. Stage, pause or expire with history; production changes require approval.

### S65 — Admin incidents
Severity, owner, start, affected services, impact and timeline. Acknowledge, assign, update, publish approved customer notice and close with postmortem.

## Standard dialogs and QA contract
Dialogs include unsaved changes, destructive action, production deployment, access change, payment review, session revocation, account deletion, integration scopes and offline/retry explanation.

Every screen is incomplete until it has a registered route, server-side authorization, loading/empty/success/error/offline/denied states, validation, keyboard/screen-reader support, responsive layout, analytics event, automated route/component test and end-to-end test for its primary action. Every visible button must work or be disabled with an explanation.
