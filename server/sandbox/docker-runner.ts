import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { env } from "../env";

const execFileAsync = promisify(execFile);
const MAX_SOURCE_BYTES = 64 * 1024;
const ALLOWED_LANGUAGES = {
  javascript: { filename: "main.js", command: ["node", "/workspace/main.js"] },
  python: { filename: "main.py", command: ["python", "-I", "/workspace/main.py"] },
} as const;
type Language = keyof typeof ALLOWED_LANGUAGES;

export async function runInSandbox(language: Language, source: string) {
  if (!(language in ALLOWED_LANGUAGES)) throw new Error("Unsupported sandbox language.");
  if (Buffer.byteLength(source, "utf8") > MAX_SOURCE_BYTES) throw new Error("Source exceeds sandbox size limit.");
  const id = randomUUID();
  const workdir = await mkdtemp(path.join(tmpdir(), "geminio-sandbox-"));
  const config = ALLOWED_LANGUAGES[language];
  try {
    await writeFile(path.join(workdir, config.filename), source, { encoding: "utf8", mode: 0o400 });
    const args = [
      "run", "--rm", "--name", `geminio-${id}`,
      "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
      "--pids-limit=64", "--memory=128m", "--memory-swap=128m", "--cpus=0.5",
      "--user=65534:65534", "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
      "--mount", `type=bind,src=${workdir},dst=/workspace,readonly`,
      "--workdir=/workspace", env.AI_SANDBOX_IMAGE, ...config.command,
    ];
    const { stdout, stderr } = await execFileAsync(env.DOCKER_BIN, args, {
      timeout: 5_000, maxBuffer: 256 * 1024, windowsHide: true,
    });
    return { stdout, stderr, exitCode: 0 };
  } catch (error) {
    const e = error as Error & { stdout?: string; stderr?: string; code?: number | string };
    if (e.killed) return { stdout: e.stdout ?? "", stderr: "Execution timed out (5 seconds).", exitCode: 124 };
    return { stdout: e.stdout ?? "", stderr: e.stderr ?? e.message, exitCode: typeof e.code === "number" ? e.code : 1 };
  } finally {
    await rm(workdir, { recursive: true, force: true });
  }
}
