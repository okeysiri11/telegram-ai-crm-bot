import { BuilderFramework } from "../framework/BuilderFramework";
import { AI_BUILDER_STEPS } from "../types";

export function AIBuilderPage() {
  return (
    <BuilderFramework
      builderId="ai"
      title="AI Builder"
      purpose="Compose AI agent teams — navigation frame (business logic arrives later)."
      steps={AI_BUILDER_STEPS}
      frameOnly
    />
  );
}
