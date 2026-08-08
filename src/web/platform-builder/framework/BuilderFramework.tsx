import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Switch } from "@/ui";
import { FRAMEWORK_PHASES } from "../types";
import { helpFor } from "../managers/builderRegistry";
import { useAcademyStore } from "../managers/academyStore";
import { BuilderStepNav } from "./BuilderStepNav";
import { HelpPanel } from "./HelpPanel";
import { PreviewWindow } from "./PreviewWindow";
import { ProgressIndicator } from "./ProgressIndicator";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { bu } from "../i18n/builderUiRu";
import { builderDisplayName } from "@/i18n/platformGlossary";

type Props = {
  builderId: string;
  title: string;
  purpose?: string;
  steps: readonly string[];
  frameOnly?: boolean;
  note?: string;
  openWorkspaceRoute?: string;
};

export function BuilderFramework({
  builderId,
  title,
  purpose,
  steps,
  frameOnly = true,
  note,
  openWorkspaceRoute,
}: Props) {
  const [current, setCurrent] = useState(0);
  const [created, setCreated] = useState(false);
  const mode = useAcademyStore((s) => s.mode);
  const learning = useAcademyStore((s) => s.isLearningEnabled(builderId));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const step = steps[current] || steps[0];
  const displayTitle = builderDisplayName(builderId, title);
  const help = useMemo(() => helpFor(step, displayTitle), [step, displayTitle]);
  const guided = learning && mode === "guided_learning";
  const phase = FRAMEWORK_PHASES[Math.min(current, FRAMEWORK_PHASES.length - 1)];
  const isLastStep = current >= steps.length - 1;
  const modeRu =
    mode === "quick_start" ? "Быстрый старт" : mode === "guided_learning" ? "Обучение" : "Эксперт";

  return (
    <PlatformBuilderLayout title={displayTitle} subtitle={purpose || bu("frameworkSubtitle")}>
      <div className="flex flex-wrap items-center gap-3">
        <Badge>{frameOnly ? bu("frame") : bu("ready")}</Badge>
        {frameOnly ? <Badge tone="warning">{bu("planned")}</Badge> : null}
        <Badge>
          {bu("phase")} · {phase}
        </Badge>
        <Badge>
          {bu("academy")} · {modeRu}
        </Badge>
        {!frameOnly ? (
          <Switch
            checked={learning}
            onChange={(v) => toggleLearning(builderId, v)}
            label={bu("learningMode")}
          />
        ) : null}
      </div>

      {note ? <p className="eds-type-small text-[var(--eds-text-muted)]">{note}</p> : null}

      <ProgressIndicator current={current} total={steps.length} />
      <BuilderStepNav steps={steps} current={current} onChange={setCurrent} />

      <div className="eds-grid eds-grid--dashboard">
        <Card title={`${bu("step")} · ${step}`}>
          <p className="eds-type-small">
            {bu("configureStep")} <strong>{step}</strong>
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              variant="ghost"
              disabled={current === 0}
              onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            >
              {bu("back")}
            </Button>
            <Button
              disabled={current >= steps.length - 1}
              onClick={() => setCurrent((c) => Math.min(steps.length - 1, c + 1))}
            >
              {bu("next")}
            </Button>
            {frameOnly ? (
              isLastStep ? (
                openWorkspaceRoute ? (
                  <Link to={openWorkspaceRoute}>
                    <Button variant="primary">{bu("openWorkspace")}</Button>
                  </Link>
                ) : (
                  <Button variant="primary" disabled>
                    {bu("planned")}
                  </Button>
                )
              ) : null
            ) : (
              <Button
                variant="primary"
                disabled={!isLastStep}
                onClick={() => setCreated(true)}
              >
                {bu("create")}
              </Button>
            )}
          </div>
          {created ? <p className="mt-3 eds-type-small text-[var(--eds-success)]">{bu("ready")}</p> : null}
        </Card>

        <HelpPanel help={help} guided={guided} />
        <PreviewWindow title={displayTitle} summary={`${bu("step")}: ${step}`} />
      </div>
    </PlatformBuilderLayout>
  );
}
