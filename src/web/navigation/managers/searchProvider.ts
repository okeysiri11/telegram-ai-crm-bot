import type { SearchCategory, SearchHit } from "../types";
import { searchIndex } from "./searchIndex";

let recentSearches: string[] = ["crm", "ai", "invoice"];

function fuzzy(a: string, b: string): number {
  if (a === b) return 100;
  if (a.includes(b) || b.includes(a)) return 70;
  let score = 0;
  const as = new Set(a.split(""));
  for (const ch of b) if (as.has(ch)) score += 1;
  return score;
}

export const searchProvider = {
  modes: ["fuzzy", "exact", "semantic_ready"] as const,
  search(query: string, category?: SearchCategory): SearchHit[] {
    const q = query.trim().toLowerCase();
    if (q) {
      recentSearches = [q, ...recentSearches.filter((s) => s !== q)].slice(0, 10);
    }
    const docs = searchIndex.list().filter((d) => !category || d.category === category);
    if (!q) {
      return docs
        .map((d) => ({ ...d, score: d.rankBoost, match: "exact" as const }))
        .sort((a, b) => b.score - a.score);
    }
    const hits: SearchHit[] = docs
      .map((d) => {
        const hay = `${d.title} ${d.tokens.join(" ")} ${d.category}`.toLowerCase();
        const exact = hay.includes(q) || d.title.toLowerCase() === q;
        const score = (exact ? 80 : fuzzy(hay, q)) + d.rankBoost;
        return {
          ...d,
          score,
          match: exact ? ("exact" as const) : score > 20 ? ("fuzzy" as const) : ("semantic_ready" as const),
        };
      })
      .filter((h) => h.score > 15)
      .sort((a, b) => b.score - a.score);
    return hits;
  },
  suggestions(query: string) {
    return this.search(query).slice(0, 5).map((h) => h.title);
  },
  recent() {
    return [...recentSearches];
  },
  filters() {
    return searchIndex.categories();
  },
};
