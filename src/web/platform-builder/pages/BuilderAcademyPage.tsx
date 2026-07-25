import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ACADEMY_MODES } from "../managers/builderRegistry";
import { useAcademyStore } from "../managers/academyStore";

export function BuilderAcademyPage() {
  const mode = useAcademyStore((s) => s.mode);
  const setMode = useAcademyStore((s) => s.setMode);

  return (
    <PlatformBuilderLayout
      title="Builder Academy"
      subtitle="Interactive learning for every Platform Builder."
    >
      <div className="eds-grid eds-grid--dashboard">
        {ACADEMY_MODES.map((m) => (
          <Card key={m.id} title={m.name}>
            <p className="eds-type-small text-[var(--eds-text-muted)]">{m.description}</p>
            <div className="mt-3 flex items-center gap-2">
              <Button
                variant={mode === m.id ? "primary" : "secondary"}
                onClick={() => setMode(m.id)}
              >
                {mode === m.id ? "Active" : "Select"}
              </Button>
              {m.id === "guided_learning" ? <Badge>Explains every screen</Badge> : null}
            </div>
          </Card>
        ))}
      </div>
      <Card title="Active mode">
        <p className="eds-type-small">
          Current: <strong>{mode}</strong>. Each builder can enable or disable learning mode from
          its own toolbar.
        </p>
      </Card>
    </PlatformBuilderLayout>
  );
}
