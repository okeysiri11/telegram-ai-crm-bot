/**
 * AGRO 1.2 — notification actions.
 */

import { useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsPost, pick } from "../business-ops/opsApi";
import { ruStatus } from "./agroLabels";

type Row = Record<string, unknown>;

const ACTIONS = [
  ["open", "Открыть"],
  ["mark_read", "Отметить прочитанным"],
  ["create_task", "Создать задачу"],
  ["add_calendar", "Добавить в календарь"],
  ["snooze", "Отложить"],
  ["disable_rule", "Отключить правило"],
] as const;

export function AgroNotificationsPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  notifications: Row[];
  onChanged: () => void;
  onOpenLinked: (kind: string, id: string) => void;
  onCreateRule: () => void;
  onCreateReminder: () => void;
}) {
  const [msg, setMsg] = useState("");
  const [rule, setRule] = useState({ commodity: "Пшеница", operator: "lt", target_price: "8500" });
  const [showRule, setShowRule] = useState(false);

  async function act(id: string, action: string) {
    const res = await agroOpsPost(`/notifications/${id}/actions`, { action, title: "Проверить сигнал" }, props.headers);
    const j = res.json as { ok?: boolean; message_ru?: string; linked?: Row; item?: Row };
    setMsg(j.ok ? `Сделано: ${action}` : j.message_ru || "Ошибка");
    if (j.ok && action === "open" && j.linked) {
      props.onOpenLinked(String(j.linked.record_kind || j.item?.entity_type || "market_price"), pick(j.linked, "id"));
    }
    if (j.ok) props.onChanged();
  }

  return (
    <div className="grid gap-3" data-testid="agro-notifications-panel">
      {props.canOperate ? (
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={() => setShowRule(true)}>Создать правило</Button>
          <Button size="sm" variant="ghost" onClick={props.onCreateReminder}>Создать напоминание</Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={async () => {
              const r = await agroOpsPost("/alerts/evaluate", {}, props.headers);
              const j = r.json as { ok?: boolean; created?: number; message_ru?: string };
              setMsg(j.ok ? `Проверено, новых сигналов: ${j.created ?? 0}` : j.message_ru || "Ошибка");
              if (j.ok) props.onChanged();
            }}
          >
            Проверить правила
          </Button>
        </div>
      ) : null}
      {!props.notifications.length ? (
        <Card title="Пока нет сигналов.">
          <div className="flex flex-wrap gap-2">
            {props.canOperate ? <Button size="sm" onClick={() => { setShowRule(true); props.onCreateRule(); }}>Создать правило</Button> : null}
            {props.canOperate ? <Button size="sm" variant="ghost" onClick={props.onCreateReminder}>Создать напоминание</Button> : null}
          </div>
        </Card>
      ) : (
        <ul className="eds-type-small">
          {props.notifications.map((n) => (
            <li key={pick(n, "id")} className="border-b border-[var(--ew-border)] py-2" data-testid="agro-notification-row">
              <div className="flex justify-between gap-2">
                <button
                  type="button"
                  className="min-h-11 text-left underline"
                  data-testid="agro-notification-linked"
                  onClick={() => void act(pick(n, "id"), "open")}
                >
                  {Boolean(n.is_demo) ? "[DEMO] " : ""}
                  {pick(n, "title")} · {ruStatus(pick(n, "status"))}
                </button>
              </div>
              {props.canOperate ? (
                <div className="mt-1 flex flex-wrap gap-1">
                  {ACTIONS.map(([id, label]) => (
                    <Button key={id} size="sm" className="min-h-11" variant="ghost" onClick={() => void act(pick(n, "id"), id)}>
                      {label}
                    </Button>
                  ))}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {props.canOperate && showRule ? (
        <Card title="Правило цены">
          <div className="grid gap-2 sm:grid-cols-3">
            <Input placeholder="Культура" value={rule.commodity} onChange={(e) => setRule((f) => ({ ...f, commodity: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={rule.operator} onChange={(e) => setRule((f) => ({ ...f, operator: e.target.value }))}>
              <option value="lt">&lt;</option>
              <option value="gt">&gt;</option>
            </select>
            <Input placeholder="Цена" value={rule.target_price} onChange={(e) => setRule((f) => ({ ...f, target_price: e.target.value }))} />
          </div>
          <Button
            className="mt-2"
            size="sm"
            onClick={async () => {
              const r = await agroOpsPost("/entities/alert_rule", rule, props.headers);
              const j = r.json as { ok?: boolean; message_ru?: string };
              setMsg(j.ok ? "Правило сохранено" : j.message_ru || "Ошибка");
              if (j.ok) props.onChanged();
            }}
          >
            Сохранить правило
          </Button>
        </Card>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
