/**
 * Local-only favorites for selected 3D objects. No backend in this sprint.
 */

export type FavoriteRecord = {
  pickId: string;
  name: string;
  assetId: string;
};

const KEY = "odessa3d.favorites";

function read(): FavoriteRecord[] {
  try {
    const raw = globalThis.localStorage?.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as FavoriteRecord[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function write(rows: FavoriteRecord[]) {
  try {
    globalThis.localStorage?.setItem(KEY, JSON.stringify(rows));
  } catch {
    /* private mode */
  }
}

export function listFavorites(): FavoriteRecord[] {
  return read();
}

export function isFavorite(pickId: string): boolean {
  return read().some((r) => r.pickId === pickId);
}

export function toggleFavorite(row: FavoriteRecord): boolean {
  const cur = read();
  const idx = cur.findIndex((r) => r.pickId === row.pickId);
  if (idx >= 0) {
    cur.splice(idx, 1);
    write(cur);
    return false;
  }
  cur.push(row);
  write(cur);
  return true;
}
