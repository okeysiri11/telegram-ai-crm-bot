/**
 * Asset registry — deduplicates GLB loads and tracks lifecycle.
 */

import type { CityAsset, AssetStatus } from "./types";

export class AssetRegistry {
  private assets = new Map<string, CityAsset>();
  private urlIndex = new Map<string, string>();

  register(asset: Omit<CityAsset, "status"> & { status?: AssetStatus }): CityAsset {
    const existing = this.assets.get(asset.id);
    if (existing) return existing;
    const urlKey = asset.url.trim().toLowerCase();
    const byUrl = this.urlIndex.get(urlKey);
    if (byUrl) return this.assets.get(byUrl)!;

    const row: CityAsset = {
      ...asset,
      status: asset.status ?? "idle",
      object3D: asset.object3D ?? null,
    };
    this.assets.set(row.id, row);
    this.urlIndex.set(urlKey, row.id);
    return row;
  }

  get(id: string): CityAsset | undefined {
    return this.assets.get(id);
  }

  getByUrl(url: string): CityAsset | undefined {
    const id = this.urlIndex.get(url.trim().toLowerCase());
    return id ? this.assets.get(id) : undefined;
  }

  update(id: string, patch: Partial<CityAsset>): CityAsset | undefined {
    const cur = this.assets.get(id);
    if (!cur) return undefined;
    Object.assign(cur, patch);
    return cur;
  }

  list(): CityAsset[] {
    return [...this.assets.values()];
  }

  byStatus(status: AssetStatus): CityAsset[] {
    return this.list().filter((a) => a.status === status);
  }

  counts() {
    const rows = this.list();
    return {
      total: rows.length,
      loaded: rows.filter((a) => a.status === "loaded").length,
      failed: rows.filter((a) => a.status === "failed").length,
      queued: rows.filter((a) => a.status === "queued").length,
      loading: rows.filter((a) => a.status === "loading").length,
      realGlb: rows.filter((a) => a.source === "REAL_GLB" && a.status === "loaded").length,
    };
  }

  unload(id: string) {
    const row = this.assets.get(id);
    if (!row) return;
    row.object3D = null;
    row.status = "unloaded";
  }
}
