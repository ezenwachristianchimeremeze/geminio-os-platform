import { RateLimiterRedis } from "rate-limiter-flexible";
import type { Request, Response, NextFunction } from "express";
import Redis from "ioredis";
import { env } from "../env";

const redis = new Redis(env.REDIS_URL, {
  maxRetriesPerRequest: 1,
  enableReadyCheck: true,
  tls: env.REDIS_URL.startsWith("rediss://") ? {} : undefined,
});
redis.on("error", (error) => console.error("Rate-limit Redis error:", error.message));

const limiter = new RateLimiterRedis({
  storeClient: redis,
  keyPrefix: "geminio:rl",
  points: 60,
  duration: 60,
  blockDuration: 60,
  insuranceLimiter: undefined,
});

export function rateLimitByUser(points = 60, duration = 60) {
  const instance = points === 60 && duration === 60 ? limiter : new RateLimiterRedis({
    storeClient: redis, keyPrefix: `geminio:rl:${points}:${duration}`, points, duration, blockDuration: duration,
  });
  return async (req: Request, res: Response, next: NextFunction) => {
    // Trust only authenticated user IDs; IP is the fallback for anonymous traffic.
    const key = req.user && "id" in req.user ? String((req.user as { id: string }).id) : req.ip;
    try {
      await instance.consume(key);
      next();
    } catch (result) {
      const retry = result && typeof result === "object" && "msBeforeNext" in result
        ? Math.ceil(Number(result.msBeforeNext) / 1000) : duration;
      res.setHeader("Retry-After", String(retry));
      res.status(429).json({ error: "Too many requests. Please retry later." });
    }
  };
}

export async function closeRateLimiter(): Promise<void> { await redis.quit(); }
