/** Fuzzy subsequence + token overlap scorer. */
export function fuzzyScore(query: string, text: string): number {
  const q = query.trim().toLowerCase();
  const t = text.toLowerCase();
  if (!q) return 0;
  if (q === t) return 1;
  if (t.includes(q)) return 0.85 + Math.min(0.1, q.length / Math.max(t.length, 1));
  let qi = 0;
  for (const ch of t) {
    if (qi < q.length && ch === q[qi]) qi += 1;
  }
  if (qi === q.length) return 0.55 + 0.2 * (q.length / Math.max(t.length, 1));
  const qTokens = new Set(q.match(/[a-z0-9]+/g) ?? []);
  const tTokens = new Set(t.match(/[a-z0-9]+/g) ?? []);
  if (!qTokens.size) return 0;
  let overlap = 0;
  for (const tok of qTokens) if (tTokens.has(tok)) overlap += 1;
  return (overlap / qTokens.size) * 0.5;
}
