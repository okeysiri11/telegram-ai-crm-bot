/**
 * AGRO 2.1 Deal 360 — workflow, payments, documents. Same backend as desktop.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost } from "../business-ops/opsApi";
import { DEAL_STATUSES, ru } from "./agroLabels";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Основное" },
  { id: "payments", label: "Платежи" },
  { id: "contracts", label: "Договор" },
  { id: "documents", label: "Документы" },
  { id: "shipments", label: "Логистика" },
  { id: "lots", label: "Склад" },
  { id: "tasks", label: "Задачи" },
  { id: "activity", label: "История" },
] as const;

function titleOf(r: Row): string {
  return String(r.title || r.name || r.filename || r.summary || r.id || "—");
}

export function AgroDeal360(props: {
  itemId: string;
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  canOperate: boolean;
  onBack: () => void;
  onQuick: (kind: string) => void;
  onChanged: () => void;
}) {
  const [tab, setTab] = useState("overview");
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pay, setPay] = useState({ amount: "", currency: "UAH", title: "Оплата" });
  const [comment, setComment] = useState("");
  const [confirmPay, setConfirmPay] = useState(false);
  const [taskTitle, setTaskTitle] = useState("");

  async function reload() {
    const res = await agroOpsGet(`/crm/deal/${props.itemId}?tab=${tab}&limit=20`, props.headers);
    if (!res.ok) {
      setError("Не удалось загрузить сделку");
      return;
    }
    setData(res.json as Row);
    setError(null);
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.itemId, tab, props.headers]);

  const item = (data?.item || {}) as Row;
  const calc = (data?.calculation || {}) as Row;
  const allowed = (item.allowed_statuses as string[]) || [];
  const rows = (data?.items as Row[]) || [];

  async function setStatus(status: string) {
    const res = await agroOpsPost(`/crm/deal/${props.itemId}/status`, { status, comment, source: "USER" }, props.headers);
    const body = res.json as { message_ru?: string };
    if (!res.ok) {
      setError(body.message_ru || "Недопустимый переход статуса");
      return;
    }
    setComment("");
    props.onChanged();
    await reload();
  }

  async function addPayment() {
    if (!confirmPay) {
      setConfirmPay(true);
      return;
    }
    await agroOpsPost(
      "/entities/payment",
      {
        title: pay.title,
        amount: pay.amount,
        currency: pay.currency,
        deal_id: props.itemId,
        counterparty_id: item.counterparty_id,
        direction: item.side === "sell" ? "in" : "out",
        status: "paid",
      },
      props.headers,
    );
    setConfirmPay(false);
    setPay({ amount: "", currency: pay.currency, title: "Оплата" });
    props.onChanged();
    await reload();
  }

  async function addComment() {
    await agroOpsPost("/crm/note", { text: comment, title: comment.slice(0, 80), deal_id: props.itemId, counterparty_id: item.counterparty_id }, props.headers);
    setComment("");
    await reload();
  }

  async function addTask() {
    const title = taskTitle.trim();
    if (!title) return;
    await agroOpsPost(
      "/entities/task",
      { title, deal_id: props.itemId, counterparty_id: item.counterparty_id, status: "open" },
      props.headers,
    );
    setTaskTitle("");
    setTab("tasks");
    props.onChanged();
    await reload();
  }

  return (
    <div className="space-y-3" data-testid="agro-deal-360">
      <header className="sticky top-0 z-10 bg-[var(--eds-surface)] py-1">
        <Button size="sm" variant="ghost" className="min-h-11 min-w-11" onClick={props.onBack} aria-label="Назад" data-testid="agro-deal-back">
          ←
        </Button>
        <h3 className="font-semibold">
          {Boolean(item.is_demo) ? "[DEMO] " : ""}
          Сделка {String(item.number || item.id || "")} · {item.side === "sell" ? "Продажа" : "Покупка"}
        </h3>
        <p className="eds-type-small text-[var(--ew-muted)]">
          {ru(DEAL_STATUSES, String(item.status || ""))} · {String(item.counterparty_id || "—")} · {item.amount != null ? `${item.amount} ${String(item.currency || "")}` : "Нет данных"}
        </p>
      </header>
      <div className="flex flex-wrap gap-2">
        {props.canOperate ? (
          <>
            <Button size="sm" className="min-h-11" onClick={() => props.onQuick("payment")}>
              Платёж
            </Button>
            <Button size="sm" className="min-h-11" variant="secondary" onClick={() => props.onQuick("documents")}>
              Документ
            </Button>
            <Button size="sm" className="min-h-11" variant="secondary" onClick={() => props.onQuick("shipment")}>
              Поставка
            </Button>
            <Button
              size="sm"
              className="min-h-11"
              variant="secondary"
              data-testid="agro-deal-add-task"
              onClick={() => {
                setTab("tasks");
                props.onQuick("task");
              }}
            >
              Задача
            </Button>
          </>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-1" data-testid="agro-deal-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}
      {tab === "overview" ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <Card title="Товар">
            <p className="eds-type-small">Культура: {String(item.crop || item.product || "Нет данных")}</p>
            <p className="eds-type-small">Класс: {String(item.quality_class || item.grade || "Нет данных")}</p>
            <p className="eds-type-small">
              Количество: {item.quantity != null ? `${item.quantity} ${String(item.unit || "")}` : "Нет данных"}
            </p>
            <p className="eds-type-small">Цена: {item.price != null ? `${item.price} ${String(item.currency || "")}` : "Нет данных"}</p>
            <p className="eds-type-small">Сумма: {item.line_total != null ? String(item.line_total) : "Нет данных"}</p>
          </Card>
          <Card title="Расчёт">
            <p className="eds-type-small">Выручка: {calc.revenue != null ? String(calc.revenue) : "Нет данных"}</p>
            <p className="eds-type-small">Себестоимость: {calc.cost_missing ? "нет данных" : String(calc.cost_basis ?? "Нет данных")}</p>
            <p className="eds-type-small">Маржа: {calc.margin_pct != null ? `${calc.margin_pct}%` : "не рассчитана"}</p>
            {calc.margin_ru ? <p className="eds-type-small">{String(calc.margin_ru)}</p> : null}
            <p className="eds-type-small">
              Оплачено: {item.paid != null ? String(item.paid) : "Нет данных"} · Остаток: {item.remaining != null ? String(item.remaining) : "Нет данных"} · {item.paid_pct != null ? `${item.paid_pct}%` : ""}
            </p>
          </Card>
          <Card title="Статус">
            <Input placeholder="Комментарий к смене статуса" value={comment} onChange={(e) => setComment(e.target.value)} />
            <div className="mt-2 flex flex-wrap gap-1">
              {allowed.map((s) => (
                <Button key={s} size="sm" variant="secondary" onClick={() => void setStatus(s)}>
                  {ru(DEAL_STATUSES, s)}
                </Button>
              ))}
              {allowed.length === 0 ? <p className="eds-type-small">Дальнейшие переходы недоступны</p> : null}
            </div>
          </Card>
          <Card title="Чеклист документов">
            {Array.isArray(data?.checklist) && (data?.checklist as Row[]).length ? (
              (data?.checklist as Row[]).map((c, i) => (
                <p key={i} className="eds-type-small">
                  {String(c.doc_type)} · {String(c.status || "missing")}
                </p>
              ))
            ) : (
              <p className="eds-type-small">Нет данных</p>
            )}
          </Card>
        </div>
      ) : (
        <Card title={TABS.find((t) => t.id === tab)?.label || tab}>
          {tab === "payments" && props.canFinance ? (
            <div className="mb-3 grid gap-2 sm:grid-cols-3">
              <Input placeholder="Сумма" value={pay.amount} onChange={(e) => setPay((f) => ({ ...f, amount: e.target.value }))} />
              <Input placeholder="Валюта" value={pay.currency} onChange={(e) => setPay((f) => ({ ...f, currency: e.target.value }))} />
              <Button size="sm" onClick={() => void addPayment()}>
                {confirmPay ? "Подтвердить платёж" : "Добавить платёж"}
              </Button>
            </div>
          ) : null}
          {tab === "tasks" && props.canOperate ? (
            <div className="mb-3 flex flex-wrap gap-2">
              <Input placeholder="Название задачи" value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} />
              <Button size="sm" className="min-h-11" onClick={() => void addTask()} data-testid="agro-deal-task-save">
                Добавить задачу
              </Button>
            </div>
          ) : null}
          {tab === "activity" ? (
            <div className="mb-3 flex gap-2">
              <Input placeholder="Комментарий" value={comment} onChange={(e) => setComment(e.target.value)} />
              <Button size="sm" className="min-h-11" onClick={() => void addComment()}>
                Добавить
              </Button>
            </div>
          ) : null}
          {rows.length === 0 ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
          <ul>
            {rows.map((r) => (
              <li key={String(r.id)} className="border-b border-[var(--ew-border)] py-2 eds-type-small">
                {titleOf(r)} {r.amount != null ? `· ${r.amount} ${String(r.currency || "")}` : ""} {r.status ? `· ${String(r.status)}` : ""}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
