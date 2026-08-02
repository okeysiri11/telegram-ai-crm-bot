/**
 * First User Experience — Sprint 32.3.1.
 * Welcome → Role → Workspace → Ready → Dashboard (AI defaults applied silently).
 * Reuses Workspace Engine (store + tenancy), AI Team / Concierge routes, Dashboard.
 */

import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Badge, Button, Card, Input, Select } from "@/ui";
import { ProgressIndicator } from "../../platform-builder/framework/ProgressIndicator";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { useThemeStore } from "@/theme/themeStore";
import { hubIntegrations } from "@/integrations/hub";
import { apiFetch } from "@/integrations/apiClient";
import { telemetry } from "@/integrations/telemetry";
import { AVATARS, COMMUNICATION_STYLES, VOICE_PROFILES } from "../../platform-builder/concierge/catalog";
import {
  FIRST_ENTRY_STEPS,
  INDUSTRY_OPTIONS,
  TEAM_SIZE_OPTIONS,
  firstEntryRoleCatalog,
  type FirstEntryStepId,
} from "./firstEntryRoles";
import {
  isFirstEntryComplete,
  loadFirstEntry,
  markFirstEntryComplete,
  saveFirstEntry,
  type FirstEntryState,
} from "./firstEntryStore";
import { postAuthDestination } from "@/navigation/roleHome";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useI18n, type Locale } from "@/i18n";

const STEP_INDEX: Record<FirstEntryStepId, number> = {
  welcome: 0,
  role: 1,
  workspace: 2,
  ready: 3,
  ai_team: 4,
  concierge: 5,
  dashboard: 6,
};

// Sprint 34.2 — shorten mandatory onboarding UX:
// welcome → role → workspace → ready → dashboard.
// AI Team & AI Concierge stay optional (defaults applied) to reduce cognitive load.
const MANDATORY_TOTAL = 4;
const MANDATORY_STEP_INDEX: Record<FirstEntryStepId, number> = {
  welcome: 0,
  role: 1,
  workspace: 2,
  ready: 3,
  ai_team: 3,
  concierge: 3,
  dashboard: 3,
};

