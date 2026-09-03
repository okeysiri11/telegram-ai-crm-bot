/**
 * Honest FX quote formatting — never render NaN / non-finite mids.
 */

export function formatFxQuote(value: unknown, digits = 4): string | null {
  if (value == null || value === "") return null;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed || trimmed === "—" || trimmed.toLowerCase() === "nan" || trimmed.toLowerCase() === "нет данных") {
      return null;
    }
    const n = Number(trimmed.replace(",", "."));
    if (!Number.isFinite(n)) return null;
    return n.toFixed(digits);
  }
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) return null;
  return n.toFixed(digits);
}

export function fxWatchlistQuoteRow(pair: string, quote: Record<string, unknown>, digits: number) {
  const mid = formatFxQuote(quote.mid, digits);
  const bid = formatFxQuote(quote.bid ?? quote.mid, digits);
  const ask = formatFxQuote(quote.ask ?? quote.mid, digits);
  const change = formatFxQuote(quote.change, 4);
  return {
    id: pair,
    pair,
    bid: bid ?? "—",
    ask: ask ?? "—",
    change: change ?? "—",
    updated: quote.fetched_at ? String(quote.fetched_at) : mid ? "—" : "нет данных",
    source: String(quote.source || quote.provider || "—"),
  };
}
