import { fuzzyScore } from "./fuzzy";
import { COMMAND_CATALOG } from "./quickActions";
import { contextEngine } from "./contextEngine";
import { navigationIndex } from "./omnibox";

const intentMap: [RegExp, string][] = [
  [/\bcrm\b/i, "open_crm"],
  [/\berp\b/i, "open_erp"],
  [/beauty/i, "open_beauty"],
  [/\bauto\b/i, "open_auto"],
  [/\bagro\b/i, "open_agro"],
  [/marketplace/i, "open_marketplace"],
  [/dashboard|command center|executive/i, "open_dashboard"],
  [/mission control|\bmc\b/i, "open_mission_control"],
  [/enterprise city|\bcity\b/i, "open_enterprise_city"],
  [/workflow center|workflows?\b|automation center/i, "open_workflow_center"],
  [/builder studio|ai builder/i, "open_builder_studio"],
  [/concierge/i, "open_concierge"],
  [/ai team|agents/i, "open_ai_team"],
  [/knowledge/i, "open_knowledge"],
  [/analytics|intelligence|kpi/i, "open_analytics"],
  [/find client|search client/i, "find_client"],
  [/find employee/i, "find_employee"],
  [/create customer|new customer/i, "create_customer"],
  [/weekly report/i, "generate_weekly_report"],
  [/launch workflow|start workflow/i, "launch_workflow"],
  [/run automation/i, "run_automation"],
  [/create invoice|invoice/i, "create_invoice"],
  [/open document/i, "open_document"],
  [/mass update/i, "mass_update_records"],
  [/summarize|what.*(happening|attention)/i, "summarize_workspace"],
  [/recommend|suggestion/i, "ai_recommendations"],
  [/create task/i, "create_task"],
  [/settings/i, "open_settings"],
];

const routes: Record<string, string> = {
  open_crm: "/workspace/crm",
  open_erp: "/workspace/erp",
  open_beauty: "/workspace/beauty",
  open_auto: "/workspace/auto",
  open_agro: "/workspace/agro",
  open_marketplace: "/platform-builder/solution-hub",
  open_dashboard: "/dashboard?mode=executive",
  open_mission_control: "/platform-builder/mission-control",
  open_enterprise_city: "/enterprise-city",
  open_workflow_center: "/platform-builder/workflow-center",
  open_builder_studio: "/platform-builder/builder-studio",
  open_concierge: "/platform-builder/concierge",
  open_ai_team: "/platform-builder/ai-team",
  open_knowledge: "/platform-builder/knowledge",
  open_analytics: "/platform-builder/intelligence",
  generate_weekly_report: "/workspace/reports/weekly",
  launch_workflow: "/workspace/workflows/invoice",
  create_task: "/workspace?action=create_task",
  open_settings: "/settings",
  summarize_workspace: "/dashboard?mode=executive",
  ai_recommendations: "/dashboard",
  create_invoice: "/workspace?action=create_invoice",
};

export const aiCommandCenter = {
  interpret(utterance: string): { ok: boolean; intent?: string; route?: string; label?: string } {
    const text = utterance.trim();
    if (!text) return { ok: false };
    for (const [re, intent] of intentMap) {
      if (re.test(text)) {
        const cmd = COMMAND_CATALOG.find((c) => c.action === intent);
        const route = cmd?.route ?? routes[intent];
        contextEngine.patch({
          recentAiConversations: [
            ...contextEngine.get().recentAiConversations,
            { utterance: text, intent },
          ].slice(-20),
        });
        if (route) navigationIndex.recordUse(cmd?.id ?? intent);
        return { ok: true, intent, route, label: cmd?.label ?? intent };
      }
    }
    let best: { action: string; score: number } | null = null;
    for (const c of COMMAND_CATALOG) {
      const score = fuzzyScore(text, `${c.label} ${c.action}`);
      if (!best || score > best.score) best = { action: c.action, score };
    }
    if (best && best.score >= 0.35) {
      const cmd = COMMAND_CATALOG.find((c) => c.action === best!.action);
      return { ok: true, intent: best.action, route: cmd?.route ?? routes[best.action], label: cmd?.label };
    }
    return { ok: false };
  },
};
