import { useMemo, useState } from "react";
import { Badge, Button, Card, Switch } from "@/ui";
import { FRAMEWORK_PHASES } from "../types";
import { helpFor } from "../managers/builderRegistry";
import { useAcademyStore } from "../managers/academyStore";
import { BuilderStepNav } from "./BuilderStepNav";
import { HelpPanel } from "./HelpPanel";
import { PreviewWindow } from "./PreviewWindow";
import { ProgressIndicator } from "./ProgressIndicator";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";

type Props = {
  builderId: string;
  title: string;
  purpose?: string;
  steps: readonly string[];
  frameOnly?: boolean;
  note?: string;
};

export function BuilderFramework({
  builderId,
  title,
  purpose,
  steps,
  frameOnly = true,
  note,
}: Props) {
  const [current, setCurrent] = useState(0);
  const [created, setCreated] = useState(false);
  const mode = useAcademyStore((s) => s.mode);
  const learning = useAcademyStore((s) => s.isLearningEnabled(builderId));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const step = steps[current] || steps[0];
  const help = useMemo(() => helpFor(step, title), [step, title]);
  const guided = learning && mode === "guided_learning";
  const phase = FRAMEWORK_PHASES[Math.min(current, FRAMEWORK_PHASES.length - 1)];

  return (
    <PlatformBuilderLayout
      title={title}
      subtitle={purpose || "Builder Framework · Step → Explanation → Information → Example → Preview → Create"}
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge>{frameOnly ? "Frame only" : "Operational"}</Badge>
        <Badge>Phase · {phase}</Badge>
        <Badge>Academy · {mode}</Badge>
        <Switch
          checked={learning}
          onChange={(v) => toggleLearning(builderId, v)}
          label="Learning mode"
        />
      </div>

      {note ? <p className="eds-type-small text-[var(--eds-text-muted)]">{note}</p> : null}

      <ProgressIndicator current={current} total={steps.length} />
      <BuilderStepNav steps={steps} current={current} onChange={setCurrent} />

      <div className="eds-grid eds-grid--dashboard">
        <Card title={`Step · ${step}`}>
          <p className="eds-type-small">
            Configure <strong>{step}</strong> using the shared Builder Framework.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              variant="ghost"
              disabled={current === 0}
              onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            >
              Back
            </Button>
            <Button
              disabled={current >= steps.length - 1}
              onClick={() => setCurrent((c) => Math.min(steps.length - 1, c + 1))}
            >
              Next
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setCurrent(steps.length - 1);
                setCreated(true);
              }}
            >
              Create
            </Button>
          </div>
        </Card>

        <HelpPanel help={help} guided={guided} />

        <PreviewWindow
          title={title}
          summary={
            created
              ? `${title} draft recorded — navigation frame complete.`
              : `Live preview for «${step}».`
          }
          payload={{ builderId, step, phase, frameOnly }}
        />
      </div>
    </PlatformBuilderLayout>
  );
}
