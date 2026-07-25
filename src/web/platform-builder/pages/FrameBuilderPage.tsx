import { BuilderFramework } from "../framework/BuilderFramework";
import { getBuilder } from "../managers/builderRegistry";
import { GENERIC_STEPS } from "../types";

export function FrameBuilderPage({ builderId }: { builderId: string }) {
  const builder = getBuilder(builderId);
  return (
    <BuilderFramework
      builderId={builderId}
      title={builder?.name || "Builder"}
      purpose={builder?.purpose || "Framework-only builder ready for future implementation."}
      steps={builder?.steps || GENERIC_STEPS}
      frameOnly
    />
  );
}
