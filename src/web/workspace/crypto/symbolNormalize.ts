/** Client-side symbol normalize (mirrors backend aliases). */

export function normalizeSymbolClient(raw: string): string {
  const key = (raw || "").trim().toUpperCase().replace(/\s+/g, "");
  const map: Record<string, string> = {
    EURUSD: "EUR/USD",
    "EUR/USD": "EUR/USD",
    "EUR-USD": "EUR/USD",
    DXY: "DXY",
    DX: "DXY",
    USDX: "DXY",
  };
  const spaced = key.replace(/-/g, "/");
  if (map[spaced]) return map[spaced];
  const compact = key.replace(/[/-]/g, "");
  if (map[compact]) return map[compact];
  return spaced || key;
}
