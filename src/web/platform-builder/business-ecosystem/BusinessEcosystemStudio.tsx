import { useMemo, useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { BUSINESS_ECOSYSTEM_STEPS } from "./catalog";

type Dict = Record<string, unknown>;

export function BusinessEcosystemStudio() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [framework, setFramework] = useState<Dict | null>(null);
  const [modules, setModules] = useState<Dict | null>(null);
  const [extensions, setExtensions] = useState<Dict | null>(null);
  const [registry, setRegistry] = useState<Dict | null>(null);
  const [automotive, setAutomotive] = useState<Dict | null>(null);
  const [agriculture, setAgriculture] = useState<Dict | null>(null);
  const [beautyCafe, setBeautyCafe] = useState<Dict | null>(null);
  const [cryptoLegalDrone, setCryptoLegalDrone] = useState<Dict | null>(null);
  const [compatibility, setCompatibility] = useState<Dict | null>(null);
  const [ui, setUi] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: BUSINESS_ECOSYSTEM_STEPS[step],
      detailedExplanation:
        "Фундамент бизнес-экосистем reorganizes the platform into reusable architecture. Ecosystems extend the shared core — nothing is copied, existing APIs and modules stay intact.",
      example: `Example: complete «${BUSINESS_ECOSYSTEM_STEPS[step]}».`,
      popup: { title: BUSINESS_ECOSYSTEM_STEPS[step], body: "Extend platform core, never fork it." },
      tooltip: BUSINESS_ECOSYSTEM_STEPS[step],
      purpose: "Reusable industry extension architecture",
      benefits: "Universal modules + capability catalogs for future ecosystems",
      typicalUse: "Prepare Automotive and other industry ecosystems",
      businessValue: "One platform core, many configurable businesses",
    }),
    [step],
  );

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/business-ecosystem/sessions`, {
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
      await fetch(`${PLATFORM_BUILDER_API}/business-ecosystem/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: next + 1 }),
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
      const res = await fetch(`${PLATFORM_BUILDER_API}/business-ecosystem/${path}`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка загрузки");
      setter(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    } finally {
      setBusy(false);
    }
  }

  async function scanCompatibility() {
    setBusy(true);
    setError(null);
    try {
      await ensureSession();
      const res = await fetch(`${PLATFORM_BUILDER_API}/business-ecosystem/compatibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "scan" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Scan failed");
      setCompatibility(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      await fetch(`${PLATFORM_BUILDER_API}/business-ecosystem/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 10 }),
      });
      const res = await fetch(`${PLATFORM_BUILDER_API}/business-ecosystem/sessions/${sid}/create`, {
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
      title="Фундамент бизнес-экосистем"
      subtitle="Reusable industry architecture — ecosystems extend the platform core, never copy it."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Extend-Only</Badge>
        <Badge>Universal Modules</Badge>
        <Badge>APIs Intact</Badge>
        <Badge>Sprint 30.2</Badge>
        {sessionId ? <Badge>session {sessionId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={BUSINESS_ECOSYSTEM_STEPS.length} />
      <BuilderStepNav
        steps={[...BUSINESS_ECOSYSTEM_STEPS]}
        current={step}
        onChange={(i) => void go(i)}
      />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="Business Ecosystem Framework">
              <Button disabled={busy} onClick={() => void load("framework", setFramework)}>
                Load framework
              </Button>
              {framework ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((framework.components as string[]) || []).map((c) => (
                    <li key={c}>{c}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Universal Модули">
              <Button disabled={busy} onClick={() => void load("modules", setModules)}>
                Load universal modules
              </Button>
              {modules ? (
                <p className="mt-3 eds-type-small">Modules: {String(modules.count)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Extension Model">
              <Button disabled={busy} onClick={() => void load("extensions", setExtensions)}>
                Load extension points
              </Button>
              {extensions ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((extensions.extension_points as string[]) || []).map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Business Ecosystem Registry">
              <Button disabled={busy} onClick={() => void load("registry", setRegistry)}>
                Load ecosystem registry
              </Button>
              {registry ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  {((registry.ecosystems as string[]) || []).map((e) => (
                    <li key={e}>{e}</li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Automotive Capabilities">
              <Button disabled={busy} onClick={() => void load("automotive", setAutomotive)}>
                Load automotive capabilities
              </Button>
              {automotive ? (
                <p className="mt-3 eds-type-small">Capabilities: {String(automotive.count)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Agriculture Capabilities">
              <Button disabled={busy} onClick={() => void load("agriculture", setAgriculture)}>
                Load agriculture capabilities
              </Button>
              {agriculture ? (
                <p className="mt-3 eds-type-small">Capabilities: {String(agriculture.count)}</p>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Beauty & Cafe Capabilities">
              <Button disabled={busy} onClick={() => void load("beauty-cafe", setBeautyCafe)}>
                Load beauty & cafe
              </Button>
              {beautyCafe ? (
                <p className="mt-3 eds-type-small">
                  Beauty: {String(((beautyCafe.beauty as Dict)?.count as number) || 0)} · Cafe:{" "}
                  {String(((beautyCafe.cafe as Dict)?.count as number) || 0)}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Crypto · Legal · Drone">
              <Button
                disabled={busy}
                onClick={() => void load("crypto-legal-drone", setCryptoLegalDrone)}
              >
                Load crypto, legal, drone
              </Button>
              {cryptoLegalDrone ? (
                <p className="mt-3 eds-type-small">
                  Crypto: {String(((cryptoLegalDrone.crypto as Dict)?.count as number) || 0)} ·
                  Legal: {String(((cryptoLegalDrone.legal as Dict)?.count as number) || 0)} · Drone:{" "}
                  {String(((cryptoLegalDrone.drone as Dict)?.count as number) || 0)}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Architecture Compatibility">
              <div className="flex flex-wrap gap-2">
                <Button disabled={busy} onClick={() => void load("compatibility", setCompatibility)}>
                  Load compatibility
                </Button>
                <Button disabled={busy} onClick={() => void scanCompatibility()}>
                  Scan compatibility
                </Button>
                <Button disabled={busy} onClick={() => void load("ui", setUi)}>
                  Load foundation UI
                </Button>
              </div>
              {compatibility ? (
                <p className="mt-3 eds-type-small">
                  Prepared for: {String(compatibility.prepared_for)}
                </p>
              ) : null}
              {ui ? (
                <p className="mt-3 eds-type-small">
                  Surfaces: {((ui.surfaces as string[]) || []).join(" · ")}
                </p>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Создать">
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register Фундамент бизнес-экосистем
              </Button>
              {created ? (
                <ul className="mt-3 eds-type-small space-y-1">
                  <li>
                    business_ecosystem_framework_id:{" "}
                    {
                      (created.business_ecosystem_framework as Dict)
                        ?.business_ecosystem_framework_id as string
                    }
                  </li>
                  <li>
                    business_template_registry_id:{" "}
                    {
                      (created.business_template_registry as Dict)
                        ?.business_template_registry_id as string
                    }
                  </li>
                  <li>
                    reusable_module_registry_id:{" "}
                    {
                      (created.reusable_module_registry as Dict)
                        ?.reusable_module_registry_id as string
                    }
                  </li>
                  <li>
                    industry_extension_engine_id:{" "}
                    {
                      (created.industry_extension_engine as Dict)
                        ?.industry_extension_engine_id as string
                    }
                  </li>
                  <li>
                    industry_capability_registry_id:{" "}
                    {
                      (created.industry_capability_registry as Dict)
                        ?.industry_capability_registry_id as string
                    }
                  </li>
                  <li>{String(created.message)}</li>
                </ul>
              ) : null}
            </Card>
          ) : null}
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>
    </PlatformBuilderLayout>
  );
}
