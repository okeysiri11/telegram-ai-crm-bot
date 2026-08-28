import type { SearchCategory, SearchHit } from "../types";
import { searchIndex } from "./searchIndex";
import { collapseCasinoSearchHits } from "@/casino/casinoPlatform";

let recentSearches: string[] = ["crm", "ai", "invoice"];

function fuzzy(a: string, b: string): number {
  if (a === b) return 100;
  if (a.includes(b) || b.includes(a)) return 70;
  let score = 0;
  const as = new Set(a.split(""));
  for (const ch of b) if (as.has(ch)) score += 1;
  return score;
}

const GROUP_ORDER: SearchCategory[] = [
  "crm",
  "erp",
  "ai_agents",
  "documents",
  "projects",
  "knowledge",
  "users",
  "commands",
  "modules",
  "workflows",
  "tasks",
  "organizations",
  "dashboards",
  "applications",
];

const GROUP_LABELS: Partial<Record<SearchCategory, string>> = {
  crm: "Клиенты",
  erp: "ERP",
  ai_agents: "AI-Агенты",
  documents: "Документы",
  projects: "Проекты",
  knowledge: "Знания",
  users: "Пользователи",
  commands: "Команды",
  modules: "Модули / Настройки",
  workflows: "Процессы",
  tasks: "Задачи",
  organizations: "Компании",
  dashboards: "Панели",
  applications: "Приложения",
};

export type SearchGroup = {
  category: SearchCategory;
  label: string;
  hits: SearchHit[];
};

export const searchProvider = {
  modes: ["fuzzy", "exact", "semantic_ready"] as const,
  search(query: string, category?: SearchCategory): SearchHit[] {
    const q = query.trim().toLowerCase();
    if (q) {
      recentSearches = [q, ...recentSearches.filter((s) => s !== q)].slice(0, 10);
    }
    const docs = searchIndex.list().filter((d) => !category || d.category === category);
    if (!q) {
      return collapseCasinoSearchHits(
        docs
          .map((d) => ({ ...d, score: d.rankBoost, match: "exact" as const }))
          .sort((a, b) => b.score - a.score),
      );
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
    return collapseCasinoSearchHits(hits);
  },
  /** Sprint 27.4 — grouped results for Search Workspace / palette. */
  searchGrouped(query: string, limitPerGroup = 6): SearchGroup[] {
    const hits = this.search(query);
    const map = new Map<SearchCategory, SearchHit[]>();
    for (const h of hits) {
      const list = map.get(h.category) || [];
      if (list.length < limitPerGroup) list.push(h);
      map.set(h.category, list);
    }
    const ordered: SearchGroup[] = [];
    for (const cat of GROUP_ORDER) {
      const groupHits = map.get(cat);
      if (groupHits?.length) {
        ordered.push({
          category: cat,
          label: GROUP_LABELS[cat] || cat,
          hits: groupHits,
        });
        map.delete(cat);
      }
    }
    for (const [cat, groupHits] of map) {
      if (groupHits.length) {
        ordered.push({
          category: cat,
          label: GROUP_LABELS[cat] || cat,
          hits: groupHits,
        });
      }
    }
    return ordered;
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
