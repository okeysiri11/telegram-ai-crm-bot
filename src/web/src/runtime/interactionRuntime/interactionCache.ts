/**
 * Interaction cache — context · selection · incremental — Sprint 29.6.
 */

import type { InteractionContext, InteractionTarget, SelectionState, SearchHit } from "./interactionTypes";

let contextCache: InteractionContext | null = null;
let selectionCache: SelectionState | null = null;
let catalogCache: InteractionTarget[] = [];
let catalogKey = "";
let searchCache = new Map<string, SearchHit[]>();
let revision = 0;

export const interactionCache = {
  clear() {
    contextCache = null;
    selectionCache = null;
    catalogCache = [];
    catalogKey = "";
    searchCache.clear();
    revision = 0;
  },

  revision() {
    return revision;
  },

  putContext(ctx: InteractionContext) {
    contextCache = { ...ctx, vars: { ...ctx.vars } };
    revision += 1;
    return contextCache;
  },

  getContext() {
    return contextCache ? { ...contextCache, vars: { ...contextCache.vars } } : null;
  },

  putSelection(sel: SelectionState) {
    selectionCache = { ...sel, targets: [...sel.targets] };
    revision += 1;
    return selectionCache;
  },

  getSelection() {
    return selectionCache ? { ...selectionCache, targets: [...selectionCache.targets] } : null;
  },

  putCatalog(key: string, targets: InteractionTarget[]) {
    if (catalogKey === key && catalogCache.length) return catalogCache;
    catalogKey = key;
    catalogCache = [...targets];
    revision += 1;
    return catalogCache;
  },

  getCatalog() {
    return [...catalogCache];
  },

  catalogValid(key: string) {
    return catalogKey === key && catalogCache.length > 0;
  },

  putSearch(query: string, hits: SearchHit[]) {
    searchCache.set(query.toLowerCase(), hits);
    if (searchCache.size > 40) {
      const first = searchCache.keys().next().value;
      if (first) searchCache.delete(first);
    }
  },

  getSearch(query: string) {
    return searchCache.get(query.toLowerCase()) || null;
  },

  stats() {
    return {
      revision,
      hasContext: !!contextCache,
      hasSelection: !!selectionCache,
      catalogSize: catalogCache.length,
      searchEntries: searchCache.size,
    };
  },
};
