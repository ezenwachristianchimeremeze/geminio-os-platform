# Geminio OS

**An AI-assisted software development and productivity workspace.** Geminio OS helps users move from project idea → requirements → architecture → code generation → review → tests → preview → approved deployment.

> **Release status: Development / not production-certified.** This repository contains a responsive product preview, existing backend components, Phase 2 integration scaffolding, and the product architecture. Live authentication, AI provider operations, payment settlement, deployment, and hardened sandbox execution require the services and release gates documented below.

## Start here
- [End-to-end product architecture](GEMINIO_OS_PRODUCT_ARCHITECTURE.md)
- [Screen-by-screen UI/UX and interaction specification](GEMINIO_OS_SCREEN_BY_SCREEN_UX.md)
- [Production release gates](PRODUCTION_RELEASE_GATES.md)
- [Phase 2 backend integration plan](PHASE_2_EXECUTION_PLAN.md)

## Product preview
Open [geminio-os/index.html](geminio-os/index.html) in a browser or serve the repository root with a static file server, then visit `/geminio-os/`.

The preview includes Welcome, sign-in/sign-up demo flows, Home, Discovery, Projects, Create Project, Project Overview, AI Builder plan preview, Chat, Files, Tests, Deployments, Documentation, Integrations, Wallet, Settings, and Help. It is intentionally local/demo-only: it does not create real accounts, call AI providers, charge payments, store real balances, or deploy code.

## Repository map
- `geminio-os/` — standalone responsive interaction prototype.
- `app/` — connected-screen examples from Phase 2.
- `server/` — TypeScript integration building blocks for environment validation, rate limiting, AI jobs, chat fallback, sandbox execution, wallet schema and payment webhooks.
- `backend/` — existing Python/FastAPI/SQLite edge health, sync, ledger, middleware and documentation modules.
- `dashboard/` — existing CHIXUS edge-control dashboard (kept separate from the Geminio OS product preview).
- `tests/` — existing Python test fixtures.
- `*.pdf` — previously supplied project, API, deployment, audit, QA and production-readiness documents.

## Important architecture boundary
The repository currently contains both Python/FastAPI/SQLite modules and TypeScript/Drizzle/Redis/BullMQ integration scaffolding. Do not allow both stacks to become competing sources of truth for authentication, workspace authorization, wallet balances or payment settlement. Select a primary API boundary and define any deliberate service split before launch.

## Security notes
- Never commit real credentials or put provider secrets in client-side bundles.
- Credentials that were previously committed must be rotated immediately. Removing them from the latest source does not remove them from Git history; history cleanup and secret-scanning review are still required.
- Wallet balances must be derived from server-side ledger entries. A browser redirect is not proof of payment.
- User code must run only in a hardened, isolated execution environment.
- Read [PRODUCTION_RELEASE_GATES.md](PRODUCTION_RELEASE_GATES.md) before staging or production deployment.

## Production launch
A successful Git push is not a production deployment. Before launch, establish reproducible dependency manifests and lockfiles, run clean builds and automated tests, verify tenant isolation and security controls, test payment webhooks in provider test mode, restore database backups, and complete staging acceptance. See the release gates for evidence required to make a go/no-go decision.

## Maintainer
Ezenwa Christian Chimeremeze
