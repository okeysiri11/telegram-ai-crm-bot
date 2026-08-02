/**
 * Sprint 33.1 — Quick Action sections for Ctrl+K palette.
 */

import type { AiNavigationIntent } from "./aiNavigationIntents";
import { AI_NAVIGATION_INTENTS } from "./aiNavigationIntents";
import { SIMPLE_MODE_NAV } from "./simpleModeNav";
import type { ExperienceMode } from "./experienceModeStore";

export type UxPaletteCommand = {
  id: string;
  section: string;
  label: string;
  route?: string;
  opensPalette?: boolean;
  requiresPro?: boolean;
  keywords: string[];
};

export const QUICK_ACTION_SECTIONS = [
  { id: "open_module", label: "Open Module", labelRu: "Открыть модуль" },
  { id: "create_object", label: "Create Object", labelRu: "Создать объект" },
  { id: "run_workflow", label: "Run Workflow", labelRu: "Запустить процесс" },
  { id: "search_everything", label: "Search Everything", labelRu: "Искать всё" },
  { id: "ask_ai", label: "Ask AI", labelRu: "Спросить AI" },
] as const;

export function buildUxPaletteCommands(mode: ExperienceMode): UxPaletteCommand[] {
  const cmds: UxPaletteCommand[] = [];

  for (const item of SIMPLE_MODE_NAV) {
    cmds.push({
      id: `mod_${item.id}`,
      section: "open_module",
      label: item.label,
      route: item.opensPalette ? undefined : item.route,
      opensPalette: item.opensPalette,
      keywords: [item.label, item.id, "module", "модуль"],
    });
  }

  if (mode === "pro") {
    const proModules = [
      { id: "erp", label: "ERP", route: "/erp" },
      { id: "kg", label: "Граф знаний", route: "/platform-builder/knowledge" },
      { id: "gov", label: "Governance", route: "/platform-builder/governance" },
      { id: "mp", label: "Маркетплейс", route: "/marketplace" },
      { id: "studio", label: "AI Studio", route: "/ai-studio" },
      { id: "runtime", label: "AI Runtime", route: "/platform-builder/runtime" },
      { id: "security", label: "Безопасность", route: "/identity/security" },
      { id: "city", label: "Enterprise City", route: "/city" },
    ];
    for (const m of proModules) {
      cmds.push({
        id: `pro_${m.id}`,
        section: "open_module",
        label: m.label,
        route: m.route,
        requiresPro: true,
        keywords: [m.label, m.id, "pro"],
      });
    }
  }

  const creates = AI_NAVIGATION_INTENTS.filter((i) => i.type === "create");
  for (const c of creates) {
    cmds.push(intentToCommand(c, "create_object"));
  }

  cmds.push({
    id: "wf_production",
    section: "run_workflow",
    label: "Запустить производство",
    route: "/erp?view=production",
    requiresPro: true,
    keywords: ["workflow", "production", "производство"],
  });
  cmds.push({
    id: "wf_overdue",
    section: "run_workflow",
    label: "Обзор просроченных проектов",
    route: "/projects?view=overdue",
    keywords: ["workflow", "overdue", "проекты"],
  });

  cmds.push({
    id: "search_all",
    section: "search_everything",
    label: "Искать по платформе",
    route: "/search",
    opensPalette: true,
    keywords: ["search", "поиск", "everything"],
  });

  cmds.push({
    id: "ask_ai_cmd",
    section: "ask_ai",
    label: "Спросить AI-ассистента",
    route: "/ai-agents",
    keywords: ["ask", "ai", "помощь"],
  });

  return cmds.filter((c) => mode === "pro" || !c.requiresPro);
}

function intentToCommand(intent: AiNavigationIntent, section: string): UxPaletteCommand {
  return {
    id: `intent_${intent.id}`,
    section,
    label: intent.label,
    route: intent.route,
    requiresPro: intent.requiresPro,
    keywords: intent.phrases,
  };
}
