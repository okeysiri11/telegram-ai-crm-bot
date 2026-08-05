/**
 * Sprint 30.3 — Invitation acceptance (Russian auth surface).
 * Complements /invite/accept ecosystem flow.
 */

import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button, Input } from "@/ui";
import { AuthLink, AuthShell } from "../../auth/components/AuthShell";
import { useAuthStore } from "@/auth/authStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { ORG_SELECTOR_OPTIONS } from "@/navigation/enterpriseRuNav";
import { saveFirstEntry } from "@/onboarding/firstEntryStore";

export function InvitationPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const setOrganization = useOrgSelector((s) => s.setOrganization);

  const inviteToken = useMemo(() => params.get("token") || params.get("invite") || "", [params]);
  const orgFromQuery = useMemo(() => params.get("org") || "demo-corp", [params]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"join" | "register">("join");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const tenant = ORG_SELECTOR_OPTIONS.some((o) => o.id === orgFromQuery)
        ? orgFromQuery
        : "demo-corp";
      setOrganization(tenant);
      if (mode === "register") {
        await register(email, password, tenant, name || email.split("@")[0]);
      } else {
        await login(email, password, tenant);
      }
      saveFirstEntry({
        companyName:
          ORG_SELECTOR_OPTIONS.find((o) => o.id === tenant)?.label || tenant,
        step: "role",
        completed: false,
      });
      navigate(
        `/onboarding/first-entry?invite=${encodeURIComponent(inviteToken)}&org=${encodeURIComponent(tenant)}`,
        { replace: true },
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка приглашения");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthShell
      title="Приглашение"
      subtitle={
        inviteToken
          ? `Токен приглашения получен · компания ${orgFromQuery}`
          : "Введите данные, чтобы присоединиться к компании"
      }
      footer={
        <div className="flex flex-col gap-1">
          <AuthLink to="/login">Уже есть аккаунт? Войти</AuthLink>
          <AuthLink to="/auth/register">Создать аккаунт без приглашения</AuthLink>
        </div>
      }
    >
      <div className="space-y-3">
        {!inviteToken ? (
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Откройте ссылку из письма или вставьте токен в адрес:{" "}
            <code>?token=…&amp;org=demo-corp</code>
          </p>
        ) : (
          <p className="eds-type-caption">Приглашение: {inviteToken.slice(0, 16)}…</p>
        )}
        <div className="flex gap-2">
          <Button
            type="button"
            size="sm"
            variant={mode === "join" ? "primary" : "secondary"}
            onClick={() => setMode("join")}
          >
            Войти и присоединиться
          </Button>
          <Button
            type="button"
            size="sm"
            variant={mode === "register" ? "primary" : "secondary"}
            onClick={() => setMode("register")}
          >
            Зарегистрироваться
          </Button>
        </div>
        {mode === "register" ? (
          <div>
            <label className="eds-type-label mb-1 block">Имя</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
        ) : null}
        <div>
          <label className="eds-type-label mb-1 block">Email</label>
          <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Пароль</label>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error ? (
          <p className="eds-type-caption text-[var(--eds-danger)]" role="alert">
            {error}
          </p>
        ) : null}
        <Button className="w-full" type="button" disabled={busy} onClick={() => void submit()}>
          {busy ? "Обработка…" : "Продолжить"}
        </Button>
      </div>
    </AuthShell>
  );
}
