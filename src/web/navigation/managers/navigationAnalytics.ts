type SearchEvent = { query: string; hits: number; abandoned: boolean };

const paths: string[] = [];
const searches: SearchEvent[] = [];
const pageTimes = new Map<string, number[]>();

export const navigationAnalytics = {
  trackPath(path: string) {
    paths.push(path);
    if (paths.length > 200) paths.shift();
  },
  trackSearch(query: string, hits: number) {
    searches.push({ query, hits, abandoned: hits === 0 && query.trim().length > 0 });
    if (searches.length > 200) searches.shift();
  },
  trackPageTime(path: string, ms: number) {
    const arr = pageTimes.get(path) ?? [];
    arr.push(ms);
    pageTimes.set(path, arr);
  },
  snapshot() {
    const popular = new Map<string, number>();
    for (const p of paths) popular.set(p, (popular.get(p) ?? 0) + 1);
    return {
      navigation_paths: [...paths].slice(-50),
      popular_pages: [...popular.entries()]
        .map(([path, count]) => ({ path, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 15),
      search_statistics: {
        total: searches.length,
        abandoned: searches.filter((s) => s.abandoned).length,
      },
      abandoned_searches: searches.filter((s) => s.abandoned).length,
      time_per_page: Object.fromEntries(
        [...pageTimes.entries()].map(([k, v]) => [k, v.reduce((a, b) => a + b, 0) / v.length]),
      ),
      ai_recommendations: ["pin_top_crm_pages", "enable_workspace_prefetch", "review_abandoned_searches"],
    };
  },
};
