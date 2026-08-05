/**
 * AI Intent interpretation — Sprint 28.7.
 * Execution always goes through commandRuntime.routeAiIntent / execute.
 */

import { fuzzyScore } from "../../../command-center/managers/fuzzy";
import { COMMAND_CATALOG } from "../../../command-center/managers/quickActions";
import { contextEngine } from "../../../command-center/managers/contextEngine";

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
  [/weekly report/i, "generate_weekly_report"],
  [/launch workflow|start workflow/i, "launch_workflow"],
  [/run automation/i, "run_automation"],
  [/create invoice|invoice/i, "create_invoice"],
  [/summarize|what.*(happening|attention)/i, "summarize_workspace"],
  [/recommend|suggestion/i, "ai_recommendations"],
  [/create task/i, "create_task"],
  [/settings/i, "open_settings"],
  [/ai studio/i, "open_ai_studio"],
  [/production/i, "qa_production"],
  [/workflow|automation flow/i, "start_workflow"],
  [/undo/i, "sys_undo"],
  [/redo/i, "sys_redo"],
];

export type AiIntentResult = {
  ok: boolean;
  intent?: string;
  commandId?: string;
  route?: string;
  label?: string;
  utterance: string;
};

export function interpretAiIntent(utterance: string): AiIntentResult {
  const text = utterance.trim();
  if (!text) return { ok: false, utterance: text };

  for (const [re, intent] of intentMap) {
    if (re.test(text)) {
      const cmd = COMMAND_CATALOG.find((c) => c.action === intent);
      contextEngine.patch({
        recentAiConversations: [
          ...contextEngine.get().recentAiConversations,
          { utterance: text, intent },
        ].slice(-20),
      });
      return {
        ok: true,
        intent,
        commandId: cmd?.id || intent,
        route: cmd?.route,
        label: cmd?.label ?? intent,
        utterance: text,
      };
    }
  }

  let best: { action: string; score: number; id: string; route?: string; label: string } | null = null;
  for (const c of COMMAND_CATALOG) {
    const score = fuzzyScore(text, `${c.label} ${c.action}`);
    if (!best || score > best.score) {
      best = { action: c.action, score, id: c.id, route: c.route, label: c.label };
    }
  }
  if (best && best.score >= 0.35) {
    return {
      ok: true,
      intent: best.action,
      commandId: best.id,
      route: best.route,
      label: best.label,
      utterance: text,
    };
  }
  return { ok: false, utterance: text };
}
