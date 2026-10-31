# Geminio OS — Screen-by-Screen UI/UX Specification

## Visual direction

**Personality:** premium, calm, precise, developer-focused, welcoming.  
**Primary:** Indigo `#4F46E5`; **accent:** blue `#3B82F6`; **success:** `#10B981`; **warning:** `#F59E0B`; **error:** `#EF4444`.  
**Surfaces:** app background `#F8FAFC`, cards `#FFFFFF`, text `#0F172A`, secondary text `#64748B`, borders `#E2E8F0`. Dark theme uses deep navy surfaces and preserves contrast.  
**Typography:** Inter/system sans; 14–16 px body; 24–32 px page titles; 12 px metadata.  
**Shape:** 12–16 px card radius, 10 px controls, restrained shadows, 8 px spacing rhythm.  
**Motion:** 120–200 ms transitions; reduced-motion preference disables nonessential movement.

## Shared components and exact behavior

- **Geminio mark + wordmark:** click returns to current workspace Home; on auth pages returns to Welcome.
- **Workspace switcher:** opens a menu with accessible workspaces, Create Workspace, Manage Members. Switching reloads all workspace-scoped queries and clears stale selections.
- **Global search:** opens command palette; typing filters accessible resources; Enter opens selected result; Escape closes.
- **Create (+):** menu: Project, Chat, Folder, Invite. Selecting opens the relevant creation flow.
- **Notification bell:** opens notification panel; clicking an item marks it read and navigates to its target.
- **Help:** opens contextual docs and support.
- **Avatar:** Profile, Preferences, Security, Switch workspace, Sign out. Sign out revokes session and returns to Welcome.
- **Primary buttons:** disabled while submitting; show progress; prevent duplicate submission; announce success/failure.
- **Overflow menu:** opens actions allowed by the user's role; unavailable actions are omitted or explained.
- **Breadcrumb:** each ancestor is a link; current location is plain text.
- **Dialogs:** trap focus, Esc closes only non-destructive dialogs, Enter confirms only when safe; destructive confirmation requires explicit action.
- **Toasts:** announce status and never contain secret values.
- **Bottom navigation (mobile):** Home, Discover, Build, Projects, More. Active tab uses filled icon + label. More opens a sheet with Chat, Files, Deployments, Integrations, Wallet, Notifications, Settings, Help.

## Screen specifications

### 01 — Splash / logo
**Layout:** centered Geminio geometric mark, wordmark, short tagline, thin progress line.  
**Actions:** none while resolving; Retry and Status appear on failure.  
**Next:** unauthenticated → Welcome; authenticated → Home; forced update → Update Required.

### 02 — Welcome
**Layout:** brand panel, product promise, 3 capability cards (Plan, Build, Ship), privacy/security note.  
**Buttons:** Sign in → 03; Create account → 04; Explore demo → read-only demo workspace with Demo label.  
**Footer:** Terms, Privacy, Status, Accessibility.

### 03 — Sign in
**Fields:** email, password; show/hide toggle; remember this device.  
**Buttons:** Sign in, Forgot password, Create account.  
**Behavior:** inline validation; server errors shown without revealing account existence; rate-limit state includes retry guidance. Success → Home or original deep link.

### 04 — Create account
**Fields:** full name, email, password, confirm password, required terms acceptance.  
**Buttons:** Create account, Sign in.  
**Behavior:** password rules and strength guidance; server-side duplicate check; submit creates pending verification state → 05.

### 05 — Verify email
**Layout:** masked email, 6-digit code entry or secure link confirmation.  
**Buttons:** Verify, Resend code (cooldown), Change email.  
**Behavior:** expiry and attempt limits; success → 08 onboarding.

### 06 — Forgot password
**Fields:** email. **Button:** Send reset link.  
**Behavior:** generic confirmation regardless of account existence → check-email state. Link → 07.

### 07 — Reset password
**Fields:** new password, confirm password.  
**Buttons:** Save password, Back to sign in.  
**Behavior:** validate one-time token, expire token after use, revoke sessions according to user choice. Success → 03.

### 08 — Onboarding
**Steps:** use case, experience level, preferred technology stack, workspace name.  
**Buttons:** Continue, Back, Skip optional step.  
**Behavior:** progress indicator, saved step state, editable later. Finish → 09.

### 09 — Workspace setup
**Cards:** personal workspace, team workspace, import existing project.  
**Buttons:** Create workspace, Invite teammates, Skip invites.  
**Behavior:** role-aware invitations; invitation acceptance requires sign-in. Success → 10.

