export const navigationPerformance = {
  features: [
    "lazy_loading",
    "route_prefetching",
    "search_caching",
    "virtual_lists",
    "background_index_updates",
  ] as const,
  cache: new Map<string, { at: number; hits: unknown }>(),
  prefetchRoutes: ["/workspace", "/identity", "/workspace/dashboards", "/settings"],
  getCached(key: string) {
    const hit = this.cache.get(key);
    if (!hit) return null;
    if (Date.now() - hit.at > 30_000) {
      this.cache.delete(key);
      return null;
    }
    return hit.hits;
  },
  setCached(key: string, hits: unknown) {
    this.cache.set(key, { at: Date.now(), hits });
  },
};
