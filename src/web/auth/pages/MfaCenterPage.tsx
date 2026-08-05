import { useEffect, useState } from "react";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Badge, Button, Card } from "@/ui";
import { mfaCenter } from "../managers";
import { Link } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";

export function MfaCenterPage() {
  const user = useAuthStore((s) => s.user);
  const [required, setRequired] = useState(false);
  const [orgRequired, setOrgRequired] = useState(false);
  const recovery = mfaCenter.recoveryFlow();

  useEffect(() => {
    document.title = "MFA · ADOS";
    if (!user?.identityId) return;
    void mfaCenter.fetchRequirement(user.identityId, user.tenantId).then((r) => {
      setRequired(Boolean(r.must_challenge ?? r.required));
      setOrgRequired(Boolean(r.org_required));
      if (r.user_enabled != null) mfaCenter.status.totpEnabled = Boolean(r.user_enabled);
    });
  }, [user?.identityId, user?.tenantId]);

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Многофакторная аутентификация</h1>
        <p className="eds-type-helper">
          MFA опциональна для пользователей. Организация может требовать MFA через политику безопасности.
        </p>
        <div className="eds-grid eds-grid--dashboard">
          <Card title="Методы">
            <ul className="space-y-1">
              {mfaCenter.methods.map((m) => (
                <li key={m}>
                  <Badge>{m}</Badge>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Расширения (готовы)">
            <ul className="space-y-1">
              {mfaCenter.extensionsReady.map((m) => (
                <li key={m} className="eds-type-small">
                  {m}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Статус">
            <p className="eds-type-small">
              Пользователь: {mfaCenter.status.totpEnabled ? "включено" : "выключено"}
            </p>
            <p className="eds-type-small">
              Требуется сейчас: {required ? "да" : "нет"}
            </p>
            <p className="eds-type-small">
              Политика организации: {orgRequired ? "MFA обязательна" : "не обязательна"}
            </p>
            <div className="mt-2 flex gap-2">
              <Button
                size="sm"
                onClick={() => {
                  if (!user?.identityId) return;
                  void mfaCenter.enable(user.identityId).then(() => setRequired(true));
                }}
              >
                Включить MFA
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={orgRequired}
                onClick={() => {
                  if (!user?.identityId) return;
                  void mfaCenter.disable(user.identityId).then(() => {
                    if (!orgRequired) setRequired(false);
                  });
                }}
              >
                Отключить MFA
              </Button>
            </div>
          </Card>
          <Card title="Восстановление">
            <p className="eds-type-small">{recovery.steps.join(" → ")}</p>
            <Link
              className="mt-2 inline-block text-[var(--eds-primary)] eds-type-small"
              to="/auth/mfa"
            >
              Экран проверки
            </Link>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
