import type { SlotFilterId, SlotGameDefinition, SlotSymbolDef } from "./slotTypes";

function sym(id: string, label: string, weight: number, payout: number): SlotSymbolDef {
  return { id, label, weight, payout };
}

const SHARED = {
  reelCount: 5,
  rowCount: 3,
  paylines: 3,
  minBet: 10,
  maxBet: 100,
  betSteps: [10, 25, 50, 100],
  demoStartingBalance: 10_000,
  availability: "demo" as const,
  currencySupport: ["DEMO"] as ["DEMO"],
  demoAvailable: true as const,
  realAvailable: false as const,
  provider: "Odessa Prime Demo",
  providerId: "odessa-prime-demo",
};

export const SLOT_CATALOG: SlotGameDefinition[] = [
  {
    ...SHARED,
    id: "olympus-crown",
    slug: "olympus-crown",
    title: "Olympus Crown",
    subtitle: "Гром Олимпа",
    theme: "olympus",
    accent: "#5ad4ff",
    accent2: "#e8d5a3",
    externalGameId: "demo-olympus-crown",
    cabinetVariant: "curved",
    jackpot: "1 248 600",
    tags: ["new", "popular", "jackpot"],
    symbols: [
      sym("ZEUS", "⚡", 8, 12),
      sym("CROWN", "👑", 10, 8),
      sym("OWL", "🦉", 14, 5),
      sym("LAUREL", "🌿", 16, 3),
      sym("URN", "🏺", 18, 2),
      sym("BOLT", "✦", 12, 4),
    ],
  },
  {
    ...SHARED,
    id: "candy-fortune",
    slug: "candy-fortune",
    title: "Candy Fortune",
    subtitle: "Сладкая удача",
    theme: "candy",
    accent: "#ff7ad9",
    accent2: "#c084fc",
    externalGameId: "demo-candy-fortune",
    cabinetVariant: "slim",
    jackpot: "886 420",
    tags: ["new", "popular"],
    symbols: [
      sym("CANDY", "🍭", 10, 9),
      sym("CAKE", "🍰", 12, 6),
      sym("HEART", "💗", 14, 4),
      sym("STAR", "⭐", 12, 5),
      sym("WRAP", "🎀", 16, 3),
      sym("GEM", "💎", 8, 10),
    ],
  },
  {
    ...SHARED,
    id: "pharaohs-book",
    slug: "pharaohs-book",
    title: "Pharaoh's Book",
    subtitle: "Книга песков",
    theme: "egypt",
    accent: "#e8b86d",
    accent2: "#c9a45c",
    externalGameId: "demo-pharaohs-book",
    cabinetVariant: "square",
    jackpot: "2 104 090",
    tags: ["classic", "jackpot"],
    symbols: [
      sym("BOOK", "📜", 8, 12),
      sym("ANUBIS", "🐺", 10, 8),
      sym("EYE", "👁", 12, 6),
      sym("SCARAB", "🪲", 14, 4),
      sym("ANKH", "☥", 16, 3),
      sym("GOLD", "✨", 12, 5),
    ],
  },
  {
    ...SHARED,
    id: "big-catch",
    slug: "big-catch",
    title: "Big Catch",
    subtitle: "Большой улов",
    theme: "sea",
    accent: "#3da9fc",
    accent2: "#7dd3fc",
    externalGameId: "demo-big-catch",
    cabinetVariant: "slim",
    jackpot: "654 880",
    tags: ["popular"],
    symbols: [
      sym("FISH", "🐟", 12, 6),
      sym("HOOK", "🪝", 14, 4),
      sym("WAVE", "🌊", 16, 3),
      sym("ANCHOR", "⚓", 12, 5),
      sym("CHEST", "🧰", 8, 10),
      sym("PEARL", "🤍", 10, 8),
    ],
  },
  {
    ...SHARED,
    id: "buffalo-fortune",
    slug: "buffalo-fortune",
    title: "Buffalo Fortune",
    subtitle: "Дикая прерия",
    theme: "buffalo",
    accent: "#ff7a3d",
    accent2: "#f59e0b",
    externalGameId: "demo-buffalo-fortune",
    cabinetVariant: "square",
    jackpot: "1 772 310",
    tags: ["popular", "jackpot"],
    symbols: [
      sym("BUFFALO", "🦬", 8, 12),
      sym("FEATHER", "🪶", 12, 5),
      sym("SUN", "🌅", 14, 4),
      sym("CACTUS", "🌵", 16, 3),
      sym("HORN", "📯", 12, 6),
      sym("COIN", "🪙", 10, 8),
    ],
  },
  {
    ...SHARED,
    id: "lady-emerald",
    slug: "lady-emerald",
    title: "Lady Emerald",
    subtitle: "Изумрудная леди",
    theme: "emerald",
    accent: "#34d399",
    accent2: "#c9a45c",
    externalGameId: "demo-lady-emerald",
    cabinetVariant: "curved",
    jackpot: "931 050",
    tags: ["classic", "new"],
    symbols: [
      sym("LADY", "💚", 8, 12),
      sym("EMERALD", "🟢", 10, 8),
      sym("RING", "💍", 12, 6),
      sym("ROSE", "🌹", 14, 4),
      sym("FAN", "🪭", 16, 3),
      sym("PEARL", "🤍", 12, 5),
    ],
  },
];

export const SLOT_FILTERS: Array<{ id: SlotFilterId; label: string }> = [
  { id: "all", label: "Все" },
  { id: "new", label: "Новые" },
  { id: "popular", label: "Популярные" },
  { id: "classic", label: "Classic" },
  { id: "jackpot", label: "Jackpot" },
];

export function getSlotDefinition(id: string): SlotGameDefinition | undefined {
  return SLOT_CATALOG.find((item) => item.id === id || item.slug === id);
}

export function filterSlotCatalog(query: string, filter: SlotFilterId): SlotGameDefinition[] {
  const q = query.trim().toLowerCase();
  return SLOT_CATALOG.filter((item) => {
    if (filter !== "all" && !item.tags.includes(filter)) return false;
    if (!q) return true;
    return (
      item.title.toLowerCase().includes(q) ||
      item.subtitle.toLowerCase().includes(q) ||
      item.theme.toLowerCase().includes(q) ||
      item.provider.toLowerCase().includes(q)
    );
  });
}

export function symbolLabel(def: SlotGameDefinition, id: string): string {
  return def.symbols.find((item) => item.id === id)?.label || id;
}
