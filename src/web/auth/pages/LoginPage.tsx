import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Button, Checkbox, Input } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { usePreferencesStore } from "@/preferences/preferencesStore";
import { loginSchema, type LoginForm } from "../schemas";
import { AuthLink, AuthShell } from "../components/AuthShell";
import { identityManager } from "../managers";
import { profileCenter } from "../managers/profileCenter";
import { isFirstEntryComplete, saveFirstEntry } from "@/onboarding/firstEntryStore";
import {
  isDemoAuthEnabled,
  isGoogleAuthConfigured,
  OWNER_DEMO_EMAIL,
  OWNER_DEMO_TENANT,
} from "@/auth/demoAuthProvider";
import { postAuthDestination } from "@/navigation/roleHome";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { openOwnerDemoWorkspace } from "@/multi-role/applyDemoSession";
import { resolvePostLoginPath } from "@/navigation/safeReturnTo";

export function LoginPage() {
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const login = useAuthStore((s) => s.login);
  const loginWithGoogle = useAuthStore((s) => s.loginWithGoogle);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const updatePrefs = usePreferencesStore((s) => s.update);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const demoMode = isDemoAuthEnabled();
  const googleReady = isGoogleAuthConfigured();
  const [mode, setMode] = useState<"chooser" | "email">(googleReady && !demoMode ? "chooser" : "email");
  const [googleBusy, setGoogleBusy] = useState(false);

  const { register, handleSubmit, formState, getValues } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema) as never,
    defaultValues: {
      identifier: OWNER_DEMO_EMAIL,
      password: "",
      rememberMe: true,
      tenantId: OWNER_DEMO_TENANT,
      language: "ru",
    },
  });

  async function afterAuth(email: string, tenantId: string, language: LoginForm["language"]) {
    const identity = identityManager.byEmail(email);
    const authUser = useAuthStore.getState().user;
    const sessionTenant = authUser?.tenantId || tenantId || OWNER_DEMO_TENANT;
    setWorkspace({
      company: sessionTenant,
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
    localStorage.setItem("ewp_remember_tenant", sessionTenant);
    useOrgSelector.getState().setOrganization(sessionTenant);

    const isClientUser =
      authUser?.roleId === "client" || email.toLowerCase().includes("travel@") || email.toLowerCase().startsWith("client@");
    const isOwner = authUser?.roleId === "platform_owner" || authUser?.roleId === "owner";
    if (!isClientUser && !isOwner && !isFirstEntryComplete()) {
      saveFirstEntry({
        completed: false,
        step: "welcome",
        roleId: authUser?.roleId || "",
        companyName: sessionTenant || "ADOS Platform",
        language,
        workspaceId: `ws_${sessionTenant}`,
      });
    }

    const roleHome = postAuthDestination(useRoleSwitcher.getState().activeRoleId || authUser?.roleId, email);
    const next = resolvePostLoginPath({
      queryReturnTo: searchParams.get("returnTo"),
      stateFrom: (location.state as { from?: string } | null)?.from,
      roleHome,
    });
    navigate(next, { replace: true });
  }

  return (
    <AuthShell
      title={t("app.title")}
      subtitle={demoMode ? "Локальный Owner login" : "Корпоративная аутентификация"}
      footer={
        <div className="flex flex-col gap-1">
          {demoMode ? null : <AuthLink to="/auth/register">Создать аккаунт</AuthLink>}
          {demoMode ? null : <AuthLink to="/auth/invite">Приглашение</AuthLink>}
          <AuthLink to="/auth/forgot-password">Восстановить пароль</AuthLink>
        </div>
      }
    >
      {mode === "chooser" ? (
        <div className="space-y-3">
          {googleReady ? (
            <Button
              className="w-full eds-type-button"
              type="button"
              disabled={googleBusy}
              onClick={async () => {
                setError(null);
                setGoogleBusy(true);
                try {
                  const tenantId = getValues("tenantId") || OWNER_DEMO_TENANT;
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
          ) : null}
          <Button
            className="w-full"
            type="button"
            variant="secondary"
            onClick={() => setMode("email")}
          >
            Войти по Email
          </Button>
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
                : `${values.identifier}@ados.demo`;
              const tenantId = OWNER_DEMO_TENANT;
              await login(email, values.password, tenantId);
              if (values.rememberMe) localStorage.setItem("ewp_remember_tenant", tenantId);
              await afterAuth(email, tenantId, values.language);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Ошибка входа");
            }
          })}
        >
          <div>
            <label className="eds-type-label mb-1 block">{t("auth.email")}</label>
            <Input className="eds-focus-ring" {...register("identifier")} autoComplete="username" />
            {formState.errors.identifier ? (
              <p className="eds-type-caption text-[var(--eds-danger)]">
                {formState.errors.identifier.message}
              </p>
            ) : null}
          </div>
          <div>
            <label className="eds-type-label mb-1 block">{t("auth.password")}</label>
            <Input type="password" className="eds-focus-ring" {...register("password")} autoComplete="current-password" />
          </div>
          <input type="hidden" {...register("tenantId")} />
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
          {demoMode ? (
            <Button
              type="button"
              variant="secondary"
              className="w-full"
              data-testid="open-owner-workspace"
              onClick={async () => {
                setError(null);
                try {
                  const creds = openOwnerDemoWorkspace();
                  await login(creds.email, creds.password, creds.tenantId);
                  await afterAuth(creds.email, creds.tenantId, "ru");
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Ошибка входа");
                }
              }}
            >
              Открыть пространство Owner
            </Button>
          ) : null}
          {googleReady ? (
            <Button className="w-full" type="button" variant="ghost" onClick={() => setMode("chooser")}>
              ← Назад
            </Button>
          ) : null}
        </form>
      )}
    </AuthShell>
  );
}
