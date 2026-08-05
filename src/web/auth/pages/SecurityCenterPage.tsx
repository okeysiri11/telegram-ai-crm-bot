import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card, Badge, Button } from "@/ui";
import { securityCenter } from "../managers";
import { hubIntegrations } from "@/integrations/hub";
import { useAuthStore } from "@/auth/authStore";

type OwnerSnap = {
  active_sessions?: number;
  failed_logins?: number;
  sessions?: Array<Record<string, unknown>>;
  failed_login_events?: Array<Record<string, unknown>>;
  audit_events?: Array<Record<string, unknown>>;
  api_status?: { ok?: boolean; tokens_active?: number };
  token_status?: { active?: number; total?: number };
  mfa?: { challenges?: number };
};

export function SecurityCenterPage() {
  const snap = securityCenter.snapshot();
  const localEvents = securityCenter.events();
  const user = useAuthStore((s) => s.user);
  const [owner, setOwner] = useState<OwnerSnap | null>(null);

  useEffect(() => {
    document.title = "Безопасность · ADOS";
    void fetch(`${hubIntegrations.authentication}/dashboard?dashboard_type=owner_security`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && typeof data === "object") setOwner(data as OwnerSnap);
      })
      .catch(() => setOwner(null));
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h1 className="eds-type-h1">Панель безопасности владельца</h1>
            <p className="eds-type-helper">
              Zero Trust · риск · инциденты · сессии · MFA · аудит
              {user?.email ? ` · ${user.email}` : ""}
              {snap.version ? ` · v${snap.version}` : ""}
            </p>
          </div>
          <div className="flex gap-2">
            <Link to="/identity/sessions" className="eds-type-small text-[var(--eds-primary)]">
              Сессии →
            </Link>
            <Link to="/identity/mfa" className="eds-type-small text-[var(--eds-primary)]">
              MFA →
            </Link>
          </div>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Активные сессии">
            <p className="eds-type-h3">{owner?.active_sessions ?? snap.trustedDevices}</p>
          </Card>
          <Card title="Неудачные входы">
            <p className="eds-type-h3">{owner?.failed_logins ?? snap.failedAttempts}</p>
          </Card>
          <Card title="Статус MFA">
            <Badge>{snap.mfaStatus}</Badge>
          </Card>
          <Card title="События безопасности">
            <p className="eds-type-h3">
              {owner?.audit_events?.length ?? snap.securityEvents}
            </p>
          </Card>
          <Card title="API">
            <Badge>{owner?.api_status?.ok === false ? "ошибка" : "ok"}</Badge>
          </Card>
          <Card title="Токены">
            <p className="eds-type-h3">
              {owner?.token_status?.active ?? "—"} / {owner?.token_status?.total ?? "—"}
            </p>
          </Card>
          <Card title="Лимиты запросов">
            <p className="eds-type-h3">0</p>
          </Card>
          <Card title="Риск">
            <p className="eds-type-h3">{snap.riskScore}</p>
          </Card>
          <Card title="Zero Trust">
            <Badge>{snap.zeroTrust ? "active" : "off"}</Badge>
          </Card>
          <Card title="Security Health">
            <Badge>{snap.health ?? "healthy"}</Badge>
          </Card>
          <Card title="Открытые инциденты">
            <p className="eds-type-h3">{snap.openIncidents ?? 0}</p>
          </Card>
        </div>

        <Card title="Недавние события аудита">
          <ul className="space-y-1 eds-type-small">
            {(owner?.audit_events || [])
              .slice(-12)
              .reverse()
              .map((e, i) => (
                <li key={String(e.audit_id || i)}>
                  {String(e.action || "event")} · {String(e.actor || "")} · {String(e.at || "")}
                </li>
              ))}
            {!owner?.audit_events?.length
              ? localEvents.map((e) => (
                  <li key={e.id}>
                    {e.type} · {e.at}
                  </li>
                ))
              : null}
          </ul>
        </Card>

        <Card title="Активные устройства / сессии">
          <ul className="space-y-1 eds-type-small">
            {(owner?.sessions || []).slice(0, 10).map((s) => (
              <li key={String(s.session_id)}>
                {String(s.device || "device")} · {String(s.ip || "")} ·{" "}
                {s.trusted ? "доверенное" : "обычное"} · {String(s.last_activity || s.at || "")}
              </li>
            ))}
            {!owner?.sessions?.length ? (
              <li>Нет данных с ISAM — показаны локальные метрики.</li>
            ) : null}
          </ul>
          <div className="mt-3">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                void fetch(`${hubIntegrations.authentication}/sessions`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    action: "terminate_all",
                    identity_id: user?.identityId || "",
                  }),
                }).then(() => window.location.reload());
              }}
            >
              Выйти со всех устройств
            </Button>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
