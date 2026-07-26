/**
 * Daily Brief preference — show once per calendar day.
 */

const KEY = "ewp_daily_brief_dismissed_v1";

function todayKey(d = new Date()): string {
  return d.toISOString().slice(0, 10);
}

export function isDailyBriefDismissed(d = new Date()): boolean {
  try {
    return localStorage.getItem(KEY) === todayKey(d);
  } catch {
    return false;
  }
}

export function dismissDailyBrief(d = new Date()): void {
  try {
    localStorage.setItem(KEY, todayKey(d));
  } catch {
    /* ignore */
  }
}

export function resetDailyBriefPref(): void {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
