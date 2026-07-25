import { useMemo, useState } from "react";
import { Badge, Button, Card, Checkbox, Input, Switch } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PreviewWindow } from "../framework/PreviewWindow";
import { ConfirmationScreen } from "../framework/ConfirmationScreen";
import { LiveValidation } from "../framework/LiveValidation";
import { useAcademyStore } from "../managers/academyStore";
import { PLATFORM_BUILDER_API } from "../types";
import {
  EXTENSION_TYPES,
  LIFECYCLE,
  PREVIEW_CAPABILITIES,
  TARGET_BUILDERS,
  UBF_STEPS,
  UI_COMPONENTS,
  VALIDATION_RULES,
  emptyUbfDraft,
  type UbfDraft,
} from "./catalog";

function toggleList(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

export function UniversalFrameworkStudio() {
  const [step, setStep] = useState(0);
  const [draft, setDraft] = useState<UbfDraft>(emptyUbfDraft());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [validation, setValidation] = useState<{
    ok?: boolean;
    errors?: { field?: string; message: string }[];
    suggestions?: string[];
  } | null>(null);
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [created, setCreated] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mode = useAcademyStore((s) => s.mode);
  const learning = useAcademyStore((s) => s.isLearningEnabled("universal_framework"));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const guided = learning && mode === "guided_learning";

  const help = useMemo(
    () => ({
      shortDescription: UBF_STEPS[step],
      detailedExplanation:
        "Universal Builder Framework gives every Platform Builder one lifecycle, UI kit, validation, preview, registry, templates, extensions, and SDK foundation.",
      example: `Example: complete «${UBF_STEPS[step]}» then continue.`,
      popup: { title: UBF_STEPS[step], body: "Shared architecture for all builders." },
      tooltip: UBF_STEPS[step],
      purpose: "One common architecture",
      benefits: "Future builders ship with minimal effort",
      typicalUse: "AI, Concierge, Vertical, CRM, ERP, and more",
      businessValue: "Faster builder delivery with consistent UX",
    }),
    [step],
  );

  function patch(p: Partial<UbfDraft>) {
    setDraft((d) => ({ ...d, ...p }));
    setCreated(null);
  }

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    await fetch(`${PLATFORM_BUILDER_API}/ubf/bootstrap`, { method: "POST", body: "{}" });
    const res = await fetch(`${PLATFORM_BUILDER_API}/ubf/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not start UBF session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function syncDraft(sid: string, stepNumber: number) {
    const res = await fetch(`${PLATFORM_BUILDER_API}/ubf/sessions/${sid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        step: stepNumber,
        draft: {
          name: draft.name,
          builder_type: draft.builderType,
          version: draft.version,
          components: draft.components,
          validation_rules: draft.validationRules,
          save_as_template: draft.saveAsTemplate,
          extensions: draft.extensions,
          steps: [...UBF_STEPS],
          schema: { type: "object", properties: { name: { type: "string" } } },
          dependencies: ["builder_engine", "help_system"],
          knowledge_topics: ["builder_framework"],
        },
      }),
    });
    const body = await res.json();
    if (!res.ok) throw new Error(body.error || "Could not save session");
  }

  async function runValidate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await syncDraft(sid, 3);
      const res = await fetch(`${PLATFORM_BUILDER_API}/ubf/sessions/${sid}/validate`, {
        method: "POST",
        body: "{}",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Validation failed");
      setValidation(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Validation failed");
    } finally {
      setBusy(false);
    }
  }

  async function runPreview() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await syncDraft(sid, 4);
      const res = await fetch(`${PLATFORM_BUILDER_API}/ubf/sessions/${sid}/preview`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Preview failed");
      setPreview(body);
      setValidation((body.realtime_validation as typeof validation) || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await syncDraft(sid, 10);
      const res = await fetch(`${PLATFORM_BUILDER_API}/ubf/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Create failed");
      setCreated(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Universal Builder Framework"
      subtitle="One architecture for every Builder — lifecycle, UI, validation, preview, registry, templates, extensions, SDK."
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge>Operational</Badge>
        <Badge>Builder Registry</Badge>
        <Badge>SDK Foundation</Badge>
        <Badge>Academy · {mode}</Badge>
        <Switch
          checked={learning}
          onChange={(v) => toggleLearning("universal_framework", v)}
          label="Learning mode"
        />
      </div>

      <ProgressIndicator current={step} total={UBF_STEPS.length} />
      <BuilderStepNav steps={[...UBF_STEPS]} current={step} onChange={setStep} />

      <div className="eds-grid eds-grid--dashboard">
        <Card title={UBF_STEPS[step]}>
          {step === 0 ? (
            <div className="space-y-3">
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Common lifecycle for every Builder:
              </p>
              <div className="flex flex-wrap gap-2">
                {LIFECYCLE.map((p) => (
                  <Badge key={p}>{p}</Badge>
                ))}
              </div>
              <Input
                placeholder="New builder name"
                value={draft.name}
                onChange={(e) => patch({ name: e.target.value })}
              />
              <Input
                placeholder="builder_type (e.g. document)"
                value={draft.builderType}
                onChange={(e) => patch({ builderType: e.target.value })}
              />
              <Input
                placeholder="Version"
                value={draft.version}
                onChange={(e) => patch({ version: e.target.value })}
              />
            </div>
          ) : null}

          {step === 1 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {UI_COMPONENTS.map((c) => (
                <label key={c} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={draft.components.includes(c)}
                      onChange={() => patch({ components: toggleList(draft.components, c) })}
                    />
                    {c}
                  </span>
                </label>
              ))}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="space-y-3">
              <div className="grid gap-2 sm:grid-cols-2">
                {VALIDATION_RULES.map((r) => (
                  <label key={r.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                    <span className="inline-flex items-center gap-2">
                      <Checkbox
                        checked={draft.validationRules.includes(r.id)}
                        onChange={() =>
                          patch({ validationRules: toggleList(draft.validationRules, r.id) })
                        }
                      />
                      {r.name}
                    </span>
                  </label>
                ))}
              </div>
              <Button disabled={busy} onClick={() => void runValidate()}>
                Run live validation
              </Button>
              {validation ? (
                <LiveValidation
                  ok={validation.ok}
                  errors={validation.errors}
                  suggestions={validation.suggestions}
                />
              ) : null}
            </div>
          ) : null}

          {step === 3 ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {PREVIEW_CAPABILITIES.map((c) => (
                  <Badge key={c}>{c}</Badge>
                ))}
              </div>
              <Button disabled={busy} onClick={() => void runPreview()}>
                Refresh live preview
              </Button>
              {preview ? (
                <pre className="max-h-40 overflow-auto eds-type-caption">
                  {JSON.stringify(preview.visual_summary, null, 2)}
                </pre>
              ) : null}
            </div>
          ) : null}

          {step === 4 ? (
            <div className="space-y-2">
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Automatically register Builder Type, Version, Schema, Components, Templates, Validation
                Rules.
              </p>
              <div className="flex flex-wrap gap-2">
                {TARGET_BUILDERS.map((b) => (
                  <Badge key={b}>{b}</Badge>
                ))}
              </div>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="space-y-3">
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Save Builders as Templates. Clone existing Builders. Duplicate configurations.
              </p>
              <label className="flex items-center gap-2 eds-type-small">
                <Checkbox
                  checked={draft.saveAsTemplate}
                  onChange={() => patch({ saveAsTemplate: !draft.saveAsTemplate })}
                />
                Save as template on create
              </label>
            </div>
          ) : null}

          {step === 6 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {EXTENSION_TYPES.map((e) => (
                <label key={e} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={draft.extensions.includes(e)}
                      onChange={() => patch({ extensions: toggleList(draft.extensions, e) })}
                    />
                    {e}
                  </span>
                </label>
              ))}
            </div>
          ) : null}

          {step === 7 ? (
            <div className="space-y-2">
              <Badge>Architecture only</Badge>
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Builder SDK foundation exposes Framework APIs: define_builder, register_steps,
                attach_validation, attach_components, save_template, clone_builder, run_lifecycle.
              </p>
            </div>
          ) : null}

          {step === 8 ? (
            <Card title="Framework Summary">
              <ul className="space-y-1 eds-type-small">
                <li>Configuration: {draft.name || "—"} · {draft.builderType || "—"} · v{draft.version}</li>
                <li>Validation rules: {draft.validationRules.length}</li>
                <li>Dependencies: builder_engine, help_system</li>
                <li>Objects: builder, template, components, schema</li>
                <li>Registry: platform_builder_builder_registry</li>
              </ul>
            </Card>
          ) : null}

          {step === 9 ? (
            <div className="space-y-3">
              {error ? <p className="eds-type-small text-[var(--eds-danger)]">{error}</p> : null}
              {created ? (
                <Card title="Registered">
                  <p className="eds-type-small">Builder, template, components, and schema registered.</p>
                  <pre className="mt-2 max-h-48 overflow-auto eds-type-caption">
                    {JSON.stringify(
                      {
                        builder: created.builder,
                        template: created.template,
                        sdk: created.sdk_foundation,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </Card>
              ) : (
                <ConfirmationScreen
                  title="Create & Register"
                  message="Register Builder, Template, Components, and Schema in the Builder Registry."
                  confirmLabel={busy ? "Creating…" : "Create Builder"}
                  busy={busy}
                  onConfirm={() => void runCreate()}
                />
              )}
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
              Back
            </Button>
            <Button
              disabled={step >= UBF_STEPS.length - 1}
              onClick={() => setStep((s) => Math.min(UBF_STEPS.length - 1, s + 1))}
            >
              Next
            </Button>
          </div>
        </Card>

        <HelpPanel help={help} guided={guided} />

        <PreviewWindow
          title="Live Preview"
          summary={`${draft.name || "Untitled"} · ${draft.builderType || "type"} · ${draft.components.length} components`}
        />

        <Card title="Target Builders">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            AI · Concierge · Vertical · Workflow · CRM · ERP · Knowledge · Marketplace · Dashboard ·
            Automation · Document · Department · User · Future
          </p>
        </Card>
      </div>
    </PlatformBuilderLayout>
  );
}
