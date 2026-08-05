/** Learning strip — Sprint 1.1.1 (split for code-splitting). */

import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { useLiveEnterprise } from "@/live-ops";
import { useNotificationStore } from "@/notifications/notificationStore";
import { telemetry } from "@/integrations/telemetry";
import { deriveLearning, type LearningRecommendation } from "./deriveLearning";

const CAT_LABEL: Record<LearningRecommendation["category"], string> = {
  workflow: "Workflow",
  ai_team: "AI Team",
  crm: "CRM",
  integrations: "Integrations",
  knowledge: "Knowledge",
  automation: "Automation",
};

export function LearningStrip() {
  const { snapshot } = useLiveEnterprise(true);
  const notifications = useNotificationStore((s) => s.items);
  const learning = useMemo(() => deriveLearning(snapshot, notifications), [snapshot, notifications]);
  const top = learning.recommendations[0];
  return (
    <div className="sle-strip" aria-label="Learning">
      <span className="sle-strip-label">Learning</span>
      <Badge tone="success">{learning.recommendations.length} recs</Badge>
      <Badge>~{learning.timeSavedMin} мин</Badge>
      {top ? <Badge>{CAT_LABEL[top.category]}</Badge> : null}
      <Link
        to="/platform-builder/learning"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("sle_open")}
      >
        Optimize →
      </Link>
    </div>
  );
}