### 10 — Home / Overview
**Top:** greeting, workspace name, quick-create button.  
**Cards:** Continue where you left off; recent projects; AI usage/credits; activity; system/integration status.  
**Buttons:** New Project → 15; Open AI Builder → 17; New Chat → 18; Browse Templates → 12; View Wallet → 27.  
**States:** first-use empty state with Create Project CTA; degraded providers show a banner with status detail.

### 11 — Global Search / Command Palette
**Overlay:** search input, recent items, command categories.  
**Keys:** Ctrl/Cmd+K opens; arrows select; Enter opens; Esc closes.  
**Result click:** opens the resource and preserves search history within workspace policy.

### 12 — Discovery
**Layout:** featured templates, starter projects, integrations, guides; category chips and search.  
**Buttons:** Filter, Sort, Preview, Use Template.  
**Next:** card → 13; Use Template → 15 with template preselected.

### 13 — Template Detail
**Content:** purpose, preview, stack, features, requirements, permissions, estimated usage.  
**Buttons:** Preview, Use Template, Back to Discovery.  
**Behavior:** project creation confirmation states files/resources that will be created.

### 14 — Projects List
**Controls:** grid/list toggle, search, status/stack filters, sort, Create Project, Import.  
**Card click:** 16. **Overflow:** Rename, Duplicate, Archive.  
**Behavior:** archive confirmation; archived projects accessible through filter.

### 15 — Create Project
**Fields:** project name, description, stack, template, visibility.  
**Buttons:** Create Draft, Cancel.  
**Behavior:** server validates workspace slug and permissions; success → 16.

### 16 — Project Overview
**Header:** project name, status, branch, actions menu.  
**Tabs:** Overview, Files, AI Builder, Activity, Tests, Deployments, Docs, Settings.  
**Buttons:** Build with AI → 17; Open Chat → 18; Files → 20; Run Tests → 22; Preview → 21.  
**Behavior:** each tab loads only authorized project data.

### 17 — AI Builder
**Layout:** left requirements/context panel; center plan and task steps; right usage/permissions inspector.  
**Input:** goal, requirements, stack, optional attachments.  
**Buttons:** Generate Plan, Edit Plan, Approve & Start, Pause, Cancel, Review Changes.  
**Behavior:** estimate cost before execution; require approval; show queued/running/waiting/failed/cancelled/completed; stream logs; show generated file diff. Accept/reject changes individually. Never deploy automatically.

### 18 — AI Chat
**Layout:** conversation list, message timeline, composer, attachment tray, model/provider selector.  
**Buttons:** New Chat, Send, Stop, Regenerate, Copy, thumbs feedback, Attach File.  
**Optional controls:** voice input/output only when permission and device support are present.  
**Behavior:** show provider fallback transparently; cancel stops generation; conversation export/delete follows retention policy.

### 19 — Code Workspace
**Layout:** file tree, editor, diagnostics, bottom terminal/output panel, diff inspector.  
**Buttons:** Save, Format, Find, Replace, Run, Test, Commit Changes.  
**Behavior:** run in isolated sandbox; terminal commands are scoped; commit shows diff and requires confirmation.

### 20 — File Manager
**Buttons:** Upload, New Folder, Rename, Move, Download, Delete.  
**Behavior:** validate file size/type; show scan status; signed download URLs expire; delete confirms and follows retention policy.

### 21 — Preview
**Layout:** preview canvas, viewport presets, refresh, open in new tab, diagnostics.  
**Behavior:** isolated origin and expiring preview session; errors link to logs; no production secrets in browser.

### 22 — Testing & Quality
**Sections:** unit, integration, e2e, lint, type-check, accessibility, security scan.  
**Buttons:** Run All, Run Selected, View Logs, Download Report.  
**Behavior:** run is tied to commit SHA and environment; report records exact tool versions.

### 23 — Documentation
**Tabs:** README, API, architecture, deployment, release notes.  
**Buttons:** Generate Draft, Edit, Preview, Publish.  
**Behavior:** generated content remains draft until approved; publish creates version history.

### 24 — Deployments
**Sections:** environments, latest release, history, logs, health.  
**Buttons:** Deploy, Rollback, View Logs.  
**Behavior:** deployment summary + target + approvals shown before confirmation; rollback is a new audited deployment event.

### 25 — Activity & Notifications
**Filters:** all, mentions, builds, deployments, billing, security; unread toggle.  
**Buttons:** Mark Read, Archive, Notification Preferences.  
**Behavior:** click navigates to related resource; inaccessible resource shows permission notice.

### 26 — Integrations
**Cards:** provider logo, capability, status, last sync, scopes.  
**Buttons:** Connect, Configure, Test Connection, Disconnect.  
**Behavior:** OAuth state/PKCE; credentials never rendered after save; disconnect confirms impact.

