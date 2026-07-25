import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { THEME_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function ThemeEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState("dark");
  const [themeId, setThemeId] = useState("enterprise_dark");
  const [overview, setOverview] = useState<Dict | null>(null);
  const [colors, setColors] = useState<Dict | null>(null);
  const [branding, setBranding] = useState<Dict | null>(null);
  const [components, setComponents] = useState<Dict | null>(null);
  const [aiStyle, setAiStyle] = useState<Dict | null>(null);
  const [anim, setAnim] = useState<Dict | null>(null);
  const [a11y, setA11y] = useState<Dict | null>(null);
  const [switched, setSwitched] = useState<Dict | null>(null);
  const [city, setCity] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: THEME_STEPS[step],
      detailedExplanation:
        "Visual Theme Engine controls platform appearance only. Themes never contain business logic.",
      example: `Example: complete «${THEME_STEPS[step]}».`,
      popup: { title: THEME_STEPS[step], body: "Enterprise visual identity." },
      tooltip: THEME_STEPS[step],
      purpose: "Visual identity and branding",
      benefits: "Consistent dark/light enterprise appearance",
      typicalUse: "Org branding and live theme switching",
      businessValue: "Personalization without logic coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/themes/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not start session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function go(next: number) {
    setError(null);
    setBusy(true);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/themes/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1, draft: { mode, theme_id: themeId } }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Navigation failed");
    } finally {
      setBusy(false);
    }
  }

  async function load(path: string, setter: (v: Dict) => void) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/themes/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Load failed");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

  async function runSwitch() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/themes/switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme_id: themeId }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Switch failed");
      setSwitched(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Switch failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/themes/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10, draft: { mode, theme_id: themeId } }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/themes/sessions/${sid}/create`, {
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
      title="Visual Theme Engine"
      subtitle="Enterprise branding · Dark/Light · Live switching — appearance only."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Appearance Only</Badge>
        <Badge>Dark / Light</Badge>
        <Badge>Sprint 29.5</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="eds-type-small">Mode</span>
        <Input value={mode} onChange={(e) => setMode(e.target.value)} />
        <span className="eds-type-small">Theme ID</span>
        <Input value={themeId} onChange={(e) => setThemeId(e.target.value)} />
      </div>

      <ProgressIndicator current={step} total={THEME_STEPS.length} />
      <BuilderStepNav steps={[...THEME_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Theme Engine">
              <Button disabled={busy} onClick={() => void load("engine", setOverview)}>
                Load scopes
              </Button>
              {overview ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((overview.scopes as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Color System">
              <Button disabled={busy} onClick={() => void load(`colors?mode=${mode}`, setColors)}>
                Load palette
              </Button>
              {colors ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(colors.palette, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Enterprise Branding">
              <Button disabled={busy} onClick={() => void load("branding", setBranding)}>
                Load brand profile
              </Button>
              {branding ? (
                <div className="mt-3 eds-type-small space-y-1">
                  {((branding.fields as string[]) || []).map((f) => (
                    <div key={f}>{f}</div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Component Theming">
              <Button
                disabled={busy}
                onClick={() => void load(`components?theme_id=${themeId}`, setComponents)}
              >
                Theme components
              </Button>
              {components ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((components.targets as string[]) || []).map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="AI Visual Style">
              <Button disabled={busy} onClick={() => void load("ai-style", setAiStyle)}>
                Load AI styles
              </Button>
              {aiStyle ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((aiStyle.style_names as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Animation Themes">
              <Button disabled={busy} onClick={() => void load("animation", setAnim)}>
                Load animation theme
              </Button>
              {anim ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(anim.config, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Accessibility">
              <Button disabled={busy} onClick={() => void load("accessibility", setA11y)}>
                Load a11y features
              </Button>
              {a11y ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((a11y.feature_names as string[]) || []).map((f) => (
                    <li key={f}>{f}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Live Theme Switching">
              <p className="eds-type-small mb-3">Switch themes without restart — instant refresh.</p>
              <Button disabled={busy} onClick={() => void runSwitch()}>
                Switch theme
              </Button>
              {switched ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Active: {String(switched.active_theme_id)}</div>
                  <div>Restart required: {String(switched.requires_restart)}</div>
                  <div>Instant refresh: {String(switched.instant_visual_refresh)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Foundation for AI City">
              <Button disabled={busy} onClick={() => void load("ai-city", setCity)}>
                Load city theme interfaces
              </Button>
              {city ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((city.interface_names as string[]) || []).map((n) => (
                    <li key={n}>{n}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Create — Register Theme Stack">
              <p className="eds-type-small mb-3">
                Registers Theme Engine, Theme Registry, and Brand Profiles.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    created.registrations || {
                      theme_engine_id: (created.theme_engine as Dict)?.theme_engine_id,
                      theme_registry_id: (created.theme_registry as Dict)?.theme_registry_id,
                      brand_profile_id: (created.brand_profile as Dict)?.brand_profile_id,
                    },
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Back
            </Button>
            <Button
              disabled={busy || step >= THEME_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Next
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>
    </PlatformBuilderLayout>
  );
}
