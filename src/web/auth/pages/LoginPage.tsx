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

export function LoginPage() {
  const t = useI18n((s) => s.t);
  const setLocale = useI18n((s) => s.setLocale);
  const login = useAuthStore((s) => s.login);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const updatePrefs = usePreferencesStore((s) => s.update);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from || "/workspace";

  const { register, handleSubmit, formState } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema) as never,
    defaultValues: {
      identifier: "owner@demo.corp",
      password: "demo",
      rememberMe: true,
      tenantId: localStorage.getItem("ewp_remember_tenant") || "demo-corp",
      language: "en",
    },
  });

  return (
    <AuthShell
      title={t("app.title")}
      subtitle="Enterprise Identity Center · MFA ready"
      footer={<AuthLink to="/auth/forgot-password">Forgot password?</AuthLink>}
    >
      <form
        className="space-y-3"
        onSubmit={handleSubmit(async (values) => {
          const email = values.identifier.includes("@")
            ? values.identifier
            : `${values.identifier}@demo.corp`;
          await login(email, values.password, values.tenantId);
          const identity = identityManager.byEmail(email);
          const authUser = useAuthStore.getState().user;
          setWorkspace({
            company: values.tenantId,
            department: identity?.department || "operations",
            userContext: identity?.username || "user",
            permissions: authUser?.permissions?.length
              ? authUser.permissions
              : ["read", "write", "admin"],
          });
          setLocale(values.language);
          updatePrefs({ language: values.language });
          profileCenter.update({
            language: values.language,
            name: identity?.name || email.split("@")[0] || "user",
          });
          if (values.rememberMe) localStorage.setItem("ewp_remember_tenant", values.tenantId);
          navigate(from, { replace: true });
        })}
      >
        <div>
          <label className="eds-type-label mb-1 block">Email / Username</label>
          <Input className="eds-focus-ring" {...register("identifier")} />
          {formState.errors.identifier ? (
            <p className="eds-type-caption text-[var(--eds-danger)]">{formState.errors.identifier.message}</p>
          ) : null}
        </div>
        <div>
          <label className="eds-type-label mb-1 block">{t("auth.password")}</label>
          <Input type="password" className="eds-focus-ring" {...register("password")} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">{t("auth.tenant")}</label>
          <Select className="eds-focus-ring" {...register("tenantId")}>
            <option value="demo-corp">demo-corp</option>
            <option value="acme-ltd">acme-ltd</option>
          </Select>
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Language</label>
          <Select className="eds-focus-ring" {...register("language")}>
            <option value="en">English</option>
            <option value="ru">Русский</option>
            <option value="uk">Українська</option>
          </Select>
        </div>
        <label className="flex items-center gap-2 eds-type-small">
          <Checkbox {...register("rememberMe")} />
          Remember me
        </label>
        <Button className="w-full eds-type-button" type="submit" disabled={formState.isSubmitting}>
          {t("auth.login")}
        </Button>
        <p className="eds-type-caption text-[var(--eds-text-muted)]">
          Production auth: Enterprise ISAM + platform JWT when{" "}
          <code>VITE_IAM_LOGIN_SECRET</code> is set. Demo tokens are disabled.
        </p>
      </form>
    </AuthShell>
  );
}
