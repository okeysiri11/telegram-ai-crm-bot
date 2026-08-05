/**
 * Sprint 30.9 — AI Prompt Security (client-side firewall).
 * Extends aiTaskSecurity — not a parallel AI engine.
 */

import { appendAuditVault } from "@/audit-vault";

export type PromptRiskLevel = "safe" | "suspicious" | "blocked";

export type PromptSecurityResult = {
  ok: boolean;
  risk: PromptRiskLevel;
  sanitized: string;
  reasons: string[];
  tokenEstimate: number;
  truncated: boolean;
};

export type PromptSecurityContext = {
  actor: string;
  orgId: string;
  workspaceId: string;
  maxTokens?: number;
};

/** Instruction-override / jailbreak / exfiltration heuristics (deny-list). */
const UNSAFE_PATTERNS: RegExp[] = [
  /ignore\s+(all\s+)?(previous|prior|above)\s+instructions?/i,
  /disregard\s+(all\s+)?(previous|prior|system)\s+/i,
  /you\s+are\s+now\s+(dan|jailbroken|unrestricted)/i,
  /system\s*prompt\s*:/i,
  /reveal\s+(your\s+)?(system|hidden)\s+prompt/i,
  /exfiltrat(e|ion)/i,
  /do\s+anything\s+now/i,
  /bypass\s+(safety|security|filter|guardrail)/i,
  /<\s*script\b/i,
  /\b(drop|truncate)\s+table\b/i,
  /\bunion\s+select\b/i,
  /\$\{.*\}/,
  /`{3}[\s\S]*system/i,
];

const ABUSE_BURST_KEY = "ewp_ai_prompt_burst_v1";
const ABUSE_WINDOW_MS = 60_000;
const ABUSE_MAX = 40;

export function estimateTokens(text: string): number {
  // Rough heuristic (~4 chars/token) — aligns with platform_memory truncate approach
  return Math.max(1, Math.ceil(text.trim().length / 4));
}

export function sanitizePrompt(input: string): string {
  let out = input.replace(/\u0000/g, "");
  out = out.replace(/[\u200B-\u200F\u202A-\u202E]/g, "");
  out = out.replace(/<\s*script[\s\S]*?>[\s\S]*?<\s*\/\s*script\s*>/gi, "[removed]");
  out = out.replace(/on\w+\s*=\s*["'][^"']*["']/gi, "");
  return out.trim();
}

export function detectUnsafePrompt(input: string): string[] {
  const reasons: string[] = [];
  for (const re of UNSAFE_PATTERNS) {
    if (re.test(input)) reasons.push(`pattern:${re.source.slice(0, 48)}`);
  }
  if (input.length > 32_000) reasons.push("length_extreme");
  return reasons;
}

function abuseCount(): number {
  try {
    const raw = sessionStorage.getItem(ABUSE_BURST_KEY);
    if (!raw) return 0;
    const data = JSON.parse(raw) as { t: number; n: number };
    if (Date.now() - data.t > ABUSE_WINDOW_MS) return 0;
    return data.n;
  } catch {
    return 0;
  }
}

function bumpAbuse(): number {
  const n = abuseCount() + 1;
  try {
    sessionStorage.setItem(ABUSE_BURST_KEY, JSON.stringify({ t: Date.now(), n }));
  } catch {
    /* ignore */
  }
  return n;
}

export function detectAiAbuse(): { abused: boolean; count: number } {
  const count = bumpAbuse();
  return { abused: count > ABUSE_MAX, count };
}

/**
 * Prompt Firewall — validate → sanitize → token cap → abuse check.
 */
export function guardPrompt(raw: string, ctx: PromptSecurityContext): PromptSecurityResult {
  const reasons: string[] = [];
  const maxTokens = ctx.maxTokens ?? 4096;
  let sanitized = sanitizePrompt(raw || "");

  if (!sanitized) {
    return { ok: false, risk: "blocked", sanitized: "", reasons: ["empty"], tokenEstimate: 0, truncated: false };
  }

  const unsafe = detectUnsafePrompt(sanitized);
  reasons.push(...unsafe);

  const abuse = detectAiAbuse();
  if (abuse.abused) reasons.push(`abuse_rate:${abuse.count}`);

  let truncated = false;
  let tokenEstimate = estimateTokens(sanitized);
  if (tokenEstimate > maxTokens) {
    const maxChars = maxTokens * 4;
    sanitized = sanitized.slice(0, maxChars);
    truncated = true;
    tokenEstimate = estimateTokens(sanitized);
    reasons.push("token_truncated");
  }

  const blocked = unsafe.length > 0 || abuse.abused;
  const risk: PromptRiskLevel = blocked ? "blocked" : reasons.length ? "suspicious" : "safe";

  return {
    ok: !blocked,
    risk,
    sanitized,
    reasons,
    tokenEstimate,
    truncated,
  };
}

export async function auditAiPrompt(
  ctx: PromptSecurityContext,
  result: PromptSecurityResult,
  action = "prompt.guard",
) {
  return appendAuditVault({
    actor: ctx.actor,
    action: `ai_security.${action}`,
    resource: `org=${ctx.orgId};ws=${ctx.workspaceId}`,
    detail: `risk=${result.risk};tokens=${result.tokenEstimate};reasons=${result.reasons.join("|") || "none"}`,
    correlationId: `ai_sec_${ctx.orgId}`,
  });
}

/** Validate prompt and throw on block (for task / studio entry points). */
export async function enforcePromptSecurity(
  raw: string,
  ctx: PromptSecurityContext,
): Promise<PromptSecurityResult> {
  const result = guardPrompt(raw, ctx);
  await auditAiPrompt(ctx, result);
  if (!result.ok) {
    throw new Error(`AI security: запрос заблокирован (${result.reasons.join(", ")})`);
  }
  return result;
}