export function FirstEntryPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const updatePrefs = usePreferencesStore((s) => s.update);
  const setMode = useThemeStore((s) => s.setMode);
  const setLocale = useI18n((s) => s.setLocale);

  const [state, setState] = useState<FirstEntryState>(() => loadFirstEntry());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [animKey, setAnimKey] = useState(0);

  const stepIdx = MANDATORY_STEP_INDEX[state.step] ?? 0;
  const roles = useMemo(() => {
    const enterprise = firstEntryRoleCatalog.enterpriseList();
    const rest = firstEntryRoleCatalog
      .list()
      .filter((r) => !enterprise.some((e) => e.id === r.id));
    return [...enterprise, ...rest];
  }, []);
  const selectedRole = firstEntryRoleCatalog.get(state.roleId);

  useEffect(() => {
    if (isFirstEntryComplete()) {
      navigate(postAuthDestination(useRoleSwitcher.getState().activeRoleId), { replace: true });
    }
  }, [navigate]);

  function go(step: FirstEntryStepId, patch: Partial<FirstEntryState> = {}) {
    const next = saveFirstEntry({ ...patch, step });
    setState(next);
    setAnimKey((k) => k + 1);
    setError(null);
    void telemetry.userActivity(`first_entry_${step}`);
  }

  async function createWorkspace() {
    if (!state.companyName.trim()) {
      setError("Укажите название компании");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const tenantId = user?.tenantId || "demo-corp";
      let workspaceId = `ws_${Date.now().toString(36)}`;

      // Prefer existing Tenancy Workspace Engine
      const res = await apiFetch(`${hubIntegrations.tenancy}/workspaces`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: tenantId,
          name: state.companyName.trim(),
          kind: selectedRole?.ecosystemHint || "general",
          settings: {
            country: state.country,
            timezone: state.timezone,
            language: state.language,
            currency: state.currency,
            industry: state.industry,
            team_size: state.teamSize,
            role_id: state.roleId,
          },
        }),
      });
      if (res.ok) {
        const body = (await res.json()) as Record<string, unknown>;
        workspaceId = String(body.workspace_id || body.id || workspaceId);
      }

      // Optional EWS bootstrap — ignore failure (engine may already be ready)
      await apiFetch(`${hubIntegrations.workspacePlatform}/bootstrap`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workspace_id: workspaceId, name: state.companyName.trim() }),
      }).catch(() => null);

      setWorkspace({
        company: state.companyName.trim(),
        project: workspaceId,
        department: selectedRole?.ecosystemHint || "operations",
        userContext: user?.name || user?.email || "user",
        permissions: user?.permissions?.length ? user.permissions : ["read", "write", "admin"],
        activeModules: selectedRole?.ecosystemHint
          ? ["hub", "workflow", "ai", selectedRole.ecosystemHint]
          : ["hub", "workflow", "ai", "knowledge"],
      });
      updatePrefs({ language: state.language as "en" | "ru" | "uk" });
      setLocale((state.language as Locale) || "ru");

      go("ready", { workspaceId });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать workspace");
    } finally {
      setBusy(false);
    }
  }

  async function finish() {
    setBusy(true);
    try {
      // Echo to existing EPR first-launch (non-blocking for UX)
      await apiFetch(`${hubIntegrations.pilotReadiness}/first-launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          organization: state.companyName,
          industry: state.industry,
          role_id: state.roleId,
          workspace_id: state.workspaceId,
          ai_team_mode: state.aiTeamMode,
          concierge: {
            name: state.conciergeName,
            avatar: state.conciergeAvatar,
            voice: state.conciergeVoice,
            style: state.conciergeStyle,
            language: state.conciergeLanguage,
          },
        }),
      }).catch(() => null);

      markFirstEntryComplete();
      await telemetry.audit("first_entry_complete", state.roleId || "user");
      const role = state.roleId;
      if (role === "client") useRoleSwitcher.getState().setRole("client");
      else if (role === "business_owner" || role === "executive") useRoleSwitcher.getState().setRole("owner");
      else if (role === "administrator") useRoleSwitcher.getState().setRole("administrator");
      else if (role === "manager") useRoleSwitcher.getState().setRole("manager");
      else if (role === "employee") useRoleSwitcher.getState().setRole("employee");
      else if (role === "auto" || role === "auto_service" || role?.includes("dealer")) {
        useRoleSwitcher.getState().setRole("dealer");
      }
      const dest =
        selectedRole?.workspaceRoute ||
        postAuthDestination(useRoleSwitcher.getState().activeRoleId);
      navigate(dest, { replace: true });
    } finally {
      setBusy(false);
    }
  }

  function onLogo(file: File | null) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const logoDataUrl = String(reader.result || "");
      setState(saveFirstEntry({ logoDataUrl }));
    };
    reader.readAsDataURL(file);
  }

  return (
    <div className="first-entry-shell min-h-screen">
      <div className="first-entry-glow" aria-hidden />
      <div className="relative z-10 mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-8 lg:px-10 lg:py-12">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="eds-type-caption tracking-[0.2em] text-[var(--eds-text-muted)] uppercase">
              Enterprise Platform
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-[var(--eds-text)] lg:text-3xl">
              Первый вход
            </h1>
          </div>
          <div className="w-full max-w-sm lg:w-72">
            <ProgressIndicator current={stepIdx} total={MANDATORY_TOTAL} />
            <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
              Оценка времени: ≈ 3 мин
            </p>
          </div>
        </header>

        <main
          key={animKey}
          className="first-entry-panel eds-anim-page flex flex-1 flex-col justify-center"
        >
          {error ? (
            <p className="mb-4 eds-type-small text-[var(--eds-danger)]" role="alert">
              {error}
            </p>
          ) : null}

          {state.step === "welcome" ? (
            <section className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
              <div>
                <Badge tone="success">Welcome</Badge>
                <h2 className="mt-4 text-4xl leading-tight font-semibold tracking-tight text-[var(--eds-text)] lg:text-5xl">
                  Добро пожаловать
                  {user?.name ? `, ${user.name}` : ""}
                </h2>
                <p className="mt-4 max-w-xl text-lg text-[var(--eds-text-muted)]">
                  Четыре коротких шага: роль, компания, готовность — и вы на Dashboard с Morning Brief.
                  AI Team и Concierge уже настроены по умолчанию.
                </p>
                <div className="mt-8 flex flex-wrap gap-3">
                  <Button size="lg" onClick={() => go("role")}>
                    Continue
                  </Button>
                  <Button
                    size="lg"
                    variant="secondary"
                    onClick={() => {
                      markFirstEntryComplete();
                      navigate(postAuthDestination(useRoleSwitcher.getState().activeRoleId), {
                        replace: true,
                      });
                    }}
                  >
                    Пропустить
                  </Button>
                </div>
              </div>
              <Card title="В этот onboarding входит">
                <ol className="eds-type-body space-y-3 text-[var(--eds-text-muted)]">
                  <li className="flex gap-3">
                    <span className="first-entry-step-num">1</span>
                    <span>Роль</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="first-entry-step-num">2</span>
                    <span>Компания</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="first-entry-step-num">3</span>
                    <span>Готово</span>
                  </li>
                  <li className="flex gap-3">
                    <span className="first-entry-step-num">4</span>
                    <span>Dashboard · Morning Brief</span>
                  </li>
                </ol>
                <p className="mt-3 eds-type-small text-[var(--eds-text-muted)]">
                  AI Team и Concierge уже работают по умолчанию — тонкая настройка доступна позже.
                </p>
              </Card>
            </section>
          ) : null}

          {state.step === "role" ? (
            <section>
              <h2 className="text-3xl font-semibold tracking-tight">Кто вы?</h2>
              <p className="mt-2 text-[var(--eds-text-muted)]">
                Who are you? Выберите роль. Каталог расширяемый — новые роли добавляются без смены архитектуры.
              </p>
              <div className="mt-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                {roles.map((role) => {
                  const active = state.roleId === role.id;
                  return (
                    <button
                      key={role.id}
                      type="button"
                      className={`first-entry-role ${active ? "is-active" : ""}`}
                      onClick={() => {
                        const industry =
                          role.ecosystemHint && role.ecosystemHint !== "platform"
                            ? role.ecosystemHint === "auto"
                              ? "automotive"
                              : role.ecosystemHint
                            : state.industry;
                        setState(saveFirstEntry({ roleId: role.id, industry }));
                      }}
                    >
                      <span className="first-entry-role-icon">{role.icon}</span>
                      <span className="block text-left">
                        <span className="block font-medium text-[var(--eds-text)]">{role.label}</span>
                        <span className="mt-1 block eds-type-small text-[var(--eds-text-muted)]">
                          {role.description}
                        </span>
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="mt-8 flex gap-3">
                <Button variant="secondary" onClick={() => go("welcome")}>
                  Назад
                </Button>
                <Button disabled={!state.roleId} onClick={() => go("workspace")}>
                  Continue
                </Button>
              </div>
            </section>
          ) : null}

          {state.step === "workspace" ? (
            <section className="grid gap-8 lg:grid-cols-2">
              <div>
                <h2 className="text-3xl font-semibold tracking-tight">Создание Workspace</h2>
                <p className="mt-2 text-[var(--eds-text-muted)]">
                  Используем существующий Workspace Engine (Tenancy + EWS). Новый engine не создаётся.
                </p>
                <div className="mt-6 grid gap-3">
                  <Input
                    value={state.companyName}
                    onChange={(e) => setState(saveFirstEntry({ companyName: e.target.value }))}
                    placeholder="Название компании"
                    aria-label="Название компании"
                  />
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input
                      value={state.country}
                      onChange={(e) => setState(saveFirstEntry({ country: e.target.value }))}
                      placeholder="Страна"
                      aria-label="Страна"
                    />
                    <Input
                      value={state.timezone}
                      onChange={(e) => setState(saveFirstEntry({ timezone: e.target.value }))}
                      placeholder="Часовой пояс"
                      aria-label="Часовой пояс"
                    />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Select
                      value={state.language}
                      onChange={(e) => setState(saveFirstEntry({ language: e.target.value }))}
                      aria-label="Язык"
                    >
                      <option value="ru">Русский</option>
                      <option value="en">English</option>
                      <option value="uk">Українська</option>
                    </Select>
                    <Select
                      value={state.currency}
                      onChange={(e) => setState(saveFirstEntry({ currency: e.target.value }))}
                      aria-label="Валюта"
                    >
                      <option value="UAH">UAH</option>
                      <option value="USD">USD</option>
                      <option value="EUR">EUR</option>
                    </Select>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Select
                      value={state.industry}
                      onChange={(e) => setState(saveFirstEntry({ industry: e.target.value }))}
                      aria-label="Отрасль"
                    >
                      {INDUSTRY_OPTIONS.map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.label}
                        </option>
                      ))}
                    </Select>
                    <Select
                      value={state.teamSize}
                      onChange={(e) => setState(saveFirstEntry({ teamSize: e.target.value }))}
                      aria-label="Размер команды"
                    >
                      {TEAM_SIZE_OPTIONS.map((o) => (
                        <option key={o.id} value={o.id}>
                          {o.label}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <label className="eds-type-small text-[var(--eds-text-muted)]">
                    Логотип (опционально)
                    <input
                      className="mt-2 block w-full eds-type-small"
                      type="file"
                      accept="image/*"
                      onChange={(e) => onLogo(e.target.files?.[0] || null)}
                    />
                  </label>
                </div>
                <div className="mt-8 flex gap-3">
                  <Button variant="secondary" onClick={() => go("role")}>
                    Назад
                  </Button>
                  <Button disabled={busy || !state.companyName.trim()} onClick={() => void createWorkspace()}>
                    {busy ? "Создаём…" : "Создать Workspace"}
                  </Button>
                </div>
              </div>
              <Card title="Превью">
                <div className="flex items-center gap-4">
                  <div className="first-entry-logo">
                    {state.logoDataUrl ? (
                      <img src={state.logoDataUrl} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <span>{(state.companyName || "CO").slice(0, 2).toUpperCase()}</span>
                    )}
                  </div>
                  <div>
                    <p className="font-medium">{state.companyName || "Ваша компания"}</p>
                    <p className="eds-type-small text-[var(--eds-text-muted)]">
                      {selectedRole?.label || "Роль"} · {state.industry} · {state.currency}
                    </p>
                  </div>
                </div>
              </Card>
            </section>
          ) : null}

          {state.step === "ready" ? (
            <section className="mx-auto max-w-2xl text-center">
              <Badge tone="success">Workspace Ready</Badge>
              <h2 className="mt-4 text-4xl font-semibold tracking-tight">Пространство готово</h2>
              <p className="mt-3 text-[var(--eds-text-muted)]">
                Персональное рабочее пространство создано через существующий Workspace Engine.
                {state.workspaceId ? (
                  <>
                    {" "}
                    ID: <code>{state.workspaceId}</code>
                  </>
                ) : null}
              </p>
              {selectedRole?.workspaceRoute ? (
                <p className="mt-2 eds-type-small">
                  Отраслевой вход:{" "}
                  <Link className="underline" to={selectedRole.workspaceRoute}>
                    {selectedRole.workspaceRoute}
                  </Link>
                </p>
              ) : null}
              <p className="mt-4 eds-type-small text-[var(--eds-text-muted)]">
                AI Team и AI Concierge можно настроить позже — в пару кликов из Dashboard и AI Concierge dock.
              </p>
              <div className="mt-8 flex justify-center gap-3">
                <Button variant="secondary" onClick={() => go("workspace")}>
                  Назад
                </Button>
                <Button
                  onClick={() => {
                    setMode(useThemeStore.getState().mode);
                    void finish();
                  }}
                >
                  Открыть Dashboard
                </Button>
              </div>
            </section>
          ) : null}

          {state.step === "ai_team" ? (
            <section>
              <h2 className="text-3xl font-semibold tracking-tight">AI Team</h2>
              <p className="mt-2 max-w-2xl text-[var(--eds-text-muted)]">
                Используйте готовую команду или настройте свою в существующем AI Team Center — без нового AI
                стека.
              </p>
              <div className="mt-8 grid gap-4 md:grid-cols-2">
                <button
                  type="button"
                  className={`first-entry-role ${state.aiTeamMode === "ready" ? "is-active" : ""}`}
                  onClick={() => setState(saveFirstEntry({ aiTeamMode: "ready" }))}
                >
                  <span className="block text-left">
                    <span className="block font-medium">Готовая команда</span>
                    <span className="mt-1 block eds-type-small text-[var(--eds-text-muted)]">
                      Быстрый старт с рекомендованными специалистами для вашей роли.
                    </span>
                  </span>
                </button>
                <button
                  type="button"
                  className={`first-entry-role ${state.aiTeamMode === "custom" ? "is-active" : ""}`}
                  onClick={() => setState(saveFirstEntry({ aiTeamMode: "custom" }))}
                >
                  <span className="block text-left">
                    <span className="block font-medium">Настроить самостоятельно</span>
                    <span className="mt-1 block eds-type-small text-[var(--eds-text-muted)]">
                      Откройте AI Team Center и AI Builder после входа.
                    </span>
                  </span>
                </button>
              </div>
              <div className="mt-6">
                <Link className="underline eds-type-small" to="/platform-builder/ai-team" target="_blank">
                  Открыть AI Team Center
                </Link>
              </div>
              <div className="mt-8 flex gap-3">
                <Button variant="secondary" onClick={() => go("ready")}>
                  Назад
                </Button>
                <Button disabled={!state.aiTeamMode} onClick={() => go("concierge")}>
                  Continue
                </Button>
              </div>
            </section>
          ) : null}

          {state.step === "concierge" ? (
            <section className="grid gap-8 lg:grid-cols-2">
              <div>
                <h2 className="text-3xl font-semibold tracking-tight">AI Concierge</h2>
                <p className="mt-2 text-[var(--eds-text-muted)]">
                  Настройки профиля Concierge. Полный wizard — в существующем Concierge Builder.
                </p>
                <div className="mt-6 grid gap-3">
                  <Input
                    value={state.conciergeName}
                    onChange={(e) => setState(saveFirstEntry({ conciergeName: e.target.value }))}
                    placeholder="Имя Concierge"
                    aria-label="Имя Concierge"
                  />
                  <Select
                    value={state.conciergeAvatar}
                    onChange={(e) => setState(saveFirstEntry({ conciergeAvatar: e.target.value }))}
                    aria-label="Аватар"
                  >
                    {AVATARS.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.emoji} {a.name}
                      </option>
                    ))}
                  </Select>
                  <Select
                    value={state.conciergeVoice}
                    onChange={(e) => setState(saveFirstEntry({ conciergeVoice: e.target.value }))}
                    aria-label="Голос"
                  >
                    {VOICE_PROFILES.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name}
                      </option>
                    ))}
                  </Select>
                  <Select
                    value={state.conciergeStyle}
                    onChange={(e) => setState(saveFirstEntry({ conciergeStyle: e.target.value }))}
                    aria-label="Стиль общения"
                  >
                    {COMMUNICATION_STYLES.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </Select>
                  <Select
                    value={state.conciergeLanguage}
                    onChange={(e) => setState(saveFirstEntry({ conciergeLanguage: e.target.value }))}
                    aria-label="Язык Concierge"
                  >
                    <option value="ru">Русский</option>
                    <option value="en">English</option>
                    <option value="uk">Українська</option>
                  </Select>
                </div>
                <p className="mt-4 eds-type-small">
                  <Link className="underline" to="/platform-builder/concierge" target="_blank">
                    Открыть Concierge Builder
                  </Link>
                </p>
                <div className="mt-8 flex gap-3">
                  <Button variant="secondary" onClick={() => go("ai_team")}>
                    Назад
                  </Button>
                  <Button
                    disabled={!state.conciergeName.trim()}
                    onClick={() => go("dashboard", { conciergeName: state.conciergeName })}
                  >
                    Continue
                  </Button>
                </div>
              </div>
              <Card title="Превью Concierge">
                <p className="text-xl font-medium">
                  {AVATARS.find((a) => a.id === state.conciergeAvatar)?.emoji}{" "}
                  {state.conciergeName || "Ваш Concierge"}
                </p>
                <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
                  {COMMUNICATION_STYLES.find((s) => s.id === state.conciergeStyle)?.sample}
                </p>
                <p className="mt-4 eds-type-small text-[var(--eds-text-muted)]">
                  Голос: {state.conciergeVoice} · Язык: {state.conciergeLanguage}
                </p>
              </Card>
            </section>
          ) : null}

          {state.step === "dashboard" ? (
            <section className="mx-auto max-w-2xl text-center">
              <Badge tone="success">Готово</Badge>
              <h2 className="mt-4 text-4xl font-semibold tracking-tight">Открываем Dashboard</h2>
              <p className="mt-3 text-[var(--eds-text-muted)]">
                Настройка завершена. Дальше — существующий Dashboard и рабочие пространства платформы.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Button variant="secondary" onClick={() => go("concierge")}>
                  Назад
                </Button>
                <Button
                  disabled={busy}
                  onClick={() => {
                    setMode(useThemeStore.getState().mode);
                    void finish();
                  }}
                >
                  {busy ? "Открываем…" : "Открыть Dashboard"}
                </Button>
              </div>
            </section>
          ) : null}
        </main>
      </div>
    </div>
  );
}
