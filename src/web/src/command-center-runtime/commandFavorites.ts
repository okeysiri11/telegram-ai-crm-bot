const FAV_KEY = "ews_cc_favorites_v1";
const RECENT_KEY = "ews_cc_recent_v1";

function readList(key: string): string[] {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as string[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeList(key: string, ids: string[]) {
  try {
    localStorage.setItem(key, JSON.stringify(ids.slice(0, 40)));
  } catch {
    /* ignore */
  }
}

const DEFAULT_FAVORITES = [
  "act_open_crm",
  "act_create_client",
  "act_open_dashboard_exec",
  "act_create_project",
  "act_open_ai_studio",
];

export const commandFavorites = {
  list(): string[] {
    const stored = typeof window !== "undefined" ? readList(FAV_KEY) : [];
    return stored.length ? stored : [...DEFAULT_FAVORITES];
  },
  toggle(id: string): string[] {
    const cur = this.list();
    const next = cur.includes(id) ? cur.filter((x) => x !== id) : [id, ...cur].slice(0, 20);
    writeList(FAV_KEY, next);
    return next;
  },
  isFavorite(id: string): boolean {
    return this.list().includes(id);
  },
};

export const commandRecent = {
  list(): string[] {
    return typeof window !== "undefined" ? readList(RECENT_KEY) : [];
  },
  push(id: string): string[] {
    const next = [id, ...this.list().filter((x) => x !== id)].slice(0, 20);
    writeList(RECENT_KEY, next);
    return next;
  },
};
