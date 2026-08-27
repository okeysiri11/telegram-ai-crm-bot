/**
 * Provider Connections — Recruiting → Integrations.
 * Secrets never rendered. LIVE / MOCK / NOT CONFIGURED are explicit.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Dialog, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { recruitingOpsGet, recruitingOpsPost } from "../business-ops/opsApi";
import { mapUiRoleToRecruiting } from "./recruitingLabels";
import { RecruitingOpsFrame } from "./RecruitingOpsFrame";

type WizardField = { id: string; label_ru: string; secret?: boolean; required?: boolean };
type ProviderCard = {
  provider?: string;
  label?: string;
  status?: string;
  status_label_ru?: string;
  mode?: string;
  mode_label_ru?: string;
  connection_type?: string;
  account_id?: string | null;
  last_successful_health_check?: string | null;
  last_error?: string | null;
  credential_presence?: { present?: boolean; fields?: Record<string, { present?: boolean }> };
  credential_expiry?: string | null;
  scopes?: string[];
  tracking_status?: string;
  mock?: boolean;
  wizard?: WizardField[];
  oauth_ready?: boolean;
  redirect_uri?: string;
  identity?: { id?: string; name?: string; username?: string };
  live_verified?: boolean;
  frozen?: boolean;
  connect_cta?: boolean;
  message_ru?: string;
};

function asRecord(json: unknown): Record<string, unknown> {
  return json && typeof json === "object" ? (json as Record<string, unknown>) : {};
}

function tone(status?: string, mock?: boolean): "success" | "info" | "warning" | "danger" | "default" {
  if (mock) return "warning";
  if (status === "CONNECTED") return "success";
  if (status === "NOT_CONFIGURED") return "info";
  if (status === "CONFIGURING") return "warning";
  if (status === "DEGRADED") return "warning";
  if (status === "ERROR") return "danger";
  return "default";
}

export function ProviderConnectionsPage() {
  const [params] = useSearchParams();
  const oauthStatus = params.get("status");
  const oauthProvider = params.get("oauth");
  const organizationId = useOrgSelector((s) => s.organizationId);
  const recruitingRole = mapUiRoleToRecruiting(useRoleSwitcher((s) => s.activeRoleId));
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<ProviderCard[]>([]);
  const [wizard, setWizard] = useState<ProviderCard | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [diagnostics, setDiagnostics] = useState<Record<string, unknown> | null>(null);
  const [testEmailTo, setTestEmailTo] = useState("");
  const [testEmailOpen, setTestEmailOpen] = useState(false);

  const headers = useMemo(
    () => ({
      "X-Organization-Id": organizationId,
      "X-Tenant-Id": organizationId,
      "X-Role": recruitingRole,
    }),
    [organizationId, recruitingRole],
  );

  const load = useCallback(async () => {
    setError(null);
    const res = await recruitingOpsGet("/providers", headers);
    if (!res.ok) {
      setError("Recruiting Ops API недоступен.");
      setItems([]);
      return;
    }
    const json = asRecord(res.json);
    setItems(Array.isArray(json.items) ? (json.items as ProviderCard[]) : []);
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const act = async (provider: string, action: string, extra: Record<string, unknown> = {}) => {
    await recruitingOpsPost(`/providers/${provider}/${action}`, extra, headers);
    await load();
  };

  const saveWizard = async () => {
    if (!wizard?.provider) return;
    const payload: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(form)) {
      if (value) payload[key] = value;
    }
    await recruitingOpsPost(`/providers/${wizard.provider}/configure`, payload, headers);
    setWizard(null);
    setForm({});
    await load();
  };

  return (
    <RecruitingOpsFrame
      title="Подключения провайдеров"
      subtitle="Интеграции. Секреты не показываются. MOCK отличается от LIVE."
      testId="provider-connections-page"
      error={error}
      onRefresh={() => void load()}
    >
      {oauthProvider ? (
        <p className="eds-type-helper" data-testid="oauth-flow-status">
          {oauthStatus === "connected" ? "Подключено" : oauthStatus === "error" ? "Ошибка подключения" : "Подключение..."}
        </p>
      ) : null}
      <div className="grid gap-3 md:grid-cols-2" data-testid="provider-connection-grid">
        {items.map((card) => {
          const frozen = Boolean(card.frozen) || card.status === "DISABLED";
          const emailStatusId =
            card.provider === "email"
              ? card.status === "CONNECTED"
                ? "email-status-connected"
                : card.status === "ERROR"
                  ? "email-status-error"
                  : "email-status-not-configured"
              : undefined;
          return (
          <Card key={card.provider} title={card.label || card.provider || ""}>
            <div data-testid={`provider-card-${card.provider}`}>
              <div className="flex flex-wrap gap-2">
                <Badge tone={tone(card.status, card.mock)}>{card.status_label_ru || card.status}</Badge>
                <Badge tone={card.mock ? "warning" : "info"}>{card.mock ? "MOCK" : card.mode_label_ru || "LIVE"}</Badge>
                {card.status === "NOT_CONFIGURED" ? <Badge tone="info">Не настроено</Badge> : null}
                {frozen ? (
                  <span data-testid="telegram-frozen-badge">
                    <Badge tone="warning">Заморожено</Badge>
                  </span>
                ) : null}
              </div>
              {emailStatusId ? (
                <p className="mt-1 eds-type-helper" data-testid={emailStatusId}>
                  {card.status_label_ru || card.status}
                </p>
              ) : null}
              {frozen ? (
                <p className="mt-2 eds-type-helper" data-testid="telegram-frozen-note">
                  {card.message_ru || "Telegram намеренно отключён."}
                </p>
              ) : null}
              <dl className="mt-2 grid grid-cols-1 gap-1 sm:grid-cols-2 eds-type-small" data-testid={`provider-meta-${card.provider}`}>
                <dt>Тип</dt>
                <dd>{card.connection_type || "—"}</dd>
                <dt>Аккаунт</dt>
                <dd>{card.account_id || card.identity?.name || card.identity?.username || "—"}</dd>
                <dt>Последняя проверка</dt>
                <dd>{card.last_successful_health_check || "—"}</dd>
                <dt>Ошибка</dt>
                <dd>{card.last_error || "—"}</dd>
                <dt>Секреты</dt>
                <dd>{card.credential_presence?.present ? "Заданы" : "Нет"}</dd>
                <dt>Срок секрета</dt>
                <dd>{card.credential_expiry || "—"}</dd>
                <dt>Разрешения</dt>
                <dd>{(card.scopes || []).join(", ") || "—"}</dd>
                <dt>Трекинг</dt>
                <dd>{card.tracking_status || "—"}</dd>
              </dl>
              {frozen ? null : (
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" onClick={() => { setWizard(card); setForm({}); }}>
                  Настроить
                </Button>
                {card.connect_cta !== false && (card.oauth_ready || card.provider === "meta" || card.provider === "google" || card.provider === "tiktok") ? (
                  <Button
                    size="sm"
                    variant="secondary"
                    data-testid={`provider-oauth-${card.provider}`}
                    onClick={async () => {
                      const res = await recruitingOpsGet(`/providers/${card.provider}/oauth/start`, headers);
                      const json = asRecord(res.json);
                      const url = String(json.authorize_url || "");
                      if (url) window.location.assign(url);
                    }}
                  >
                    Подключить
                  </Button>
                ) : null}
                <Button
                  size="sm"
                  variant="secondary"
                  data-testid={card.provider === "email" ? "email-check-connection" : undefined}
                  onClick={() => void act(card.provider || "", "test")}
                >
                  Проверить соединение
                </Button>
                {card.provider === "email" ? (
                  <Button size="sm" variant="secondary" data-testid="email-test-send" onClick={() => { setTestEmailOpen(true); setTestEmailTo(""); }}>
                    Тестовое письмо
                  </Button>
                ) : null}
                <Button size="sm" variant="secondary" onClick={() => void act(card.provider || "", "reconnect")}>
                  Переподключить
                </Button>
                <Button size="sm" variant="secondary" onClick={() => void act(card.provider || "", "disable")}>
                  Отключить
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={async () => {
                    const res = await recruitingOpsPost(`/providers/${card.provider}/diagnostics`, {}, headers);
                    setDiagnostics(asRecord(res.json));
                  }}
                >
                  Диагностика
                </Button>
              </div>
              )}
            </div>
          </Card>
          );
        })}
      </div>
      {diagnostics ? (
        <Card title="Диагностика">
          <pre className="eds-type-small whitespace-pre-wrap" data-testid="provider-diagnostics">
            {JSON.stringify(diagnostics, null, 2)}
          </pre>
        </Card>
      ) : null}
      <Dialog open={Boolean(wizard)} title={`Настройка: ${wizard?.label || ""}`} onClose={() => setWizard(null)}>
        <p className="eds-type-helper mb-2">Секреты не сохраняются в браузере.</p>
        {(wizard?.wizard || []).map((field) => (
          <label key={field.id} className="mb-2 block eds-type-small">
            {field.label_ru}
            <Input
              type={field.secret ? "password" : "text"}
              autoComplete="off"
              data-testid={field.secret ? `secret-input-${field.id}` : undefined}
              value={form[field.id] || ""}
              placeholder={field.secret ? "" : undefined}
              onChange={(ev) => setForm((prev) => ({ ...prev, [field.id]: ev.target.value }))}
            />
          </label>
        ))}
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={() => void saveWizard()}>
            Сохранить
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setWizard(null)}>
            Закрыть
          </Button>
        </div>
      </Dialog>
      <Dialog open={testEmailOpen} title="Тестовое письмо SMTP" onClose={() => setTestEmailOpen(false)}>
        <p className="eds-type-helper mb-2">Письмо отправится только по явной команде. Health check письма не шлёт.</p>
        <Input
          placeholder="email@example.com"
          value={testEmailTo}
          onChange={(ev) => setTestEmailTo(ev.target.value)}
          autoComplete="off"
        />
        <div className="mt-3 flex gap-2">
          <Button
            size="sm"
            data-testid="email-test-send-confirm"
            onClick={async () => {
              await recruitingOpsPost("/providers/email/test-email", { to: testEmailTo }, headers);
              setTestEmailOpen(false);
              await load();
            }}
          >
            Отправить тест
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setTestEmailOpen(false)}>
            Закрыть
          </Button>
        </div>
      </Dialog>
    </RecruitingOpsFrame>
  );
}
