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
  isGoogleAuthConfigured,
  isLocalOwnerLoginEnabled,
  OWNER_DEMO_EMAIL,
  OWNER_DEMO_TENANT,
} from "@/auth/demoAuthProvider";
import { postAuthDestination } from "@/navigation/roleHome";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { openOwnerDemoWorkspace } from "@/multi-role/applyDemoSession";
import { resolvePostLoginPath } from "@/navigation/safeReturnTo";

function isBlockingAuthBackendError(message: string): boolean {
  return /authentication backend unavailable|ISAM proxy|localhost:8080/i.test(message);
}

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
  const localOwner = isLocalOwnerLoginEnabled();
  const googleReady = isGoogleAuthConfigured() && !localOwner;
  const [mode, setMode] = useState<"chooser" | "email">(googleReady ? "chooser" : "email");
  const [googleBusy, setGoogleBusy] = useState(false);
  const [ownerBusy, setOwnerBusy] = useState(false);

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

  function showLoginError(err: unknown) {
    const message = err instanceof Error ? err.message : "Ошибка входа";
    if (localOwner && isBlockingAuthBackendError(message)) {
      setError(null);
      return;
    }
    setError(message);
  }

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

  async function enterAsOwner() {
    setError(null);
    setOwnerBusy(true);
    try {
      const creds = openOwnerDemoWorkspace();
      await login(creds.email, creds.password, creds.tenantId);
      await afterAuth(creds.email, creds.tenantId, "ru");
    } catch (err) {
      showLoginError(err);
    } finally {
      setOwnerBusy(false);
    }
  }

  const emailForm = (
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
          showLoginError(err);
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
      {error && !localOwner ? (
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
    </form>
  );

  return (
    <AuthShell
      title={t("app.title")}
      subtitle={localOwner ? "Локальный Owner login" : "Корпоративная аутентификация"}
      footer={
        localOwner ? null : (
          <div className="flex flex-col gap-1">
            <AuthLink to="/auth/register">Создать аккаунт</AuthLink>
            <AuthLink to="/auth/invite">Приглашение</AuthLink>
            <AuthLink to="/auth/forgot-password">Восстановить пароль</AuthLink>
          </div>
        )
      }
    >
      {localOwner ? (
        <div className="space-y-4">
          <p
            className="rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface-muted,transparent)] px-3 py-2 eds-type-caption text-[var(--eds-text-muted)]"
            data-testid="local-owner-status"
          >
            External authentication services are offline. Local Owner mode is available.
          </p>
          <Button
            type="button"
            className="w-full eds-type-button"
            data-testid="login-as-owner"
            disabled={ownerBusy}
            onClick={() => void enterAsOwner()}
          >
            {ownerBusy ? "Вход…" : "Войти как Owner"}
          </Button>
          {error && !isBlockingAuthBackendError(error) ? (
            <p
              className="rounded-md border border-[var(--eds-danger)]/40 bg-[var(--eds-danger-soft)] px-3 py-2 eds-type-caption text-[var(--eds-danger)]"
              role="alert"
            >
              {error}
            </p>
          ) : null}
          <details className="rounded-md border border-[var(--eds-border)] px-3 py-2" data-testid="local-auth-advanced">
            <summary className="cursor-pointer eds-type-small text-[var(--eds-text-muted)]">
              Другие способы входа
            </summary>
            <div className="mt-3 space-y-3">
              {emailForm}
              <p className="eds-type-caption text-[var(--eds-text-muted)]">Google login — Недоступно в локальном режиме</p>
              <p className="eds-type-caption text-[var(--eds-text-muted)]">Регистрация — Недоступно в локальном режиме</p>
              <p className="eds-type-caption text-[var(--eds-text-muted)]">
                Восстановление пароля — Недоступно в локальном режиме
              </p>
            </div>
          </details>
        </div>
      ) : mode === "chooser" ? (
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
                  showLoginError(err);
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
        <div className="space-y-3">
          {emailForm}
          {googleReady ? (
            <Button className="w-full" type="button" variant="ghost" onClick={() => setMode("chooser")}>
              ← Назад
            </Button>
          ) : null}
        </div>
      )}
    </AuthShell>
  );
}
