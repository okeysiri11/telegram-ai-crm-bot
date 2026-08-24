/** Short non-secret stamp so a phone can tell LIVE tunnel from Chrome's offline copy. */
export const ADOS_LIVE_STAMP = "k7p2";

export function liveBuildLabel(host = typeof window === "undefined" ? "" : window.location.hostname): string | null {
  const tunnel = /\.trycloudflare\.com$/i.test(host);
  if (!import.meta.env.DEV && !tunnel) return null;
  return `LIVE • ${ADOS_LIVE_STAMP}`;
}
