import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { RENDER_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function RenderingEngineStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [renderer, setRenderer] = useState<Dict | null>(null);
  const [lod, setLod] = useState<Dict | null>(null);
  const [viewport, setViewport] = useState<Dict | null>(null);
  const [layers, setLayers] = useState<Dict | null>(null);
  const [priorities, setPriorities] = useState<Dict | null>(null);
  const [animOpt, setAnimOpt] = useState<Dict | null>(null);
  const [liveOrg, setLiveOrg] = useState<Dict | null>(null);
  const [city, setCity] = useState<Dict | null>(null);
  const [perf, setPerf] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: RENDER_STEPS[step],
      detailedExplanation:
        "Движок визуализации displays objects efficiently with LOD and viewport culling. Independent from business logic — updates from Event Bus and Behavior Engine.",
      example: `Example: complete «${RENDER_STEPS[step]}».`,
      popup: { title: RENDER_STEPS[step], body: "GPU-friendly visual rendering." },
      tooltip: RENDER_STEPS[step],
      purpose: "Efficient visual display",
      benefits: "High FPS with smart culling and layers",
      typicalUse: "Team Map and AI City viewports",
      businessValue: "Scalable visualization without business coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/rendering/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать сессию");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function go(next: number) {
    setError(null);
    setBusy(true);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/rendering/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1, draft: { zoom } }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка навигации");
    } finally {
      setBusy(false);
    }
  }

  async function load(path: string, setter: (v: Dict) => void, qs = "") {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/rendering/${path}${qs}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/rendering/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10, draft: { zoom } }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/rendering/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка создания");
      setCreated(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Движок визуализации"
      subtitle="LOD · Smart Viewport · Layers — GPU-friendly, independent from business logic."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">GPU Friendly</Badge>
        <Badge>LOD L0–L4</Badge>
        <Badge>Sprint 29.4</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="eds-type-small">Zoom</span>
        <Input
          type="number"
          step="0.05"
          min="0"
          max="2"
          value={String(zoom)}
          onChange={(e) => setZoom(Number(e.target.value) || 0)}
        />
      </div>

      <ProgressIndicator current={step} total={RENDER_STEPS.length} />
      <BuilderStepNav steps={[...RENDER_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Visual Renderer">
              <Button disabled={busy} onClick={() => void load(`renderer?zoom=${zoom}`, setRenderer)}>
                Build render queue
              </Button>
              {renderer ? (
                <div className="mt-3 eds-type-small space-y-2">
                  <div>Pool size: {String((renderer.object_pool as Dict)?.size)}</div>
                  <div>Queue: {((renderer.render_queue as unknown[]) || []).length} items</div>
                  <div>{((renderer.capabilities as string[]) || []).join(" · ")}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Visual LOD Engine">
              <Button disabled={busy} onClick={() => void load(`lod?zoom=${zoom}`, setLod)}>
                Resolve LOD
              </Button>
              {lod ? (
                <div className="mt-3 eds-type-small space-y-2">
                  <div>
                    Level {String((lod.lod as Dict)?.id)} — {String((lod.lod as Dict)?.label)}
                  </div>
                  <div>
                    Objects {String(lod.output_count)} / {String(lod.input_count)}
                  </div>
                  <div>Types: {((lod.allowed_types as string[]) || []).join(", ")}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Smart Viewport">
              <Button
                disabled={busy}
                onClick={() =>
                  void load(`viewport?zoom=${zoom}&x=0&y=0&width=800&height=600`, setViewport)
                }
              >
                Cull viewport
              </Button>
              {viewport ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Visible: {String(viewport.visible_count)}</div>
                  <div>Culled: {String(viewport.culled_count)}</div>
                  <div>
                    Detection {String(viewport.viewport_detection)} · Culling{" "}
                    {String(viewport.object_culling)} · Lazy {String(viewport.lazy_rendering)}
                  </div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Layer System">
              <Button disabled={busy} onClick={() => void load(`layers?zoom=${zoom}`, setLayers)}>
                Build layers
              </Button>
              {layers ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {Object.entries((layers.counts as Dict) || {}).map(([k, v]) => (
                    <li key={k}>
                      {k}: {String(v)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Object Priority">
              <Button disabled={busy} onClick={() => void load("priorities", setPriorities)}>
                Load priorities
              </Button>
              {priorities ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(priorities.counts, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Animation Optimization">
              <Button
                disabled={busy}
                onClick={() => void load("animation-optimization", setAnimOpt)}
              >
                Load animation profile
              </Button>
              {animOpt ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Quality: {String(animOpt.adaptive_quality)}</div>
                  <div>Active: {String(animOpt.active_animations)}</div>
                  <div>FPS limit: {String(animOpt.frame_limit_fps)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Live Организация Support">
              <Button disabled={busy} onClick={() => void load("live-organization", setLiveOrg)}>
                Load live surfaces
              </Button>
              {liveOrg ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((liveOrg.surface_names as string[]) || []).map((s) => (
                    <li key={s}>
                      {s}: {(((liveOrg.surfaces as Dict)?.[s] as unknown[]) || []).length}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Foundation for AI City">
              <Button disabled={busy} onClick={() => void load("ai-city", setCity)}>
                Load render interfaces
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

          {step === 8 ? (
            <Card title="Performance">
              <Button disabled={busy} onClick={() => void load("performance", setPerf)}>
                Monitor
              </Button>
              {perf ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(perf.metrics, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Создать — зарегистрировать Render Stack">
              <p className="eds-type-small mb-3">
                Registers Rendering Engine, LOD Engine, Viewport Engine, and Layer System.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(created.registrations || {
                    rendering_engine_id: (created.rendering_engine as Dict)?.rendering_engine_id,
                    lod_engine_id: (created.lod_engine as Dict)?.lod_engine_id,
                    viewport_engine_id: (created.viewport_engine as Dict)?.viewport_engine_id,
                    layer_system_id: (created.layer_system as Dict)?.layer_system_id,
                  }, null, 2)}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Назад
            </Button>
            <Button
              disabled={busy || step >= RENDER_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Далее
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>
    </PlatformBuilderLayout>
  );
}
