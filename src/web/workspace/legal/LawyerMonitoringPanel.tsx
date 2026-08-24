/**
 * Sprint Lawyer 3.3/3.4 — Monitoring / Change Center / Manual Import / Sources.
 */

import { useEffect, useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { legalOpsGet, legalOpsPost, pick } from "../business-ops/opsApi";

type Tab = "cases" | "decisions" | "enforcement" | "counterparties" | "changes" | "sources";

const OBJECT_TYPES = [
  { value: "court_case", label: "Судебное дело" },
  { value: "enforcement", label: "Исполнительное производство" },
  { value: "decision", label: "Судебное решение" },
  { value: "counterparty", label: "Контрагент" },
  { value: "other", label: "Другое" },
];

const FREQ = [
  { value: "1h", label: "Каждый час" },
  { value: "6h", label: "Каждые 6 ч" },
  { value: "12h", label: "Каждые 12 ч" },
  { value: "24h", label: "Ежедневно" },
];

const WORKFLOW_RU: Record<string, string> = {
  new: "Новое",
  viewed: "Просмотрено",
  needs_action: "Требует действия",
  closed: "Закрыто",
};

const ICON: Record<string, string> = {
  green: "🟢",
  yellow: "🟡",
  red: "🔴",
  gray: "⚪",
};

export function LawyerMonitoringPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  cases: Record<string, unknown>[];
  clients: Record<string, unknown>[];
  onRefresh: () => void;
  onHandoffAi?: (ctx: { changeId: string; caseId?: string; clientId?: string; contextLabels?: string[] }) => void;
}) {
  const [tab, setTab] = useState<Tab>("cases");
  const [providers, setProviders] = useState<Record<string, unknown>[]>([]);
  const [watchlist, setWatchlist] = useState<Record<string, unknown>[]>([]);
  const [changes, setChanges] = useState<Record<string, unknown>[]>([]);
  const [enforcement, setEnforcement] = useState<Record<string, unknown>[]>([]);
  const [msg, setMsg] = useState("");
  const [checkResult, setCheckResult] = useState<Record<string, unknown> | null>(null);
  const [selectedChange, setSelectedChange] = useState<Record<string, unknown> | null>(null);
  const [watchForm, setWatchForm] = useState({
    entity_kind: "court_case",
    title: "",
    identifier: "",
    source_url: "",
    check_frequency: "12h",
    comment: "",
    counterparty: "",
    decision_ref: "",
    case_id: "",
    active: true,
  });
  const [importJson, setImportJson] = useState(
    '{"status":"open","events":[{"title":"Заседание","starts_at":"2026-08-21T11:30:00+00:00","kind":"hearing"}],"documents":[{"title":"Решение","external_id":"dec-1","url":"https://example.invalid/doc"}]}',
  );
  const [enfForm, setEnfForm] = useState({
    production_number: "",
    debtor: "",
    creditor: "",
    executor: "",
    case_id: "",
    client_id: "",
    notes: "",
  });

  async function reload() {
    const [p, w, c, e] = await Promise.all([
      legalOpsGet("/providers", props.headers),
      legalOpsGet("/monitoring/watchlist", props.headers),
      legalOpsGet("/monitoring/changes", props.headers),
      legalOpsGet("/monitoring/enforcement", props.headers),
    ]);
    setProviders((((p.json as { items?: Record<string, unknown>[] })?.items) || []) as Record<string, unknown>[]);
    setWatchlist((((w.json as { items?: Record<string, unknown>[] })?.items) || []) as Record<string, unknown>[]);
    setChanges((((c.json as { items?: Record<string, unknown>[] })?.items) || []) as Record<string, unknown>[]);
    setEnforcement((((e.json as { items?: Record<string, unknown>[] })?.items) || []) as Record<string, unknown>[]);
  }

  useEffect(() => {
    void reload();
  }, [props.headers]);

  const tabs: { id: Tab; label: string }[] = [
    { id: "cases", label: "Судебные дела" },
    { id: "decisions", label: "Судебные решения" },
    { id: "enforcement", label: "Исполнительные производства" },
    { id: "counterparties", label: "Контрагенты" },
    { id: "changes", label: "Изменения" },
    { id: "sources", label: "Источники данных" },
  ];

  const todayChanges = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return changes.filter((c) => String(pick(c, "created_at")).startsWith(today));
  }, [changes]);

  async function saveWatch() {
    const res = await legalOpsPost(
      "/monitoring/watchlist",
      {
        entity_kind: watchForm.entity_kind,
        title: watchForm.title,
        identifier: watchForm.identifier,
        external_case_number: watchForm.identifier,
        source_url: watchForm.source_url || undefined,
        check_frequency: watchForm.check_frequency,
        comment: watchForm.comment,
        counterparty: watchForm.counterparty || undefined,
        decision_ref: watchForm.decision_ref || undefined,
        case_id: watchForm.case_id || undefined,
        active: watchForm.active,
        provider: "manual_import",
      },
      props.headers,
    );
    const r = res.json as { ok?: boolean; message_ru?: string };
    setMsg(res.ok || r?.ok ? "Сохранено" : r?.message_ru || "Ошибка");
    await reload();
    props.onRefresh();
  }

  async function checkNow(watchId: string, withImport: boolean) {
    let imported: Record<string, unknown> | undefined;
    if (withImport) {
      try {
        imported = JSON.parse(importJson);
      } catch {
        setMsg("Некорректный JSON импорта");
        return;
      }
    }
    const res = await legalOpsPost(
      `/monitoring/watchlist/${watchId}/check`,
      imported ? { imported_state: imported } : {},
      props.headers,
    );
    const r = res.json as { ok?: boolean; message_ru?: string };
    setCheckResult(res.json as Record<string, unknown>);
    setMsg(r?.message_ru || "Проверено");
    await reload();
    props.onRefresh();
  }

  async function changeAction(changeId: string, action: string, extra: Record<string, unknown> = {}) {
    const needsConfirm = !["mark_read", "open", "set_status"].includes(action);
    const res = await legalOpsPost(
      `/monitoring/changes/${changeId}/actions`,
      { action, confirm: needsConfirm ? true : undefined, ...extra },
      props.headers,
    );
    const r = res.json as { ok?: boolean; message_ru?: string; related?: Record<string, unknown> };
    setMsg(res.ok || r?.ok ? "Действие выполнено" : r?.message_ru || "Ошибка");
    if (r?.related) setSelectedChange((prev) => ({ ...(prev || {}), related: r.related }));
    await reload();
    props.onRefresh();
  }

  return (
    <div className="grid gap-3" data-testid="lawyer-monitoring-panel">
      <div className="flex flex-wrap gap-2" data-testid="lawyer-monitoring-tabs">
        {tabs.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}

      {tab === "sources" ? (
        <Card title="Источники данных">
          <p className="eds-type-small mb-2 text-[var(--ew-muted)]">
            Статусы честные. Государственные реестры не имитируются.
          </p>
          <div className="grid gap-2" data-testid="lawyer-provider-statuses">
            {providers.map((p) => (
              <div key={pick(p, "provider")} className="rounded-md border border-[var(--ew-border)] p-3">
                <div className="font-medium">{pick(p, "label_ru", "provider")}</div>
                <div className="eds-type-small">Статус: {pick(p, "status")}</div>
                <div className="eds-type-small">{pick(p, "message_ru") || pick(p, "ui_hint_ru")}</div>
                <div className="eds-type-small text-[var(--ew-muted)]">Источник: {pick(p, "official_source")}</div>
              </div>
            ))}
          </div>
        </Card>
      ) : null}

      {tab === "cases" ? (
        <Card title="Ручной мониторинг">
          <p className="eds-type-small mb-2 text-[var(--ew-muted)]">
            Ссылка источника сохраняется для справки. Сервер не загружает произвольные сайты.
          </p>
          <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-watch-form">
            <label className="eds-type-small">
              Тип объекта
              <select
                className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
                value={watchForm.entity_kind}
                onChange={(e) => setWatchForm((f) => ({ ...f, entity_kind: e.target.value }))}
              >
                {OBJECT_TYPES.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="eds-type-small">
              Название
              <Input
                className="mt-1"
                value={watchForm.title}
                onChange={(e) => setWatchForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="Дело / объект"
              />
            </label>
            <label className="eds-type-small">
              Идентификатор
              <Input
                className="mt-1"
                value={watchForm.identifier}
                onChange={(e) => setWatchForm((f) => ({ ...f, identifier: e.target.value }))}
                placeholder="Номер дела / производства"
              />
            </label>
            <label className="eds-type-small">
              URL источника
              <Input
                className="mt-1"
                value={watchForm.source_url}
                onChange={(e) => setWatchForm((f) => ({ ...f, source_url: e.target.value }))}
                placeholder="https://…"
              />
            </label>
            <label className="eds-type-small">
              Частота проверки
              <select
                className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
                value={watchForm.check_frequency}
                onChange={(e) => setWatchForm((f) => ({ ...f, check_frequency: e.target.value }))}
              >
                {FREQ.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="eds-type-small">
              Контрагент
              <Input
                className="mt-1"
                value={watchForm.counterparty}
                onChange={(e) => setWatchForm((f) => ({ ...f, counterparty: e.target.value }))}
              />
            </label>
            <label className="eds-type-small">
              Судебное решение (ссылка / номер)
              <Input
                className="mt-1"
                value={watchForm.decision_ref}
                onChange={(e) => setWatchForm((f) => ({ ...f, decision_ref: e.target.value }))}
              />
            </label>
            <label className="eds-type-small">
              Дело Legal CRM
              <select
                className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
                value={watchForm.case_id}
                onChange={(e) => setWatchForm((f) => ({ ...f, case_id: e.target.value }))}
              >
                <option value="">—</option>
                {props.cases.map((c) => (
                  <option key={pick(c, "id")} value={pick(c, "id")}>
                    {pick(c, "title", "case_number")}
                  </option>
                ))}
              </select>
            </label>
            <label className="eds-type-small sm:col-span-2">
              Комментарий
              <Input
                className="mt-1"
                value={watchForm.comment}
                onChange={(e) => setWatchForm((f) => ({ ...f, comment: e.target.value }))}
              />
            </label>
            <label className="eds-type-small flex items-center gap-2">
              <input
                type="checkbox"
                checked={watchForm.active}
                onChange={(e) => setWatchForm((f) => ({ ...f, active: e.target.checked }))}
              />
              Активен
            </label>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" disabled={!props.canOperate} data-testid="lawyer-watchlist-save" onClick={() => void saveWatch()}>
              Сохранить
            </Button>
          </div>

          <div className="mt-4 grid gap-2">
            {watchlist.map((w) => (
              <div key={pick(w, "id")} className="rounded-md border border-[var(--ew-border)] p-3">
                <div className="font-medium">
                  {pick(w, "title") || pick(w, "external_case_number")}{" "}
                  <span className="eds-type-small text-[var(--ew-muted)]">({pick(w, "entity_kind")})</span>
                </div>
                <div className="eds-type-small">
                  Идентификатор: {pick(w, "external_case_number")} · Источник:{" "}
                  {pick(w, "provider") === "manual_import" ? "Ручной импорт" : pick(w, "provider")} · Частота:{" "}
                  {pick(w, "check_frequency") || "12h"}
                </div>
                <div className="eds-type-small">
                  URL: {pick(w, "source_url") || "—"} · Проверка: {pick(w, "last_checked_at") || "—"}
                </div>
                <div className="eds-type-small">
                  Статус: {pick(w, "status")} · Активен: {pick(w, "active") !== "false" ? "да" : "нет"}
                </div>
                {pick(w, "last_error") ? <div className="eds-type-small text-[var(--ew-danger)]">{pick(w, "last_error")}</div> : null}
                <label className="eds-type-small mt-2 block">
                  Импорт состояния (JSON) — опционально для проверки diff
                  <textarea
                    className="mt-1 min-h-[60px] w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 font-mono text-xs"
                    value={importJson}
                    onChange={(e) => setImportJson(e.target.value)}
                  />
                </label>
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    data-testid="lawyer-watchlist-check"
                    disabled={!props.canOperate}
                    onClick={() => void checkNow(pick(w, "id"), true)}
                  >
                    Проверить сейчас
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!props.canOperate}
                    onClick={() => void checkNow(pick(w, "id"), false)}
                  >
                    Проверить по сохранённым данным
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!props.canOperate}
                    onClick={async () => {
                      const title = window.prompt("Название", pick(w, "title") || "");
                      if (title == null) return;
                      await legalOpsPost(
                        `/monitoring/watchlist/${pick(w, "id")}`,
                        { title, comment: pick(w, "comment") },
                        props.headers,
                      );
                      setMsg("Объект обновлён");
                      await reload();
                    }}
                  >
                    Изменить
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!props.canOperate}
                    onClick={async () => {
                      const active = !(pick(w, "active") === "true" || pick(w, "status") === "active");
                      await legalOpsPost(`/monitoring/watchlist/${pick(w, "id")}`, { active }, props.headers);
                      setMsg(active ? "Мониторинг возобновлён" : "Мониторинг приостановлен");
                      await reload();
                    }}
                  >
                    {pick(w, "status") === "disabled" || pick(w, "active") === "false"
                      ? "Возобновить"
                      : "Приостановить"}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={!props.canOperate}
                    onClick={async () => {
                      if (!window.confirm("Удалить объект мониторинга? Запись будет отключена.")) return;
                      await legalOpsPost(`/monitoring/watchlist/${pick(w, "id")}`, { active: false }, props.headers);
                      setMsg("Объект отключён");
                      await reload();
                    }}
                  >
                    Удалить
                  </Button>
                </div>
              </div>
            ))}
          </div>
          {checkResult ? (
            <pre className="eds-type-small mt-3 max-h-48 overflow-auto whitespace-pre-wrap rounded-md border border-[var(--ew-border)] p-2">
              {JSON.stringify(checkResult, null, 2)}
            </pre>
          ) : null}
        </Card>
      ) : null}

      {tab === "decisions" ? (
        <Card title="Судебные решения">
          <p className="eds-type-small">
            Автоматический поиск в ЄДРСР недоступен. Сохраняйте reference и ссылку официального источника через ручной
            мониторинг, затем передавайте в AI-анализ (Lawyer 3.2). AI-текст не является официальным судебным документом.
          </p>
          <div className="mt-2 eds-type-small" data-testid="lawyer-decisions-provider">
            {providers
              .filter((p) => pick(p, "provider") === "ua_edrsr")
              .map((p) => (
                <div key="edrsr">
                  Статус: {pick(p, "status")} — {pick(p, "message_ru")}
                </div>
              ))}
          </div>
        </Card>
      ) : null}

      {tab === "enforcement" ? (
        <Card title="Исполнительные производства">
          <p className="eds-type-small mb-2">
            Ручной учёт. Автоматический источник: требуется настройка.
          </p>
          <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-enforcement-form">
            <Input
              placeholder="Номер производства"
              value={enfForm.production_number}
              onChange={(e) => setEnfForm((f) => ({ ...f, production_number: e.target.value }))}
            />
            <Input placeholder="Должник" value={enfForm.debtor} onChange={(e) => setEnfForm((f) => ({ ...f, debtor: e.target.value }))} />
            <Input
              placeholder="Взыскатель"
              value={enfForm.creditor}
              onChange={(e) => setEnfForm((f) => ({ ...f, creditor: e.target.value }))}
            />
            <Input
              placeholder="Исполнитель"
              value={enfForm.executor}
              onChange={(e) => setEnfForm((f) => ({ ...f, executor: e.target.value }))}
            />
          </div>
          <Button
            className="mt-2"
            size="sm"
            disabled={!props.canOperate}
            onClick={async () => {
              const res = await legalOpsPost("/monitoring/enforcement", enfForm, props.headers);
              const r = res.json as { ok?: boolean; message_ru?: string };
              setMsg(res.ok || r?.ok ? "ИП создано" : r?.message_ru || "Ошибка");
              await reload();
            }}
          >
            Создать ИП
          </Button>
                  <ul className="mt-3 eds-type-small">
            {enforcement.map((e) => (
              <li key={pick(e, "id")} className="mb-2 flex flex-wrap items-center gap-2">
                <span>
                  {pick(e, "production_number")} — {pick(e, "status")} — {pick(e, "debtor")}
                </span>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!props.canOperate}
                  onClick={async () => {
                    const status = window.prompt("Статус", pick(e, "status") || "open");
                    if (status == null) return;
                    await legalOpsPost(`/monitoring/enforcement/${pick(e, "id")}`, { status }, props.headers);
                    setMsg("ИП обновлено");
                    await reload();
                  }}
                >
                  Изменить
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!props.canOperate}
                  onClick={async () => {
                    if (!window.confirm("Удалить объект? ИП будет отправлено в архив.")) return;
                    await legalOpsPost(`/entities/enforcement/${pick(e, "id")}/archive`, {}, props.headers);
                    setMsg("ИП в архиве");
                    await reload();
                  }}
                >
                  Удалить
                </Button>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "counterparties" ? (
        <Card title="Контрагенты">
          <p className="eds-type-small">
            Используйте картотеку Клиенты. Внешняя проверка контрагентов не подключена.
          </p>
          <p className="eds-type-small text-[var(--ew-muted)]">
            Источник не подключен. Для автоматического обновления требуется официальный или лицензированный источник
            данных.
          </p>
          <ul className="mt-2 eds-type-small">
            {props.clients.slice(0, 20).map((c) => (
              <li key={pick(c, "id")}>{pick(c, "name")}</li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "changes" ? (
        <Card title="Центр изменений">
          <div className="mb-2 font-medium">СЕГОДНЯ</div>
          <div className="grid gap-2" data-testid="lawyer-change-center">
            {(todayChanges.length ? todayChanges : changes).map((c) => {
              const wf = pick(c, "workflow_status") || (pick(c, "read_at") ? "viewed" : "new");
              return (
                <div
                  key={pick(c, "id")}
                  className="cursor-pointer rounded-md border border-[var(--ew-border)] p-3"
                  onClick={() => setSelectedChange(c)}
                  data-testid="lawyer-change-row"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded bg-[var(--ew-surface-2,transparent)] px-2 py-0.5 eds-type-small">
                      {WORKFLOW_RU[wf] || wf}
                    </span>
                    <span className="eds-type-small text-[var(--ew-muted)]">{pick(c, "created_at")}</span>
                  </div>
                  <div className="font-medium">{pick(c, "title")}</div>
                  <div className="eds-type-small">
                    Объект: {pick(c, "payload") ? String((c.payload as { watch_title?: string })?.watch_title || "—") : "—"} ·
                    Тип: {pick(c, "change_type")} · Источник: {pick(c, "source_label") || pick(c, "provider")}
                  </div>
                  <div className="eds-type-small">{pick(c, "summary")}</div>
                </div>
              );
            })}
            {changes.length === 0 ? <p className="eds-type-small">Пока нет изменений</p> : null}
          </div>

          {selectedChange ? (
            <div className="mt-4 rounded-md border border-[var(--ew-border)] p-3" data-testid="lawyer-change-detail">
              <div className="font-medium">Детали изменения</div>
              <div className="eds-type-small mt-1">
                Что изменилось:{" "}
                {typeof selectedChange.detail === "object"
                  ? pick(selectedChange.detail as Record<string, unknown>, "title") ||
                    pick(selectedChange.detail as Record<string, unknown>, "to") ||
                    pick(selectedChange, "summary")
                  : pick(selectedChange, "summary")}
              </div>
              <div className="eds-type-small">Источник: {pick(selectedChange, "source_label") || pick(selectedChange, "provider")}</div>
              <div className="eds-type-small">Дата: {pick(selectedChange, "created_at")}</div>
              <div className="eds-type-small mt-2 font-medium">Связанные</div>
              <div className="eds-type-small">дело: {pick(selectedChange, "case_id") || "—"}</div>
              <div className="eds-type-small">клиент: {pick(selectedChange, "client_id") || "—"}</div>
              <div className="eds-type-small">
                контрагент: {String((selectedChange.payload as { counterparty?: string } | undefined)?.counterparty || "—")}
              </div>
              <div className="eds-type-small">исполнительное производство: {pick(selectedChange, "enforcement_id") || "—"}</div>
              <div className="mt-3 flex flex-wrap gap-1">
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!props.canOperate}
                  onClick={() => void changeAction(pick(selectedChange, "id"), "create_task")}
                >
                  Создать задачу
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!props.canOperate}
                  onClick={() =>
                    void changeAction(pick(selectedChange, "id"), "add_calendar", {
                      starts_at:
                        (selectedChange.detail as { starts_at?: string } | undefined)?.starts_at ||
                        "2026-08-21T11:30:00+00:00",
                    })
                  }
                >
                  Добавить в календарь
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!props.canOperate}
                  onClick={() => {
                    void changeAction(pick(selectedChange, "id"), "handoff_lawyer");
                    props.onHandoffAi?.({
                      changeId: pick(selectedChange, "id"),
                      caseId: pick(selectedChange, "case_id") || undefined,
                      clientId: pick(selectedChange, "client_id") || undefined,
                      contextLabels: [
                        `Изменение мониторинга: ${pick(selectedChange, "title") || pick(selectedChange, "summary")}`,
                        ...(pick(selectedChange, "case_id") ? [`Дело ${pick(selectedChange, "case_id")}`] : []),
                      ],
                    });
                  }}
                >
                  Передать AI-юристу
                </Button>
                <Button size="sm" variant="ghost" onClick={() => void changeAction(pick(selectedChange, "id"), "mark_read")}>
                  Отметить просмотренным
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => void changeAction(pick(selectedChange, "id"), "set_status", { workflow_status: "closed" })}
                >
                  Закрыть
                </Button>
              </div>
            </div>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}

export function IntegrationHealthCard(props: {
  headers: Record<string, string>;
  onConnectGoogle?: () => void;
  onDisconnectGoogle?: () => void;
}) {
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    void legalOpsGet("/integrations/health", props.headers).then((r) => {
      setHealth((r.json as Record<string, unknown>) || null);
    });
  }, [props.headers]);

  const items = ((health?.items as Record<string, unknown>[]) || []) as Record<string, unknown>[];

  return (
    <Card title="СОСТОЯНИЕ ИНТЕГРАЦИЙ">
      <div className="grid gap-2" data-testid="lawyer-integrations-health">
        {items.map((it) => (
          <div key={pick(it, "id")} className="rounded-md border border-[var(--ew-border)] p-3">
            <div className="font-medium">
              {ICON[pick(it, "icon")] || "⚪"} {pick(it, "label_ru")}
            </div>
            <div className="eds-type-small">
              Статус: {pick(it, "status_label_ru") || pick(it, "status_raw")}
            </div>
            <div className="eds-type-small text-[var(--ew-muted)]">{pick(it, "message_ru")}</div>
            <div className="eds-type-small">
              Последняя успешная синхронизация: {pick(it, "last_success_at") || "—"}
            </div>
            {pick(it, "id") === "google_calendar" ? (
              <div className="mt-2 flex flex-wrap gap-2">
                <Button size="sm" onClick={() => props.onConnectGoogle?.()}>
                  Подключить
                </Button>
                <Button size="sm" variant="ghost" onClick={() => props.onDisconnectGoogle?.()}>
                  Отключить
                </Button>
              </div>
            ) : null}
          </div>
        ))}
        {!items.length ? <p className="eds-type-small">Загрузка состояния…</p> : null}
        <div className="eds-type-small mt-2">
          Ошибки за 24 часа: {String(health?.errors_24h_count ?? "—")}
        </div>
      </div>
    </Card>
  );
}
