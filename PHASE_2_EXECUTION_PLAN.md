# Geminio OS — Phase 2 Backend Integration

## Scope and status

This branch introduces backend integration building blocks and connected-screen examples. It is **not a production launch certification**. The repository's current default branch contains only a minimal README, so these files intentionally document integration boundaries rather than pretending an existing server, database, tRPC router, or settlement service is already present.

## 1. Runtime and environment

Use Node.js 20 LTS or newer. Install and pin compatible versions of:

- `express`, `zod`, `ioredis`, `rate-limiter-flexible`, `bullmq`
- `drizzle-orm`, `drizzle-kit`, `pg`
- `typescript`, `tsx`, and the existing Expo/React Native dependencies

Create a local `.env` (never commit it) with:

```dotenv
NODE_ENV=development
PORT=4000
DATABASE_URL=postgresql://user:password@localhost:5432/geminio
REDIS_URL=redis://localhost:6379
SESSION_SECRET=replace-with-at-least-32-random-characters
PAYSTACK_SECRET_KEY=sk_test_...
PAYSTACK_PUBLIC_KEY=pk_test_...
PAYSTACK_WEBHOOK_SECRET=your-webhook-hmac-secret
OPENAI_API_KEY=
GEMINI_API_KEY=
AI_DEFAULT_PROVIDER=openai
DOCKER_BIN=docker
AI_SANDBOX_IMAGE=geminio-ai-sandbox:latest
APP_BASE_URL=http://localhost:4000
WORKER_INTERNAL_SECRET=separate-long-random-secret
```

Generate secrets with a cryptographically secure password manager or `openssl rand -base64 48`. Keep production secrets in the deployment platform's secret manager. Never put provider secret keys in Expo `EXPO_PUBLIC_*` variables or the mobile bundle.

## 2. Local infrastructure

Start PostgreSQL and Redis with managed local services or a reviewed Docker Compose file. Restrict Redis to the private application network and require authentication/TLS outside local development. Configure health checks, backups, point-in-time recovery, connection limits, and alerting before production.

Build the sandbox image from a reviewed Dockerfile that contains only supported runtimes. The runner uses no network, a read-only root filesystem, dropped Linux capabilities, a non-root user, process/memory/CPU/time limits, and a read-only source mount. Add seccomp/AppArmor policy, output limits, image scanning, per-user quotas, and an external job watchdog. Do not allow arbitrary image names, Docker socket access from app containers, privileged mode, host mounts, or user-supplied Docker flags.

## 3. Database and ledger

Add the Drizzle schema to the project's schema barrel and configure `drizzle.config.ts` with the actual PostgreSQL connection. Generate and review migrations, then run them against a disposable database first.

Money is stored as integer minor units (kobo). A wallet balance is derived from posted ledger entries, not stored as a client-editable number. Each posted transaction must contain balanced debit and credit entries in one SERIALIZABLE database transaction. Use unique idempotency keys and provider references. Enforce immutability for posted journal rows through database permissions/triggers; corrections must be reversing entries. Add a deferred constraint trigger in SQL to enforce sum(debits) = sum(credits) per transaction. The TypeScript schema comment alone does not enforce this invariant.

## 4. Paystack webhook and checkout

Mount the webhook router before the global JSON parser so it receives raw request bytes. Verify `x-paystack-signature` with HMAC-SHA512 and constant-time comparison. Then load the matching pending payment intent from the database, validate expected amount, currency, customer, status, and reference, and settle exactly once. Implement `server/payments/settle-payment.ts` and a unique provider-event table before enabling wallet crediting. Return non-2xx on transient database failures so Paystack can retry. Never credit a wallet from a webhook payload without a matching pending intent.

Checkout must be initialized server-side using the secret key; the app receives only a short-lived authorization URL. Verify payment server-side and credit only after verified webhook/verification reconciliation. Use Paystack test keys and test accounts first.

## 5. Local webhook testing

Run the API on port 4000, expose it temporarily with a trusted tunnel, and configure the Paystack dashboard webhook URL to `https://YOUR-TUNNEL/payments/paystack/webhook`. Use test-mode credentials. Send test events from the Paystack dashboard or a signed local fixture. Confirm invalid signatures return 401, malformed payloads return 400, duplicate events do not double-credit, amount/currency mismatches are rejected, and database failures return 5xx. Do not test with real customer funds until reconciliation and rollback procedures are approved.

## 6. tRPC and app integration

The example screens import `trpc` from `@/utils/trpc`. Align this import with the actual app provider and implement authenticated procedures:

- `wallet.getBalance`: return server-derived balance and currency.
- `wallet.createTransfer`: validate recipient, limits, available funds, idempotency key, and step-up authentication.
- `credits.createCheckout`: create pending intent and initialize Paystack server-side.
- `aiBuilder.startBuild`: authorize project ownership, enforce quotas, enqueue BullMQ job, return build ID.

The SSE endpoint used by the AI Builder must authenticate the session, verify build ownership, send heartbeats, handle disconnects, and emit sanitized events. For React Native, verify the chosen streaming transport is supported on target platforms; use authenticated WebSocket or polling if fetch streaming is not reliable.

## 7. Release gates

Before launch: add integration tests, migration tests, webhook signature/idempotency tests, rate-limit tests, queue retry/dead-letter handling, sandbox escape tests, SAST/dependency scanning, secret scanning, structured logs with redaction, metrics/tracing, incident runbooks, disaster recovery drills, fraud monitoring, KYC/AML and payment-provider compliance review, privacy/data-retention controls, and independent penetration testing.

Do not enable live transfers or wallet crediting until the ledger settlement service, reconciliation jobs, fraud controls, regulatory review, and operational support are complete.
