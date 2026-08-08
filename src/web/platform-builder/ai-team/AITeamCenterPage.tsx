import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, EmptyState, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { PLATFORM_BUILDER_API } from "../types";
import { AITeamCollaborationWorkspace } from "@/ai-team-collaboration";
import { bu } from "../i18n/builderUiRu";
import { builderDisplayName } from "@/i18n/platformGlossary";

type TeamMember = {
  agent_id: string;
  name: string;
  avatar: string;
  profession: string;
  specialization: string;
  status: string;
  current_task?: string | null;
  memory_usage?: number;
  last_activity?: string;
  capabilities?: string[];
  paused?: boolean;
};

type TeamDashboard = {
  title: string;
  organization_id: string;
  count: number;
  active: number;
  paused: number;
  members: TeamMember[];
  owner_actions: string[];
  group_ai_chat: Record<string, unknown>;
  ready: boolean;
};

const ACTION_LABELS: Record<string, string> = {
  open_chat: "Открыть чат",
  assign_task: "Назначить задачу",
  view_knowledge: "Открыть знания",
  view_memory: "Открыть память",
  pause_agent: "Приостановить агента",
  resume_agent: "Возобновить агента",
  edit_agent: "Изменить агента",
  replace_agent: "Заменить агента",
  remove_agent: "Удалить агента",
};

export function AITeamCenterPage() {
  const [orgId, setOrgId] = useState("org_demo");
  const [dash, setDash] = useState<TeamDashboard | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/dashboard`,
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Не удалось загрузить команду AI");
      setDash(data as TeamDashboard);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : bu("loadFailed"));
    } finally {
      setBusy(false);
    }
  }, [orgId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(agentId: string, action: string) {
    setBusy(true);
    setMessage(null);
    try {
      const payload: Record<string, unknown> = {};
      if (action === "assign_task") payload.task = "Задача от владельца";
      if (action === "edit_agent") payload.name = undefined;
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_id: agentId, action, payload }),
        },
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Ошибка действия");
      setDash(data.dashboard as TeamDashboard);
      setMessage(`${ACTION_LABELS[action] || action} — выполнено`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Ошибка действия");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title={builderDisplayName("ai_team")}
      subtitle="Все AI-специалисты организации. Консьерж управляет. Специалисты выполняют."
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge tone="success">{bu("ready")}</Badge>
        <Badge>Без лимита специалистов</Badge>
        <Badge>Групповой AI-чат</Badge>
        <Badge>Мультиагентное пространство</Badge>
        <Input
          className="max-w-xs"
          value={orgId}
          onChange={(e) => setOrgId(e.target.value)}
          placeholder="ID организации"
        />
        <Button disabled={busy} onClick={() => void load()}>
          {bu("refresh")}
        </Button>
      </div>

      <AITeamCollaborationWorkspace apiMembers={dash?.members} />

      {message ? <p className="eds-type-small text-[var(--eds-text-muted)]">{message}</p> : null}

      {dash ? (
        <>
          <div className="flex flex-wrap gap-4 eds-type-small">
            <span>Специалисты: {dash.count}</span>
            <span>Активные: {dash.active}</span>
            <span>На паузе: {dash.paused}</span>
          </div>

          <div className="eds-grid eds-grid--dashboard">
            {dash.members.length ? (
              dash.members.map((m) => (
                <Card key={m.agent_id} title={`${m.avatar} ${m.name}`}>
                  <ul className="space-y-1 eds-type-small">
                    <li>Назначение: {m.profession}</li>
                    <li>Специализация: {m.specialization}</li>
                    <li>Статус: {m.status}</li>
                    <li>Текущая задача: {m.current_task || "—"}</li>
                    <li>Память: {Math.round((m.memory_usage || 0) * 100)}%</li>
                    <li>Активность: {m.last_activity || "—"}</li>
                    <li>Навыки: {(m.capabilities || []).join(", ") || "—"}</li>
                  </ul>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(dash.owner_actions || []).map((action) => (
                      <Button
                        key={action}
                        variant="ghost"
                        disabled={busy}
                        onClick={() => void runAction(m.agent_id, action)}
                      >
                        {ACTION_LABELS[action] || action}
                      </Button>
                    ))}
                  </div>
                </Card>
              ))
            ) : (
              <div>
                <EmptyState
                  title="Пока нет AI-специалистов"
                  description="Центр команды AI готов, но в организации ещё нет специалистов. Создайте первого агента в студии AI."
                  actionLabel="Открыть мастер студии AI"
                  actionTo="/platform-builder/builder-studio?mode=wizard"
                  illustration="◇"
                />
              </div>
            )}
          </div>

          <Card title="Основа группового AI-чата">
            <Badge>Архитектура</Badge>
            <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
              {(dash.group_ai_chat as { description?: string })?.description ||
                "Владелец приглашает специалистов для совместного обсуждения."}
            </p>
            <p className="mt-1 eds-type-caption">
              Роли для приглашения:{" "}
              {((dash.group_ai_chat as { invite_roles?: string[] })?.invite_roles || []).join(", ")}
            </p>
          </Card>
        </>
      ) : (
        <div>
          {busy ? (
            <p className="eds-type-small">Загрузка центра команды AI…</p>
          ) : (
            <EmptyState
              title={builderDisplayName("ai_team")}
              description="Здесь собираются специалисты организации. Если агентов ещё нет — начните с мастера студии AI."
              actionLabel="Создать агента"
              actionTo="/platform-builder/builder-studio?mode=wizard"
              illustration="◇"
            />
          )}
        </div>
      )}
    </PlatformBuilderLayout>
  );
}
