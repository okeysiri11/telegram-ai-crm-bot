import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Checkbox, Input, Switch, Tooltip } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { useAcademyStore } from "../managers/academyStore";
import { PLATFORM_BUILDER_API } from "../types";
import {
  AI_EXPLANATION,
  AI_MODES,
  BRAND_COLORS,
  BUSINESS_SIZES,
  CONCIERGE_MODES,
  DASHBOARD_WIDGETS,
  INDUSTRIES,
  MODULES,
  VERTICAL_WIZARD_STEPS,
  emptyDraft,
  type HelpBits,
  type VerticalDraft,
} from "./catalog";

function makeHelp(purpose: string, benefits: string, example: string, what = ""): HelpBits {
  return {
    shortDescription: what || purpose,
    purpose,
    benefits,
    example,
    businessValue: benefits,
    tooltip: purpose,
    moreInformation: `${purpose} ${benefits}`,
  };
}

function toHelpContent(h: HelpBits) {
  return {
    shortDescription: h.shortDescription,
    detailedExplanation: h.moreInformation,
    example: h.example,
    popup: { title: h.shortDescription, body: h.purpose },
    tooltip: h.tooltip,
    purpose: h.purpose,
    benefits: h.benefits,
    typicalUse: h.example,
    businessValue: h.businessValue,
  };
}