### 27 — Wallet
**Cards:** available balance, reserved credits, recent ledger entries.  
**Buttons:** Add Credits → 28; View Transactions; Download Statement.  
**Behavior:** balance comes from server ledger; pending/failed payments clearly separated.

### 28 — Credits & Plans
**Cards:** plan comparison, included usage, top-up amounts.  
**Buttons:** Choose Plan, Add Credits, View Invoices.  
**Behavior:** display currency and total before provider checkout; signed webhook is authoritative for settlement.

### 29 — Profile
**Fields:** display name, avatar, email, locale, time zone.  
**Buttons:** Save, Change Email.  
**Behavior:** email change requires verification; avatar uploads are scanned and size-limited.

### 30 — Preferences
**Controls:** light/dark/system theme, density, editor preferences, notification channels, language, accessibility.  
**Buttons:** Save, Reset Defaults.  
**Behavior:** changes preview immediately and persist after save.

### 31 — Security
**Sections:** password, MFA, sessions, recovery codes, trusted devices.  
**Buttons:** Change Password, Enable MFA, Revoke Session, Sign Out All.  
**Behavior:** re-authentication for sensitive operations; recovery codes shown once only.

### 32 — Help & Feedback
**Controls:** help search, category, message, optional diagnostics consent.  
**Buttons:** Search, Submit Feedback, Contact Support.  
**Behavior:** show ticket/reference number and status.

### 33 — Legal
**Tabs:** Terms, Privacy, Cookies, Subprocessors.  
**Buttons:** Download, Manage Cookies, Submit Data Request.  
**Behavior:** record policy version accepted; no preselected optional cookies.

### 34 — Offline / Degraded
**Layout:** connection status, last sync, pending safe drafts, conflicts.  
**Buttons:** Retry, Resolve Conflict, Open Cached Project.  
**Behavior:** financial, account-security, deletion, and deployment actions are unavailable offline.

### 35 — Admin Overview
**Cards:** service health, queue age, error rate, provider health, payment reconciliation.  
**Buttons:** View Incident, Open Audit Log, Manage Feature Flags.  
**Behavior:** role-gated; aggregates minimize personal data.

### 36 — User Directory
**Controls:** search, role/status filters, user detail.  
**Buttons:** Suspend, Reactivate, Change Role.  
**Behavior:** require reason, permission, re-auth for privileged action, and immutable audit event.

### 37 — Workspace & Access
**Sections:** members, invitations, roles, ownership.  
**Buttons:** Invite, Change Role, Remove Member, Transfer Ownership.  
**Behavior:** show access impact and require confirmation.

### 38 — Plans & Usage Admin
**Sections:** plan catalog, quotas, usage policy, effective date.  
**Buttons:** Create Draft, Preview Change, Publish.  
**Behavior:** dual approval for pricing/credit policy; audit before/after values.

### 39 — Provider Health & Secret Vault
**Sections:** provider availability, latency, configured status, last successful call.  
**Buttons:** Add/Rotate Secret, Test Connection, Disable Provider.  
**Behavior:** secret input is write-only; after save show only provider, key suffix/fingerprint, creation date. Never expose secret in API responses or logs.

### 40 — Payment Operations
**Sections:** webhook event queue, payment status, ledger settlement, reconciliation.  
**Buttons:** Inspect Event, Retry Safe Processing, Export Report.  
**Behavior:** verify signature and idempotency; never directly edit balance; adjustment requires audited compensating ledger entry.

### 41 — Audit Log
**Filters:** actor, action, resource, time, outcome, request ID.  
**Behavior:** append-only access; sensitive payload fields redacted; export permission-gated.

### 42 — Feature Flags
**Controls:** flag, environment, rollout percentage, allowlist, kill switch.  
**Buttons:** Save Draft, Preview, Activate, Disable.  
**Behavior:** every change audited and reversible; gradual rollout with metrics.

### 43 — Support & Incidents
**Sections:** incident timeline, severity, owner, customer impact, runbook, follow-ups.  
**Buttons:** Assign, Update Status, Add Timeline Entry, Close Incident.  
**Behavior:** closure requires resolution summary and follow-up tasks.

## Interaction quality checklist
- Every clickable element has a visible focus state and accessible name.
- Every submit action has loading, success, validation, and recoverable failure states.
- No icon-only action without tooltip/accessible label.
- No destructive action executes from a single accidental tap.
- No empty screen without explanation and next action.
- No provider integration is called connected until a health check succeeds.
- No financial balance is computed from client state.
- No user-generated code executes on the API process.
- Mobile bottom navigation never covers the final content or primary CTA; safe-area padding is included.
- Screen transitions preserve context and support browser/device back behavior.
