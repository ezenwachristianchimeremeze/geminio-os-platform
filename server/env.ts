import { z } from "zod";

const schema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().min(1).max(65535).default(4000),
  DATABASE_URL: z.string().url(),
  REDIS_URL: z.string().url(),
  SESSION_SECRET: z.string().min(32),
  PAYSTACK_SECRET_KEY: z.string().min(1),
  PAYSTACK_PUBLIC_KEY: z.string().min(1),
  PAYSTACK_WEBHOOK_SECRET: z.string().min(1),
  OPENAI_API_KEY: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),
  AI_DEFAULT_PROVIDER: z.enum(["openai", "gemini"]).default("openai"),
  DOCKER_BIN: z.string().default("docker"),
  AI_SANDBOX_IMAGE: z.string().default("geminio-ai-sandbox:latest"),
  APP_BASE_URL: z.string().url(),
}).superRefine((v, ctx) => {
  if (!v.OPENAI_API_KEY && !v.GEMINI_API_KEY) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: "Configure at least one AI provider key." });
  }
  if (v.NODE_ENV === "production" && v.SESSION_SECRET.includes("change-me")) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: "SESSION_SECRET must not use a sample value." });
  }
});

const parsed = schema.safeParse(process.env);
if (!parsed.success) {
  console.error("Invalid environment configuration:", parsed.error.flatten().fieldErrors);
  throw new Error("Environment validation failed; refusing to start.");
}
export const env = Object.freeze(parsed.data);
export type Environment = typeof env;
