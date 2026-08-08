/**
 * Sprint 42.3 / 46.4 — Auto Human AI bar → UnifiedIntentBar (same UX all verticals).
 */

import { UnifiedIntentBar } from "@/workspace-chrome/unified-intent";

export function HumanAiCommandBar({
  moduleId = "auto",
}: {
  moduleId?: string;
}) {
  return (
    <div data-testid="human-ai-bar" data-module={moduleId}>
      <UnifiedIntentBar verticalId={moduleId} showQuickHints showRecent />
    </div>
  );
}
