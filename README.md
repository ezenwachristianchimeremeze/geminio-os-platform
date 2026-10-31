# Geminio OS

**An AI-first software creation and productivity workspace.** Geminio OS is designed to bring project creation, AI-assisted software building, collaboration, automation, integrations, deployment workflows and usage management into one connected environment.

> **Release status: in development; not certified for production.** The repository currently contains architecture documents, legacy edge-control services, a small set of React Native integration examples and Phase 2 backend building blocks. It is not yet a complete, verified application. See the release gates before deploying or enabling payments.

## Product journey

**Brand / Splash → Welcome → Sign up or Sign in → Email verification → MFA when enabled → Profile → Workspace → Onboarding → Home**

From Home, users can discover tools, create/import projects, chat with AI, run an AI Builder plan, review generated code, run tests, preview changes, collaborate, automate tasks and manage deployments. Wallet and credits are server-authoritative and use a verified payment/ledger flow.

## Documentation
- [Master product and technical architecture](docs/GEMINIO_OS_MASTER_PRODUCT_ARCHITECTURE.md)
- [Screen-by-screen UX and interaction specification](docs/GEMINIO_OS_SCREEN_BY_SCREEN_UX.md)
- [Production readiness gates](docs/PRODUCTION_READINESS_GATES.md)
- [Phase 2 backend execution plan](PHASE_2_EXECUTION_PLAN.md)

## Current repository map
- app/ — three React Native connected-screen examples (wallet, credits, AI Builder).
- backend/ — Python FastAPI edge-health, ledger, rate-limit and sync modules; currently identified as CHIXUS edge-control services and not reconciled with the Geminio OS app API.
- dashboard/ — standalone HTML edge-control dashboard.
- server/ — TypeScript integration building blocks for environment validation, rate limiting, AI worker, chat fallback, sandbox runner, wallet schema and Paystack webhook.
- tests/ — existing Python test support.
- verify_team/ — legacy team-verification service.
- index.html — personal portfolio page; not the Geminio OS app entry point.
- PDF files — existing project, API, capability, audit, QA, deployment and readiness documents.

## Architecture direction
The target is a responsive web application and Expo/React Native client backed by one documented authenticated API and PostgreSQL data model. Redis supports rate limits and durable job coordination. AI providers are accessed only server-side. Code execution uses isolated, short-lived, resource-limited sandboxes. Paystack payments are created server-side and reconciled through verified, idempotent webhooks and a balanced immutable ledger.

Do not merge legacy services into the app API without defining ownership, authentication, data contracts, migrations and tests.

## Security rules
- Never commit API keys, passwords, passkeys, signing secrets or production environment files.
- Never expose provider secrets through public client environment variables or app bundles.
- Never trust client-reported wallet balances or payment redirect success.
- Never run user-generated code in the application process or a privileged container.
- Enforce workspace permissions server-side for every read and write.
- Treat generated code, repository content and uploaded files as untrusted input.

## Production status
A successful GitHub commit is not a production deployment. Production requires a coherent build system, route implementation, database migrations, authentication, API integration, automated tests, security review, observability, backups, deployment configuration and owner-supplied provider credentials. Track evidence in [Production Readiness Gates](docs/PRODUCTION_READINESS_GATES.md).

## Ownership
Product owner and project founder: **Ezenwa Christian Chimeremeze**.
