import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Checkbox, Input, Select } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { loginSchema, type LoginForm } from "../schemas";
import { AuthLink, AuthShell } from "../components/AuthShell";
import { identityManager } from "../managers";
import { profileCenter } from "../managers/profileCenter";
import { isFirstEntryComplete, saveFirstEntry } from "@/onboarding/firstEntryStore";
import { isDemoAuthEnabled } from "@/auth/demoAuthProvider";
import { postAuthDestination } from "@/navigation/roleHome";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { MULTI_ROLE_DEMO_USERS } from "@/multi-role/demoUsers";
import { openClientDemoWorkspace } from "@/multi-role/applyDemoSession";

export function LoginPage() {
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const login = useAuthStore((s) => s.login);
  const loginWithGoogle = useAuthStore((s) => s.loginWithGoogle);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const updatePrefs = usePreferencesStore((s) => s.update);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from || "/dashboard";
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"chooser" | "email">("chooser");
  const [googleBusy, setGoogleBusy] = useState(false);

  const { register, handleSubmit, formState, getValues, setValue } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema) as never,
    defaultValues: {
      identifier: isDemoAuthEnabled() ? "travel@globefly.demo" : "",
      password: isDemoAuthEnabled() ? "demo" : "",
      rememberMe: true,
      tenantId: localStorage.getItem("ewp_remember_tenant") || (isDemoAuthEnabled() ? "globefly" : ""),
      language: "ru",
    },
  });

  async function afterAuth(email: string, tenantId: string, language: LoginForm["language"]) {
    const identity = identityManager.byEmail(email);
    const authUser = useAuthStore.getState().user;
    setWorkspace({
      company: tenantId,
      department: identity?.department || "operations",
      userContext: identity?.username || "user",
      permissions: authUser?.permissions?.length
        ? authUser.permissions
        : ["read", "write", "admin"],
    });
    setLocale(language);
    updatePrefs({ language });
    profileCenter.update({
      language,
      name: identity?.name || authUser?.name || email.split("@")[0] || "user",
    });
    localStorage.setItem("ewp_remember_tenant", tenantId);
    useOrgSelector.getState().setOrganization(tenantId || "ados");

    // Seed first-run wizard for new sessions; clients use /onboarding/client.
    const isClientUser =
      authUser?.roleId === "client" || email.toLowerCase().includes("travel@") || email.toLowerCase().startsWith("client@");
    if (!isClientUser && !isFirstEntryComplete()) {
      saveFirstEntry({
        completed: false,
        step: "welcome",
        roleId: authUser?.roleId || "",
        companyName: tenantId || "Demo Corp",
        language,
        workspaceId: `ws_${tenantId}`,
      });
    }

    const roleHome = postAuthDestination(useRoleSwitcher.getState().activeRoleId || authUser?.roleId, email);
    const next =
      from.startsWith("/onboarding") || from === "/login" ? roleHome : from || roleHome;
    navigate(next, { replace: true });
  }

  return (
    <AuthShell
      title={t("app.title")}
      subtitle="Корпоративная аутентификация · Google · MFA"
      footer={
        <div className="flex flex-col gap-1">
          <AuthLink to="/auth/register">Создать аккаунт</AuthLink>
          <AuthLink to="/auth/invite">Приглашение</AuthLink>
          <AuthLink to="/auth/forgot-password">Восстановить пароль</AuthLink>
        </div>
      }
    >
      {mode === "chooser" ? (
        <div className="space-y-3">
          <Button
            className="w-full eds-type-button"
            type="button"
            disabled={googleBusy}
            onClick={async () => {
              setError(null);
              setGoogleBusy(true);
              try {
                const tenantId = getValues("tenantId") || "demo-corp";
                const language = getValues("language") || "ru";
                await loginWithGoogle({
                  email: "user@gmail.com",
                  name: "Google User",
                  tenantId,
                  rememberMe: true,
                });
                const email = useAuthStore.getState().user?.email || "user@gmail.com";
                await afterAuth(email, tenantId, language);
              } catch (err) {
                setError(err instanceof Error ? err.message : "Ошибка входа через Google");
              } finally {
                setGoogleBusy(false);
              }
            }}
          >
            {googleBusy ? "Вход…" : "Продолжить через Google"}
          </Button>
          <Button
            className="w-full"
            type="button"
            variant="secondary"
            onClick={() => setMode("email")}
          >
            Войти по Email
          </Button>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Google — основной способ входа для Beta. Microsoft, Apple, GitHub и Telegram будут
            добавлены позже.
            {isDemoAuthEnabled() ? " · Локальный demo-режим включён" : null}
          </p>
          {isDemoAuthEnabled() ? (
            <div className="rounded-md border border-[var(--ew-border)] p-2 space-y-2" data-testid="demo-accounts">
              <p className="eds-type-caption font-medium">Демо-аккаунты (пароль: demo)</p>
              <Select
                className="eds-focus-ring w-full"
                defaultValue=""
                onChange={(e) => {
                  const u = MULTI_ROLE_DEMO_USERS.find((x) => x.email === e.target.value);
                  if (!u) return;
                  setValue("identifier", u.email);
                  setValue("password", u.password);
                  setValue("tenantId", u.tenantId);
                  setMode("email");
                }}
                aria-label="Демо-аккаунты"
              >
                <option value="">Выберите роль / компанию…</option>
                {MULTI_ROLE_DEMO_USERS.map((u) => (
                  <option key={u.email} value={u.email}>
                    {u.company} — {u.email}
                  </option>
                ))}
              </Select>
              <Button
                type="button"
                size="sm"
                className="ews-primary-cta w-full"
                onClick={async () => {
                  setError(null);
                  try {
                    const creds = openClientDemoWorkspace();
                    await login(creds.email, creds.password, creds.tenantId);
                    await afterAuth(creds.email, creds.tenantId, "ru");
                  } catch (err) {
                    setError(err instanceof Error ? err.message : "Ошибка демо-входа");
                  }
                }}
              >
                Открыть демо-пространство
              </Button>
            </div>
          ) : null}
          {error ? (
            <p
              className="rounded-md border border-[var(--eds-danger)]/40 bg-[var(--eds-danger-soft)] px-3 py-2 eds-type-caption text-[var(--eds-danger)]"
              role="alert"
            >
              {error}
            </p>
          ) : null}
        </div>
      ) : (
        <form
          className="space-y-3"
          onSubmit={handleSubmit(async (values) => {
            setError(null);
            try {
              const email = values.identifier.includes("@")
                ? values.identifier
                : `${values.identifier}@demo.corp`;
              await login(email, values.password, values.tenantId);
              if (values.rememberMe) localStorage.setItem("ewp_remember_tenant", values.tenantId);
              await afterAuth(email, values.tenantId, values.language);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Ошибка входа");
            }
          })}
        >
          <div>
            <label className="eds-type-label mb-1 block">{t("auth.email")}</label>
            <Input className="eds-focus-ring" {...register("identifier")} />
            {formState.errors.identifier ? (
              <p className="eds-type-caption text-[var(--eds-danger)]">
                {formState.errors.identifier.message}
              </p>
            ) : null}
          </div>
          <div>
            <label className="eds-type-label mb-1 block">{t("auth.password")}</label>
            <Input type="password" className="eds-focus-ring" {...register("password")} />
          </div>
          <div>
            <label className="eds-type-label mb-1 block">{t("auth.tenant")}</label>
            <Select className="eds-focus-ring" {...register("tenantId")}>
              <option value="ados">ados</option>
              <option value="globefly">globefly</option>
              <option value="crypto-desk">crypto-desk</option>
              <option value="buildcorp">buildcorp</option>
              <option value="skyfleet">skyfleet</option>
              <option value="prime-auto">prime-auto</option>
              <option value="lex">lex</option>
              <option value="greenfield">greenfield</option>
              <option value="seller-co">seller-co</option>
              <option value="demo-corp">demo-corp</option>
              <option value="acme-ltd">acme-ltd</option>
            </Select>
          </div>
          <div>
            <label className="eds-type-label mb-1 block">Язык</label>
            <Select className="eds-focus-ring" {...register("language")}>
              <option value="ru">Русский</option>
              <option value="en">English</option>
              <option value="uk">Українська</option>
            </Select>
          </div>
          <label className="flex items-center gap-2 eds-type-small">
            <Checkbox {...register("rememberMe")} />
            Запомнить меня
          </label>
          {error ? (
            <p
              className="rounded-md border border-[var(--eds-danger)]/40 bg-[var(--eds-danger-soft)] px-3 py-2 eds-type-caption text-[var(--eds-danger)]"
              role="alert"
            >
              {error}
            </p>
          ) : null}
          <Button className="w-full eds-type-button" type="submit" disabled={formState.isSubmitting}>
            {formState.isSubmitting ? "Вход…" : "Войти по Email"}
          </Button>
          <Button className="w-full" type="button" variant="ghost" onClick={() => setMode("chooser")}>
            ← Назад
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
