/**
 * Sprint 42.1 — Client onboarding wizard (6 steps).
 */

import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card, Input, Select } from "@/ui";
import { FullLayout } from "@/layouts/FullLayout";
import {
  CLIENT_ONBOARDING_STEPS,
  loadClientOnboarding,
  saveClientOnboarding,
  markClientOnboardingComplete,
  type ClientOnboardingStep,
} from "./clientOnboardingStore";
import { seedClientDemoData } from "./clientDemoSeed";
import { demoUserByEmail } from "./demoUsers";
import { useAuthStore } from "@/auth/authStore";
import { useI18n } from "@/i18n";

const BUSINESS_TYPES = [
  { id: "travel", label: "Туризм / агентство" },
  { id: "crypto", label: "Crypto OTC" },
  { id: "construction", label: "Строительство" },
  { id: "drone", label: "БПЛА / Drone" },
  { id: "auto", label: "Автодилер" },
  { id: "legal", label: "Юридические услуги" },
  { id: "agro", label: "Агро" },
  { id: "marketplace", label: "Marketplace" },
  { id: "other", label: "Другое" },
];

const MODULE_OPTIONS = [
  { id: "crm", label: "CRM" },
  { id: "documents", label: "Документы" },
  { id: "analytics", label: "Аналитика" },
  { id: "tasks", label: "Задачи" },
  { id: "knowledge", label: "Знания" },
  { id: "support", label: "Поддержка" },
];

export function ClientOnboardingPage() {
  const t = useI18n((s) => s.t);
  const navigate = useNavigate();
  const email = useAuthStore((s) => s.user?.email);
  const [state, setState] = useState(() => loadClientOnboarding());

  const stepIndex = CLIENT_ONBOARDING_STEPS.indexOf(state.step);
  const progress = useMemo(
    () => Math.round(((stepIndex + 1) / CLIENT_ONBOARDING_STEPS.length) * 100),
    [stepIndex],
  );

  function go(step: ClientOnboardingStep, patch: Partial<typeof state> = {}) {
    const next = saveClientOnboarding({ ...patch, step });
    setState(next);
  }

  function toggleModule(id: string) {
    const modules = state.modules.includes(id)
      ? state.modules.filter((m) => m !== id)
      : [...state.modules, id];
    setState(saveClientOnboarding({ modules }));
  }

  function finish() {
    if (state.importChoice === "demo") {
      const demo = email ? demoUserByEmail(email) : demoUserByEmail("travel@globefly.demo");
      if (demo) seedClientDemoData(demo);
    }
    markClientOnboardingComplete({
      companyName: state.companyName,
      businessType: state.businessType,
      modules: state.modules,
      importChoice: state.importChoice,
    });
    navigate("/dashboard", { replace: true });
  }

  return (
    <FullLayout>
      <div className="mx-auto max-w-2xl space-y-4" data-testid="client-onboarding">
        <Card title={t("onboard.clientTitle")}>
          <p className="eds-type-helper mb-2">
            {t("onboard.step")} {stepIndex + 1} / {CLIENT_ONBOARDING_STEPS.length} · {progress}%
          </p>
          <div className="h-2 w-full rounded bg-[var(--ew-border)]">
            <div
              className="h-2 rounded bg-[var(--eds-success)] transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </Card>

        {state.step === "welcome" ? (
          <Card title={t("onboard.welcome")}>
            <p className="eds-type-body">{t("onboard.welcomeBody")}</p>
            <div className="mt-4">
              <Button className="ews-primary-cta" onClick={() => go("company")}>
                {t("onboard.continue")}
              </Button>
            </div>
          </Card>
        ) : null}

        {state.step === "company" ? (
          <Card title={t("onboard.company")}>
            <label className="eds-type-label mb-1 block">{t("onboard.companyName")}</label>
            <Input
              value={state.companyName}
              onChange={(e) => setState(saveClientOnboarding({ companyName: e.target.value }))}
              placeholder="GlobeFly Travel"
            />
            <div className="mt-4 flex gap-2">
              <Button variant="secondary" onClick={() => go("welcome")}>
                {t("onboard.back")}
              </Button>
              <Button
                className="ews-primary-cta"
                disabled={state.companyName.trim().length < 2}
                onClick={() => go("business")}
              >
                {t("onboard.continue")}
              </Button>
            </div>
          </Card>
        ) : null}

        {state.step === "business" ? (
          <Card title={t("onboard.business")}>
            <Select
              value={state.businessType}
              onChange={(e) => setState(saveClientOnboarding({ businessType: e.target.value }))}
            >
              <option value="">{t("onboard.chooseBusiness")}</option>
              {BUSINESS_TYPES.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label}
                </option>
              ))}
            </Select>
            <div className="mt-4 flex gap-2">
              <Button variant="secondary" onClick={() => go("company")}>
                {t("onboard.back")}
              </Button>
              <Button
                className="ews-primary-cta"
                disabled={!state.businessType}
                onClick={() => go("modules")}
              >
                {t("onboard.continue")}
              </Button>
            </div>
          </Card>
        ) : null}

        {state.step === "modules" ? (
          <Card title={t("onboard.modules")}>
            <div className="flex flex-wrap gap-2">
              {MODULE_OPTIONS.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  className={`ews-workspace-dock-chip ${state.modules.includes(m.id) ? "is-active" : ""}`}
                  onClick={() => toggleModule(m.id)}
                >
                  {m.label}
                </button>
              ))}
            </div>
            <div className="mt-4 flex gap-2">
              <Button variant="secondary" onClick={() => go("business")}>
                {t("onboard.back")}
              </Button>
              <Button
                className="ews-primary-cta"
                disabled={!state.modules.length}
                onClick={() => go("import")}
              >
                {t("onboard.continue")}
              </Button>
            </div>
          </Card>
        ) : null}

        {state.step === "import" ? (
          <Card title={t("onboard.import")}>
            <div className="space-y-2">
              {(
                [
                  ["demo", t("onboard.importDemo")],
                  ["skip", t("onboard.importSkip")],
                  ["file", t("onboard.importFile")],
                ] as const
              ).map(([id, label]) => (
                <label key={id} className="flex items-center gap-2 eds-type-body">
                  <input
                    type="radio"
                    name="import"
                    checked={state.importChoice === id}
                    onChange={() => setState(saveClientOnboarding({ importChoice: id }))}
                  />
                  {label}
                </label>
              ))}
            </div>
            <div className="mt-4 flex gap-2">
              <Button variant="secondary" onClick={() => go("modules")}>
                {t("onboard.back")}
              </Button>
              <Button className="ews-primary-cta" onClick={() => go("finish")}>
                {t("onboard.continue")}
              </Button>
            </div>
          </Card>
        ) : null}

        {state.step === "finish" ? (
          <Card title={t("onboard.finish")}>
            <p className="eds-type-body">{t("onboard.finishBody")}</p>
            <ul className="mt-2 list-disc pl-5 eds-type-helper">
              <li>{state.companyName}</li>
              <li>{state.businessType}</li>
              <li>{state.modules.join(", ")}</li>
            </ul>
            <div className="mt-4 flex gap-2">
              <Button variant="secondary" onClick={() => go("import")}>
                {t("onboard.back")}
              </Button>
              <Button className="ews-primary-cta" onClick={finish} data-testid="onboard-finish">
                {t("onboard.openWorkspace")}
              </Button>
            </div>
          </Card>
        ) : null}
      </div>
    </FullLayout>
  );
}
