type Provider = "openai" | "gemini";
export type ChatMessage = { role: "system" | "user" | "assistant"; content: string };
export type ChatResult = { provider: Provider; text: string };

const transient = (status: number) => status === 429 || status >= 500;

async function openAI(messages: ChatMessage[], signal?: AbortSignal): Promise<string> {
  const key = process.env.OPENAI_API_KEY;
  if (!key) throw new Error("OpenAI is not configured");
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST", signal,
    headers: { authorization: `Bearer ${key}`, "content-type": "application/json" },
    body: JSON.stringify({ model: "gpt-4o-mini", messages, temperature: 0.4 }),
  });
  if (!response.ok) {
    const error = new Error(`OpenAI request failed (${response.status})`) as Error & { status?: number };
    error.status = response.status; throw error;
  }
  const body = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
  const text = body.choices?.[0]?.message?.content;
  if (!text) throw new Error("OpenAI returned an empty response");
  return text;
}

async function gemini(messages: ChatMessage[], signal?: AbortSignal): Promise<string> {
  const key = process.env.GEMINI_API_KEY;
  if (!key) throw new Error("Gemini is not configured");
  const system = messages.filter(m => m.role === "system").map(m => m.content).join("\n");
  const contents = messages.filter(m => m.role !== "system").map(m => ({
    role: m.role === "assistant" ? "model" : "user", parts: [{ text: m.content }],
  }));
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${encodeURIComponent(key)}`, {
    method: "POST", signal, headers: { "content-type": "application/json" },
    body: JSON.stringify({ systemInstruction: system ? { parts: [{ text: system }] } : undefined, contents }),
  });
  if (!response.ok) {
    const error = new Error(`Gemini request failed (${response.status})`) as Error & { status?: number };
    error.status = response.status; throw error;
  }
  const body = await response.json() as { candidates?: Array<{ content?: { parts?: Array<{ text?: string }> } }> };
  const text = body.candidates?.[0]?.content?.parts?.map(p => p.text ?? "").join("");
  if (!text) throw new Error("Gemini returned an empty response");
  return text;
}

/** Retries the alternate provider only for transient/provider-availability failures. */
export async function chatWithFallback(messages: ChatMessage[], signal?: AbortSignal): Promise<ChatResult> {
  const preferred: Provider = process.env.AI_DEFAULT_PROVIDER === "gemini" ? "gemini" : "openai";
  const alternate: Provider = preferred === "openai" ? "gemini" : "openai";
  const invoke = (provider: Provider) => provider === "openai" ? openAI(messages, signal) : gemini(messages, signal);
  try { return { provider: preferred, text: await invoke(preferred) }; }
  catch (error) {
    const status = (error as { status?: number }).status;
    if (status !== undefined && !transient(status)) throw error;
    if (!(alternate === "openai" ? process.env.OPENAI_API_KEY : process.env.GEMINI_API_KEY)) throw error;
    return { provider: alternate, text: await invoke(alternate) };
  }
}
