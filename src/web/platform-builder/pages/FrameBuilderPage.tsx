import { BuilderFramework } from "../framework/BuilderFramework";
import { getBuilder } from "../managers/builderRegistry";
import { GENERIC_STEPS } from "../types";
import { builderDisplayName } from "@/i18n/platformGlossary";

export function FrameBuilderPage({ builderId }: { builderId: string }) {
  const builder = getBuilder(builderId);
  return (
    <BuilderFramework
      builderId={builderId}
      title={builderDisplayName(builderId, builder?.name)}
      purpose={
        builder?.purpose
          ? // purpose in catalog may still be EN — show RU frame note
            "Превью-конструктор. Полная реализация подключается через рабочее пространство."
          : "Каркасный конструктор готов к будущей реализации."
      }
      steps={builder?.steps || GENERIC_STEPS}
      frameOnly
      openWorkspaceRoute={builder?.openWorkspaceRoute}
    />
  );
}
