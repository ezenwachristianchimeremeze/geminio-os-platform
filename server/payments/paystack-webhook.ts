import express, { type Request, type Response } from "express";
import crypto from "node:crypto";
import { env } from "../env";

export const paystackWebhook = express.Router();

// Mount this router before express.json(), or use express.raw() on this route.
// Signature validation must use the exact raw request bytes.
paystackWebhook.post("/", express.raw({ type: "application/json", limit: "256kb" }), async (req: Request, res: Response) => {
  const raw = req.body;
  if (!Buffer.isBuffer(raw)) return res.status(400).send("Raw body required");
  const supplied = req.header("x-paystack-signature") ?? "";
  const expected = crypto.createHmac("sha512", env.PAYSTACK_WEBHOOK_SECRET).update(raw).digest("hex");
  const a = Buffer.from(supplied, "utf8");
  const b = Buffer.from(expected, "utf8");
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return res.status(401).send("Invalid signature");

  let event: { event?: string; data?: { reference?: string; status?: string; amount?: number; currency?: string; id?: number } };
  try { event = JSON.parse(raw.toString("utf8")); }
  catch { return res.status(400).send("Invalid JSON"); }

  if (event.event !== "charge.success") return res.status(200).json({ received: true, ignored: true });
  const data = event.data;
  if (!data?.reference || data.status !== "success" || !Number.isSafeInteger(data.amount) || !data.currency) {
    return res.status(400).send("Invalid payment payload");
  }

  try {
    // REQUIRED: replace with a DB transaction that locks the payment intent, verifies
    // expected amount/currency/customer, checks unique provider event/reference, and
    // posts balanced debit/credit ledger entries exactly once (idempotent).
    // Do not credit a wallet from webhook data alone without a matching pending intent.
    const { settleVerifiedPaystackPayment } = await import("./settle-payment");
    await settleVerifiedPaystackPayment({
      reference: data.reference, amountMinor: BigInt(data.amount), currency: data.currency,
      providerEventId: String(data.id ?? data.reference),
    });
    return res.status(200).json({ received: true });
  } catch (error) {
    console.error("Paystack webhook settlement failed:", error);
    return res.status(500).send("Settlement failed; provider may retry");
  }
});
