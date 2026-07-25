import { BuilderFramework } from "../framework/BuilderFramework";
import { CONCIERGE_STEPS } from "../types";

export function ConciergeBuilderPage() {
  return (
    <BuilderFramework
      builderId="concierge"
      title="Concierge Builder"
      purpose="Separate from AI Agents. Only one Concierge per organization."
      steps={CONCIERGE_STEPS}
      frameOnly
      note="Concierge is an organization companion — not part of the AI Agents fleet."
    />
  );
}
