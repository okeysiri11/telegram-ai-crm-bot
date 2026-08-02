import { COMMAND_CATALOG } from "../../command-center/managers/quickActions";
import { commandAnalytics } from "../../command-center/managers/analytics";
import { DEVELOPER_COMMANDS } from "./developerCommands";
import { commandFavorites, commandRecent } from "./commandFavorites";
import type { CommandItem } from "../../command-center/types";
import {
  buildUxPaletteCommands,
  matchAiNavigationIntent,
  useExperienceModeStore,
  type ExperienceMode,
} from "@/ux-revolution";

export type PaletteSectionId =
  | "recent"
  | "favorites"
  | "ai"
  | "developer"
  | "navigate"
  | "create"
  | "workflow"
  | "ask_ai"
  | "all";

export type PaletteSection = {
  id: PaletteSectionId;
  label: string;
  items: CommandItem[];
};

function byId(id: string): CommandItem | undefined {
  return COMMAND_CATALOG.find((c) => c.id === id || c.action === id) || DEVELOPER_COMMANDS.find((c) => c.id === id);
}

function resolveIds(ids: string[]): CommandItem[] {
  return ids.map(byId).filter(Boolean) as CommandItem[];
}

function uxCommandsAsItems(mode: ExperienceMode): CommandItem[] {
  return buildUxPaletteCommands(mode).map((c) => ({
    id: c.id,
    kind:
      c.section === "create_object"
        ? ("create" as const)
        : c.section === "run_workflow"
          ? ("run_workflow" as const)
          : c.section === "ask_ai"
            ? ("ai_execute" as const)
            : ("open_module" as const),
    action: c.id,
    label: c.label,
    route: c.route,
    keywords: c.keywords,
  }));
}

function currentMode(): ExperienceMode {
  try {
    return useExperienceModeStore.getState().mode;
  } catch {
    return "simple";
  }
}

/** Build VS Code–style sections for an empty palette query. Sprint 33.1 adds UX quick actions. */
export function buildPaletteSections(): PaletteSection[] {
  const mode = currentMode();
  const ux = uxCommandsAsItems(mode);
  const recentIds = commandRecent.list();
  const popular = commandAnalytics.snapshot().popular_commands.map((p) => p.id);
  const recent = resolveIds([...recentIds, ...popular].filter((v, i, a) => a.indexOf(v) === i)).slice(0, 8);
  const favorites = resolveIds(commandFavorites.list()).slice(0, 8);
  const ai = [
    ...ux.filter((c) => c.kind === "ai_execute"),
    ...COMMAND_CATALOG.filter((c) => c.kind === "ai_execute" || c.keywords.includes("ai")),
  ].slice(0, 8);
  const navigate = [
    ...ux.filter((c) => c.kind === "open_module"),
    ...COMMAND_CATALOG.filter((c) => c.kind === "open" || c.kind === "navigate" || c.kind === "open_module"),
  ].slice(0, 12);
  const create = [
    ...ux.filter((c) => c.kind === "create"),
    ...COMMAND_CATALOG.filter((c) => c.kind === "create"),
  ].slice(0, 10);
  const workflow = ux.filter((c) => c.kind === "run_workflow").slice(0, 8);

  return [
    { id: "recent" as const, label: "Recent", items: recent },
    { id: "favorites" as const, label: "Favorites", items: favorites },
    { id: "navigate" as const, label: "Open Module", items: navigate },
    { id: "create" as const, label: "Create Object", items: create },
    { id: "workflow" as const, label: "Run Workflow", items: workflow },
    { id: "ask_ai" as const, label: "Ask AI", items: ai },
    { id: "ai" as const, label: "AI commands", items: ai },
    ...(mode === "pro"
      ? [{ id: "developer" as const, label: "Developer", items: DEVELOPER_COMMANDS }]
      : []),
  ].filter((s) => s.items.length > 0);
}

export function allPaletteCommands(): CommandItem[] {
  const ux = uxCommandsAsItems(currentMode());
  const mode = currentMode();
  const base = mode === "pro" ? [...COMMAND_CATALOG, ...DEVELOPER_COMMANDS] : [...COMMAND_CATALOG];
  return [...ux, ...base];
}

export function searchPaletteCommands(query: string): CommandItem[] {
  const q = query.trim().toLowerCase();
  const all = allPaletteCommands();
  if (!q) return all.slice(0, 20);

  const intent = matchAiNavigationIntent(query);
  const intentItems: CommandItem[] = intent
    ? [
        {
          id: `ai_intent_${intent.id}`,
          kind: intent.type === "create" ? "create" : intent.type === "palette" ? "ai_execute" : "navigate",
          action: intent.id,
          label: `AI · ${intent.label}`,
          route: intent.route,
          keywords: intent.phrases,
        },
      ]
    : [];

  const tokens = q.split(/\s+/).filter(Boolean);
  const fuzzy = all
    .filter((c) => {
      const hay = `${c.label} ${c.action} ${c.keywords.join(" ")} ${c.kind}`.toLowerCase();
      return tokens.every((t) => hay.includes(t));
    })
    .slice(0, 30);

  const seen = new Set<string>();
  return [...intentItems, ...fuzzy].filter((c) => {
    if (seen.has(c.id)) return false;
    seen.add(c.id);
    return true;
  });
}