function toggleList(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

export function VerticalWizard() {
  const [step, setStep] = useState(0);
  const [orgId, setOrgId] = useState("org_demo");
  const [draft, setDraft] = useState<VerticalDraft>(emptyDraft());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [created, setCreated] = useState<Record<string, unknown> | null>(null);
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mode = useAcademyStore((s) => s.mode);
  const learning = useAcademyStore((s) => s.isLearningEnabled("vertical"));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const guided = learning && mode === "guided_learning";

  const brand = BRAND_COLORS.find((c) => c.id === draft.brandColor) || BRAND_COLORS[0];

  const help = useMemo(() => {
    const title = VERTICAL_WIZARD_STEPS[step];
    if (step === 1 && draft.industry) {
      const ind = INDUSTRIES.find((i) => i.id === draft.industry);
      if (ind) return toHelpContent(ind.help);
    }
    return toHelpContent(
      makeHelp(
        `This screen helps you set «${title}».`,
        "Clear vertical choices make the organization easier to operate.",
        `Example: complete «${title}» before moving on.`,
        title,
      ),
    );
  }, [step, draft.industry]);

  function patch(p: Partial<VerticalDraft>) {
    setDraft((d) => ({ ...d, ...p }));
    setCreated(null);
  }

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/vertical/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ organization_id: orgId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not start Vertical session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function syncDraft(sid: string, stepNumber: number) {
    const payload = {
      step: stepNumber,
      organization_id: orgId,
      draft: {
        name: draft.name,
        description: draft.description,
        industry: draft.industry,
        industry_custom: draft.industryCustom,
        business_size: draft.businessSize,
        logo: draft.logo,
        brand_color: draft.brandColor,
        modules: draft.modules,
        ai_mode: draft.aiMode,
        concierge_mode: draft.conciergeMode,
        dashboard_widgets: draft.dashboardWidgets,
        workspace_name: draft.workspaceName || `${draft.name || "Vertical"} Workspace`,
        departments: draft.departments,
        menus: draft.menus,
        navigation: draft.navigation,
        owner_name: draft.ownerName,
      },
    };
    const patchRes = await fetch(`${PLATFORM_BUILDER_API}/vertical/sessions/${sid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const patchBody = await patchRes.json();
    if (!patchRes.ok) throw new Error(patchBody.error || "Could not save Vertical");
  }

  async function loadPreview() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await syncDraft(sid, 8);
      const res = await fetch(`${PLATFORM_BUILDER_API}/vertical/sessions/${sid}/preview`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Could not load preview");
      setPreview(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preview failed");
    } finally {
      setBusy(false);
    }
  }

  async function syncAndCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await syncDraft(sid, 10);
      const create = await fetch(`${PLATFORM_BUILDER_API}/vertical/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const createBody = await create.json();
      if (!create.ok) throw new Error(createBody.error || "Could not create Vertical");
      setCreated(createBody);
      setPreview((createBody.organization_preview as Record<string, unknown>) || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Vertical Builder"
      subtitle="Visually create complete Enterprise Verticals without programming. Every object gets Logical + Visual representation."
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge>Operational</Badge>
        <Badge>Platform Registry</Badge>
        <Badge>Visual Layer</Badge>
        <Badge>Academy · {mode}</Badge>
        <Switch
          checked={learning}
          onChange={(v) => toggleLearning("vertical", v)}
          label="Learning mode"
        />
      </div>

      <ProgressIndicator current={step} total={VERTICAL_WIZARD_STEPS.length} />
      <BuilderStepNav steps={[...VERTICAL_WIZARD_STEPS]} current={step} onChange={setStep} />

      <div className="eds-grid eds-grid--dashboard">
        <Card title={VERTICAL_WIZARD_STEPS[step]}>
          {step === 0 ? (
            <div className="space-y-3">
              <Input
                placeholder="Organization ID"
                value={orgId}
                onChange={(e) => {
                  setOrgId(e.target.value);
                  setSessionId(null);
                }}
              />
              <Input
                placeholder="Vertical name (required)"
                value={draft.name}
                onChange={(e) => patch({ name: e.target.value })}
              />
              <Input
                placeholder="Description"
                value={draft.description}
                onChange={(e) => patch({ description: e.target.value })}
              />
              <div className="flex flex-wrap gap-2">
                {BUSINESS_SIZES.map((s) => (
                  <Button
                    key={s.id}
                    variant={draft.businessSize === s.id ? "primary" : "secondary"}
                    onClick={() => patch({ businessSize: s.id })}
                  >
                    {s.name}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {BRAND_COLORS.map((c) => (
                  <Button
                    key={c.id}
                    variant={draft.brandColor === c.id ? "primary" : "ghost"}
                    onClick={() => patch({ brandColor: c.id })}
                  >
                    <span
                      className="mr-2 inline-block h-3 w-3 rounded-full"
                      style={{ background: c.hex }}
                    />
                    {c.name}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {["logo_mark", "logo_shield", "logo_wave"].map((logo) => (
                  <Button
                    key={logo}
                    variant={draft.logo === logo ? "primary" : "secondary"}
                    onClick={() => patch({ logo })}
                  >
                    Logo · {logo.replace("logo_", "")}
                  </Button>
                ))}
              </div>
            </div>
          ) : null}

          {step === 1 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {INDUSTRIES.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => patch({ industry: item.id })}
                  className={`rounded-md border p-3 text-left eds-type-small ${
                    draft.industry === item.id
                      ? "border-[var(--eds-primary)] bg-[var(--eds-primary-soft)]"
                      : "border-[var(--eds-border)]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <strong>{item.name}</strong>
                    <Tooltip label={item.help.tooltip}>
                      <span className="eds-type-caption text-[var(--eds-primary)]">Info</span>
                    </Tooltip>
                  </div>
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                  {guided ? (
                    <p className="mt-1 eds-type-caption">
                      Benefits: {item.help.benefits} · Use: {item.help.typicalUseCases} ·{" "}
                      {item.help.example}
                    </p>
                  ) : null}
                </button>
              ))}
              {draft.industry === "custom" ? (
                <Input
                  className="sm:col-span-2"
                  placeholder="Describe custom industry"
                  value={draft.industryCustom}
                  onChange={(e) => patch({ industryCustom: e.target.value })}
                />
              ) : null}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {MODULES.map((item) => (
                <label key={item.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={draft.modules.includes(item.id)}
                      onChange={() => patch({ modules: toggleList(draft.modules, item.id) })}
                    />
                    {item.name}
                  </span>
                  <p className="mt-1 text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                  {guided ? (
                    <p className="mt-1 eds-type-caption">
                      Value: {item.help.benefits} · {item.help.example}
                    </p>
                  ) : null}
                </label>
              ))}
            </div>
          ) : null}

          {step === 3 ? (
            <div className="space-y-3">
              <p className="eds-type-small text-[var(--eds-text-muted)]">{AI_EXPLANATION}</p>
              <div className="grid gap-2 sm:grid-cols-2">
                {AI_MODES.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => patch({ aiMode: item.id })}
                    className={`rounded-md border p-3 text-left eds-type-small ${
                      draft.aiMode === item.id
                        ? "border-[var(--eds-primary)]"
                        : "border-[var(--eds-border)]"
                    }`}
                  >
                    <strong>{item.name}</strong>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                  </button>
                ))}
              </div>
              {draft.aiMode === "launch_ai_builder" ? (
                <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/builder-studio?mode=wizard">
                  Open AI Builder →
                </Link>
              ) : (
                <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/ai-team">
                  Open AI Team Center →
                </Link>
              )}
            </div>
          ) : null}

          {step === 4 ? (
            <div className="space-y-3">
              <div className="grid gap-2 sm:grid-cols-2">
                {CONCIERGE_MODES.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => patch({ conciergeMode: item.id })}
                    className={`rounded-md border p-3 text-left eds-type-small ${
                      draft.conciergeMode === item.id
                        ? "border-[var(--eds-primary)]"
                        : "border-[var(--eds-border)]"
                    }`}
                  >
                    <strong>{item.name}</strong>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                  </button>
                ))}
              </div>
              {draft.conciergeMode === "create_new" ? (
                <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/concierge">
                  Open Concierge Builder →
                </Link>
              ) : null}
            </div>
          ) : null}

          {step === 5 ? (
            <div className="space-y-3">
              <div className="grid gap-2 sm:grid-cols-2">
                {DASHBOARD_WIDGETS.map((item) => (
                  <label key={item.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                    <span className="inline-flex items-center gap-2">
                      <Checkbox
                        checked={draft.dashboardWidgets.includes(item.id)}
                        onChange={() =>
                          patch({ dashboardWidgets: toggleList(draft.dashboardWidgets, item.id) })
                        }
                      />
                      {item.name}
                    </span>
                  </label>
                ))}
              </div>
              <Card title="Live dashboard preview">
                <div className="grid gap-2 sm:grid-cols-2">
                  {draft.dashboardWidgets.map((id) => (
                    <div
                      key={id}
                      className="rounded-md border border-[var(--eds-border)] p-3 eds-type-caption"
                      style={{ borderLeft: `3px solid ${brand.hex}` }}
                    >
                      {DASHBOARD_WIDGETS.find((w) => w.id === id)?.name || id}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          ) : null}

          {step === 6 ? (
            <div className="space-y-3">
              <Input
                placeholder="Workspace name"
                value={draft.workspaceName}
                onChange={(e) => patch({ workspaceName: e.target.value })}
              />
              <Input
                placeholder="Departments (comma separated)"
                value={draft.departments.join(", ")}
                onChange={(e) =>
                  patch({
                    departments: e.target.value
                      .split(",")
                      .map((x) => x.trim())
                      .filter(Boolean),
                  })
                }
              />
              <Input
                placeholder="Menus (comma separated)"
                value={draft.menus.join(", ")}
                onChange={(e) =>
                  patch({
                    menus: e.target.value
                      .split(",")
                      .map((x) => x.trim())
                      .filter(Boolean),
                  })
                }
              />
              <Input
                placeholder="Owner name"
                value={draft.ownerName}
                onChange={(e) => patch({ ownerName: e.target.value })}
              />
            </div>
          ) : null}

          {step === 7 ? (
            <div className="space-y-3">
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Organization Map shows Owner, Concierge, Departments, AI Team, Connections, and Future AI
                City Position. Compatible with AI Operations Center.
              </p>
              <Button disabled={busy} onClick={() => void loadPreview()}>
                {busy ? "Loading…" : "Refresh organization preview"}
              </Button>
              {preview ? (
                <Card title="Organization Map">
                  <ul className="space-y-1 eds-type-small">
                    <li>Owner: {String(preview.owner)}</li>
                    <li>
                      Concierge:{" "}
                      {String((preview.concierge as { name?: string } | null)?.name || "—")}
                    </li>
                    <li>Departments: {(preview.departments as string[] | undefined)?.join(", ")}</li>
                    <li>Modules: {(preview.modules as string[] | undefined)?.join(", ")}</li>
                    <li>
                      AI City:{" "}
                      {JSON.stringify(preview.future_ai_city_position || {})}
                    </li>
                    <li>Nodes: {(preview.nodes as unknown[] | undefined)?.length || 0}</li>
                    <li>Connections: {(preview.connections as unknown[] | undefined)?.length || 0}</li>
                  </ul>
                </Card>
              ) : null}
            </div>
          ) : null}

          {step === 8 ? (
            <Card title={`Vertical Card · ${draft.name || "Unnamed"}`}>
              <ul className="space-y-1 eds-type-small">
                <li>
                  Brand: {brand.name} · {brand.hex} · {draft.logo}
                </li>
                <li>
                  Industry:{" "}
                  {draft.industry === "custom"
                    ? draft.industryCustom || "Custom"
                    : INDUSTRIES.find((i) => i.id === draft.industry)?.name || "—"}
                </li>
                <li>Modules: {draft.modules.join(", ") || "—"}</li>
                <li>Departments: {draft.departments.join(", ")}</li>
                <li>AI mode: {draft.aiMode}</li>
                <li>Concierge: {draft.conciergeMode}</li>
                <li>Dashboards: {draft.dashboardWidgets.join(", ")}</li>
                <li>Workspace: {draft.workspaceName || `${draft.name || "Vertical"} Workspace`}</li>
                <li>Knowledge: Industry playbooks, SOPs</li>
              </ul>
            </Card>
          ) : null}

          {step === 9 ? (
            <div className="space-y-3">
              <p className="eds-type-small">
                Create registers Vertical, Modules, Workspace, AI, Concierge, Knowledge, Dashboard, and
                Organization in Platform Registry, and prepares the Visual Layer.
              </p>
              {error ? <p className="eds-type-small text-[var(--eds-danger)]">{error}</p> : null}
              {created ? (
                <Card title="Created">
                  <p className="eds-type-small">
                    Platform Registry connected · Visual Layer ready · AI Team connected · Concierge
                    connected
                  </p>
                  <pre className="mt-2 max-h-48 overflow-auto eds-type-caption">
                    {JSON.stringify(
                      {
                        vertical_id: (created.vertical as { object_id?: string })?.object_id,
                        registry: created.registry,
                        visual_layer_ready: (created.visual_layer as { ready?: boolean })?.ready,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </Card>
              ) : (
                <Button variant="primary" disabled={busy} onClick={() => void syncAndCreate()}>
                  {busy ? "Creating…" : "Create Vertical"}
                </Button>
              )}
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
              Back
            </Button>
            <Button
              disabled={step >= VERTICAL_WIZARD_STEPS.length - 1}
              onClick={() => setStep((s) => Math.min(VERTICAL_WIZARD_STEPS.length - 1, s + 1))}
            >
              Next
            </Button>
          </div>
        </Card>

        <HelpPanel help={help} guided={guided} />

        <Card title="Live preview">
          <div
            className="rounded-md border border-[var(--eds-border)] p-4"
            style={{ borderTop: `4px solid ${brand.hex}` }}
          >
            <p className="eds-type-small font-semibold">{draft.name || "Untitled Vertical"}</p>
            <p className="eds-type-caption text-[var(--eds-text-muted)]">
              {draft.description || "Description appears here"}
            </p>
            <p className="mt-2 eds-type-caption">
              Size: {draft.businessSize} · Modules: {draft.modules.length} · Widgets:{" "}
              {draft.dashboardWidgets.length}
            </p>
          </div>
        </Card>

        <Card title="Architecture">
          <p className="eds-type-small">Logical Representation + Visual Representation</p>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Prepared for AI Operations Center, AI Team Center, 2D AI City, and future 3D visualization.
          </p>
        </Card>
      </div>
    </PlatformBuilderLayout>
  );
}
