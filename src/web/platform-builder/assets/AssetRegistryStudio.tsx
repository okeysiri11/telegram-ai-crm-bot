import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { ASSET_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function AssetRegistryStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState("asset_ai_avatar_base");
  const [registry, setRegistry] = useState<Dict | null>(null);
  const [categories, setCategories] = useState<Dict | null>(null);
  const [versions, setVersions] = useState<Dict | null>(null);
  const [opt, setOpt] = useState<Dict | null>(null);
  const [avatars, setAvatars] = useState<Dict | null>(null);
  const [branding, setBranding] = useState<Dict | null>(null);
  const [city, setCity] = useState<Dict | null>(null);
  const [search, setSearch] = useState<Dict | null>(null);
  const [perf, setPerf] = useState<Dict | null>(null);
  const [browser, setBrowser] = useState<Dict | null>(null);
  const [preview, setPreview] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: ASSET_STEPS[step],
      detailedExplanation:
        "Реестр визуальных активов stores, versions, and optimizes platform visuals. Completely separated from business logic.",
      example: `Example: complete «${ASSET_STEPS[step]}».`,
      popup: { title: ASSET_STEPS[step], body: "Enterprise visual asset management." },
      tooltip: ASSET_STEPS[step],
      purpose: "Central visual resource registry",
      benefits: "Версияed, searchable, optimized assets",
      typicalUse: "Browse, preview, replace, and rollback assets",
      businessValue: "Visual assets without logic coupling",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/assets/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/assets/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          step: next + 1,
          draft: { selected_asset_id: selectedId },
        }),
      });
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка навигации");
    } finally {
      setBusy(false);
    }
  }

  async function load(path: string, setter: (v: Dict) => void) {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/assets/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function runReplace() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/assets/replace`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_id: selectedId,
          uri: `/assets/replaced/${selectedId}.svg`,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Replace failed");
      setVersions(body);
      await load(`versions?asset_id=${selectedId}`, setVersions);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Replace failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/assets/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10, draft: { selected_asset_id: selectedId } }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/assets/sessions/${sid}/create`, {
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
      title="Реестр визуальных активов"
      subtitle="Browse · Версия · Optimize — visual assets separated from business logic."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Separated from Logic</Badge>
        <Badge>Asset Browser</Badge>
        <Badge>Sprint 29.6</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="eds-type-small">Asset ID</span>
        <Input value={selectedId} onChange={(e) => setSelectedId(e.target.value)} />
        <span className="eds-type-small">Search</span>
        <Input value={query} onChange={(e) => setQuery(e.target.value)} />
      </div>

      <ProgressIndicator current={step} total={ASSET_STEPS.length} />
      <BuilderStepNav steps={[...ASSET_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Реестр визуальных активов">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("registry", setRegistry)}>
                  Load registry
                </Button>
                <Button disabled={busy} onClick={() => void load("browser", setBrowser)}>
                  Open browser
                </Button>
              </div>
              {registry ? (
                <div className="mt-3 eds-type-small">
                  Ресурсы: {String(registry.count)} · Types:{" "}
                  {((registry.supported_types as string[]) || []).join(", ")}
                </div>
              ) : null}
              {browser ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {(((browser.assets as Dict[]) || []) as Dict[]).slice(0, 6).map((a) => (
                    <li key={String(a.asset_id)}>
                      {String(a.name)} — {String(a.category)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Asset Categories">
              <Button disabled={busy} onClick={() => void load("categories", setCategories)}>
                Explore categories
              </Button>
              {categories ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {Object.entries((categories.counts as Dict) || {}).map(([k, v]) => (
                    <li key={k}>
                      {k}: {String(v)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Версия Management">
              <div className="flex flex-wrap gap-2">
                <Button
                  disabled={busy}
                  onClick={() => void load(`versions?asset_id=${selectedId}`, setVersions)}
                >
                  Version history
                </Button>
                <Button disabled={busy} onClick={() => void runReplace()}>
                  Replace asset
                </Button>
              </div>
              {versions ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    (versions.history as Dict)?.revisions || versions.asset || versions,
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Resource Optimization">
              <Button disabled={busy} onClick={() => void load("optimization", setOpt)}>
                Optimize
              </Button>
              {opt ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Pool: {String(opt.resource_pool_size)}</div>
                  <div>Cache: {String(opt.cache_entries)}</div>
                  <div>Duplicates: {String(opt.duplicate_groups)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="AI Avatar Library">
              <Button disabled={busy} onClick={() => void load("avatars", setAvatars)}>
                Load library
              </Button>
              {avatars ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((avatars.sections as string[]) || []).map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Организация Branding">
              <Button disabled={busy} onClick={() => void load("branding", setBranding)}>
                Load brand assets
              </Button>
              {branding ? (
                <div className="mt-3 eds-type-small">
                  Stored: {((branding.stored as string[]) || []).join(" · ")}
                  <div>Count: {String(branding.count)}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Foundation for AI City">
              <Button disabled={busy} onClick={() => void load("ai-city", setCity)}>
                Load city asset interfaces
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

          {step === 7 ? (
            <Card title="Поиск & Filters">
              <Button
                disabled={busy}
                onClick={() =>
                  void load(
                    `search?q=${encodeURIComponent(query)}&organization_id=org_default`,
                    setSearch,
                  )
                }
              >
                Search
              </Button>
              {search ? (
                <div className="mt-3 eds-type-small space-y-1">
                  <div>Results: {String(search.count)}</div>
                  <div>Facets: {((search.facets as string[]) || []).join(", ")}</div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Performance">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("performance", setPerf)}>
                  Monitor
                </Button>
                <Button
                  disabled={busy}
                  onClick={() => void load(`preview/${selectedId}`, setPreview)}
                >
                  Предпросмотр panel
                </Button>
              </div>
              {perf ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(perf.metrics, null, 2)}
                </pre>
              ) : null}
              {preview ? (
                <div className="mt-3 eds-type-small">
                  Предпросмотр: {String(preview.preview_uri)}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Создать — зарегистрировать Asset Stack">
              <p className="eds-type-small mb-3">
                Registers Asset Registry, Version Registry, and Optimization Engine.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    created.registrations || {
                      asset_registry_id: (created.asset_registry as Dict)?.asset_registry_id,
                      version_registry_id: (created.version_registry as Dict)?.version_registry_id,
                      optimization_engine_id: (created.optimization_engine as Dict)
                        ?.optimization_engine_id,
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
              Назад
            </Button>
            <Button
              disabled={busy || step >= ASSET_STEPS.length - 1}
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
