/** Bounded retry with exponential backoff for Vanguard tracking. Failure never blocks apply. */

export type TrackingDelivery = "DELIVERED" | "RETRYING" | "FAILED";

const MAX_ATTEMPTS = 4;
const BASE_MS = 300;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function postWithRetry(
  url: string,
  body: Record<string, unknown>,
  extraHeaders: Record<string, string> = {},
): Promise<{ ok: boolean; delivery_status: TrackingDelivery; json: Record<string, unknown> }> {
  let last: Record<string, unknown> = {};
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt += 1) {
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...extraHeaders },
        body: JSON.stringify(body),
      });
      const json = (await res.json().catch(() => ({}))) as Record<string, unknown>;
      last = json;
      if (res.ok && json.ok !== false) {
        return { ok: true, delivery_status: "DELIVERED", json };
      }
      if (res.status === 400) {
        return { ok: false, delivery_status: "FAILED", json };
      }
    } catch {
      last = {};
    }
    if (attempt < MAX_ATTEMPTS - 1) {
      await sleep(BASE_MS * 2 ** attempt);
    }
  }
  return { ok: false, delivery_status: "FAILED", json: last };
}
