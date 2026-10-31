import { pgEnum, pgTable, uuid, varchar, bigint, timestamp, index, uniqueIndex, text } from "drizzle-orm/pg-core";
import { sql } from "drizzle-orm";

export const walletStatus = pgEnum("wallet_status", ["active", "frozen", "closed"]);
export const ledgerDirection = pgEnum("ledger_direction", ["debit", "credit"]);
export const ledgerStatus = pgEnum("ledger_status", ["pending", "posted", "reversed"]);

export const wallets = pgTable("wallets", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull(),
  currency: varchar("currency", { length: 3 }).notNull().default("NGN"),
  status: walletStatus("status").notNull().default("active"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
}, t => [uniqueIndex("wallet_user_currency_uq").on(t.userId, t.currency)]);

/** Immutable journal lines. Store minor units (kobo), never floating-point naira. */
export const ledgerTransactions = pgTable("ledger_transactions", {
  id: uuid("id").defaultRandom().primaryKey(),
  reference: varchar("reference", { length: 100 }).notNull(),
  description: text("description"),
  status: ledgerStatus("status").notNull().default("pending"),
  idempotencyKey: varchar("idempotency_key", { length: 128 }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  postedAt: timestamp("posted_at", { withTimezone: true }),
}, t => [uniqueIndex("ledger_reference_uq").on(t.reference), uniqueIndex("ledger_idempotency_uq").on(t.idempotencyKey)]);

export const ledgerEntries = pgTable("ledger_entries", {
  id: uuid("id").defaultRandom().primaryKey(),
  transactionId: uuid("transaction_id").notNull().references(() => ledgerTransactions.id),
  walletId: uuid("wallet_id").notNull().references(() => wallets.id),
  direction: ledgerDirection("direction").notNull(),
  amountMinor: bigint("amount_minor", { mode: "bigint" }).notNull(),
  currency: varchar("currency", { length: 3 }).notNull().default("NGN"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
}, t => [index("ledger_entries_wallet_created_idx").on(t.walletId, t.createdAt)]);

/**
 * Enforce per-transaction debit/credit equality in a SERIALIZABLE DB transaction
 * or a deferred PostgreSQL constraint trigger in migration SQL. Never update/delete
 * posted journal lines; corrections are new reversing transactions.
 */
export const walletAuditEvents = pgTable("wallet_audit_events", {
  id: uuid("id").defaultRandom().primaryKey(),
  walletId: uuid("wallet_id").references(() => wallets.id),
  actorUserId: uuid("actor_user_id"),
  action: varchar("action", { length: 80 }).notNull(),
  reason: text("reason").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
}, t => [index("wallet_audit_wallet_idx").on(t.walletId, t.createdAt)]);
