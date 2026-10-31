import { Worker, Job } from "bullmq";
import IORedis from "ioredis";
import { env } from "../env";

export type BuildJob = { buildId: string; userId: string; prompt: string; projectId: string };
const connection = new IORedis(env.REDIS_URL, { maxRetriesPerRequest: null, enableReadyCheck: true });

async function publish(buildId: string, event: Record<string, unknown>) {
  await connection.publish(`geminio:build:${buildId}`, JSON.stringify({ at: new Date().toISOString(), ...event }));
}

async function processBuild(job: Job<BuildJob>) {
  const { buildId, userId, prompt, projectId } = job.data;
  if (!prompt.trim() || prompt.length > 20_000) throw new Error("Invalid build prompt.");
  await publish(buildId, { type: "status", status: "running", projectId, userId });
  try {
    // Delegate to the application-owned build orchestrator; never evaluate model output in this worker.
    const response = await fetch(`${env.APP_BASE_URL}/internal/ai-builder/execute`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-internal-worker-secret": process.env.WORKER_INTERNAL_SECRET ?? "" },
      body: JSON.stringify({ buildId, userId, projectId, prompt }),
      signal: AbortSignal.timeout(10 * 60 * 1000),
    });
    if (!response.ok) throw new Error(`Build orchestrator failed (${response.status}).`);
    const result = await response.json() as { summary?: string };
    await publish(buildId, { type: "status", status: "completed", summary: result.summary ?? "Build completed." });
    return result;
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown build failure";
    await publish(buildId, { type: "status", status: "failed", message });
    throw error;
  }
}

export const aiBuilderWorker = new Worker<BuildJob>("ai-builder", processBuild, {
  connection, concurrency: 3,
  limiter: { max: 10, duration: 60_000 },
  lockDuration: 120_000,
});
aiBuilderWorker.on("failed", (job, error) => console.error("AI build job failed", job?.id, error.message));
