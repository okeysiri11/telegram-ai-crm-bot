/**
 * Visual Lawyer calendar — month / week / day / agenda (Sprint 51.1 / 3.5).
 */

import { useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { EVENT_TYPES, ruStatus } from "./lawyerLabels";
import { pick } from "../business-ops/opsApi";

type Ev = Record<string, unknown>;

function startOfDay(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function addDays(d: Date, n: number) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

function sameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function parseAt(raw: unknown): Date | null {
  if (!raw) return null;
  const d = new Date(String(raw));
  return Number.isNaN(d.getTime()) ? null : d;
}

function originBadge(e: Ev): string {
  if (e.gcal_event_id || e.external_provider === "google") return "Google";
  if (e.source_kind === "court_monitor" || (e.payload as { origin?: string } | undefined)?.origin === "court") {
    return "Суд";
  }
  if (pick(e, "event_type") === "deadline") return "Срок";
  if (pick(e, "event_type") === "contract_end") return "Договор";
  return "ADOS";
}

function syncLabel(e: Ev): string {
  const st = pick(e, "sync_status");
  if (st === "synced" || e.gcal_event_id) return "Синхронизировано";
  if (st === "error") return "Синхронизация не выполнена";
  if (st === "pending") return "Ожидает синхронизации";
  return "Локально (без Google)";
}

const FILTERS = [
  { id: "all", label: "Все" },
  { id: "hearing", label: "Заседания" },
  { id: "meeting", label: "Встречи" },
  { id: "deadline", label: "Сроки" },
  { id: "task", label: "Задачи" },
  { id: "contract_end", label: "Договоры" },
];

export function LawyerCalendarBoard({
  events,
  canCreate,
  clients,
  cases,
  onCreate,
  onOpen,
  onEdit,
  onArchive,
  onSyncGoogle,
  onOpenRelated,
}: {
  events: Ev[];
  canCreate: boolean;
  clients?: Ev[];
  cases?: Ev[];
  onCreate: (isoDate: string) => void;
  onOpen: (ev: Ev) => void;
  onEdit: (ev: Ev) => void;
  onArchive: (ev: Ev) => void;
  onSyncGoogle?: (ev: Ev) => void;
  onOpenRelated?: (kind: "client" | "case", id: string) => void;
}) {
  const [cursor, setCursor] = useState(() => startOfDay(new Date()));
  const [view, setView] = useState<"month" | "week" | "day" | "agenda">("month");
  const [filter, setFilter] = useState(() => {
    try {
      return localStorage.getItem("lawyer_cal_filter_v1") || "all";
    } catch {
      return "all";
    }
  });
  const [responsible, setResponsible] = useState("");
  const [selected, setSelected] = useState<Ev | null>(null);

  const filtered = useMemo(() => {
    return events.filter((e) => {
      const t = String(e.event_type || "other");
      if (filter === "meeting" && t !== "meeting" && t !== "consultation" && t !== "internal") return false;
      if (filter !== "all" && filter !== "meeting" && t !== filter) return false;
      if (responsible && String(e.responsible_user_id || "") !== responsible) return false;
      return true;
    });
  }, [events, filter, responsible]);

  const responsibles = useMemo(
    () => [...new Set(events.map((e) => String(e.responsible_user_id || "")).filter(Boolean))],
    [events],
  );

  function setFilterPersist(id: string) {
    setFilter(id);
    try {
      localStorage.setItem("lawyer_cal_filter_v1", id);
    } catch {
      /* ignore */
    }
  }

  const monthGrid = useMemo(() => {
    const first = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
    const start = addDays(first, -((first.getDay() + 6) % 7));
    return Array.from({ length: 42 }, (_, i) => addDays(start, i));
  }, [cursor]);

  const weekDays = useMemo(() => {
    const start = addDays(cursor, -((cursor.getDay() + 6) % 7));
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [cursor]);

  function eventsOn(day: Date) {
    return filtered.filter((e) => {
      const d = parseAt(e.starts_at);
      return d ? sameDay(d, day) : false;
    });
  }

  function openDetail(e: Ev) {
    setSelected(e);
    onOpen(e);
  }

  const clientName = (id?: string) => {
    if (!id) return "—";
    const c = (clients || []).find((x) => pick(x, "id") === id);
    return c ? pick(c, "name") : id;
  };
  const caseName = (id?: string) => {
    if (!id) return "—";
    const c = (cases || []).find((x) => pick(x, "id") === id);
    return c ? pick(c, "title", "case_number") : id;
  };

  const title =
    view === "month"
      ? cursor.toLocaleDateString("ru-RU", { month: "long", year: "numeric" })
      : cursor.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });

  return (
    <Card title="Календарь юриста">
      <div className="mb-3 flex flex-wrap items-center gap-2" data-testid="lawyer-calendar-toolbar">
        <Button size="sm" variant="secondary" onClick={() => setCursor(startOfDay(new Date()))}>
          Сегодня
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setCursor(addDays(cursor, view === "month" ? -30 : view === "week" ? -7 : -1))}
        >
          ←
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => setCursor(addDays(cursor, view === "month" ? 30 : view === "week" ? 7 : 1))}
        >
          →
        </Button>
        <Input
          type="month"
          className="max-w-[10rem]"
          value={`${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, "0")}`}
          onChange={(e) => {
            const [y, m] = e.target.value.split("-").map(Number);
            if (y && m) setCursor(new Date(y, m - 1, 1));
          }}
        />
        <span className="eds-type-body capitalize">{title}</span>
        {(["month", "week", "day", "agenda"] as const).map((v) => (
          <Button key={v} size="sm" variant={view === v ? "primary" : "ghost"} onClick={() => setView(v)}>
            {v === "month" ? "Месяц" : v === "week" ? "Неделя" : v === "day" ? "День" : "Повестка"}
          </Button>
        ))}
      </div>
      <div className="mb-3 flex flex-wrap gap-2" data-testid="lawyer-calendar-filters">
        {FILTERS.map((f) => (
          <Button key={f.id} size="sm" variant={filter === f.id ? "secondary" : "ghost"} onClick={() => setFilterPersist(f.id)}>
            {f.label}
          </Button>
        ))}
        {responsibles.length ? (
          <select
            className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small"
            value={responsible}
            onChange={(e) => setResponsible(e.target.value)}
          >
            <option value="">Все ответственные</option>
            {responsibles.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        ) : null}
      </div>

      {view === "month" ? (
        <div className="grid grid-cols-7 gap-1" data-testid="lawyer-calendar-month">
          {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => (
            <div key={d} className="eds-type-small px-1 text-[var(--eds-text-muted)]">
              {d}
            </div>
          ))}
          {monthGrid.map((day) => {
            const list = eventsOn(day);
            const iso = day.toISOString();
            return (
              <div
                key={iso}
                className="min-h-[5.5rem] rounded-md border border-[var(--ew-border)] p-1 text-left hover:bg-[var(--eds-primary-soft)]"
              >
                <button
                  type="button"
                  className="eds-type-small w-full text-left"
                  onClick={() => canCreate && onCreate(iso)}
                >
                  {day.getDate()}
                  {canCreate ? <span className="ml-1 text-[var(--eds-text-muted)]">+ Создать событие</span> : null}
                </button>
                {list.slice(0, 3).map((e) => (
                  <button
                    type="button"
                    key={pick(e, "id")}
                    className="block w-full truncate text-left eds-type-small"
                    onClick={() => openDetail(e)}
                  >
                    {ruStatus(pick(e, "event_type"))}: {pick(e, "title")}
                    <span className="ml-1 text-[10px] text-[var(--ew-muted)]">{originBadge(e)}</span>
                  </button>
                ))}
              </div>
            );
          })}
        </div>
      ) : null}

      {view === "week" || view === "day" ? (
        <div className="space-y-2" data-testid={`lawyer-calendar-${view}`}>
          {(view === "day" ? [cursor] : weekDays).map((day) => (
            <div key={day.toISOString()} className="rounded-md border border-[var(--ew-border)] p-2">
              <div className="mb-1 flex items-center justify-between">
                <strong className="eds-type-small">
                  {day.toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "short" })}
                </strong>
                {canCreate ? (
                  <Button size="sm" variant="ghost" onClick={() => onCreate(day.toISOString())}>
                    + Создать событие
                  </Button>
                ) : null}
              </div>
              {eventsOn(day).length === 0 ? (
                <p className="eds-type-small text-[var(--eds-text-muted)]">Нет событий</p>
              ) : (
                eventsOn(day).map((e) => (
                  <div key={pick(e, "id")} className="flex flex-wrap items-center justify-between gap-2 py-1">
                    <button type="button" className="text-left" onClick={() => openDetail(e)}>
                      {pick(e, "starts_at").slice(11, 16)} · {pick(e, "title")} · {ruStatus(pick(e, "event_type"))}
                    </button>
                    <span className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => onEdit(e)}>
                        Изменить
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => onArchive(e)}>
                        Удалить
                      </Button>
                    </span>
                  </div>
                ))
              )}
            </div>
          ))}
        </div>
      ) : null}

      {view === "agenda" ? (
        <div data-testid="lawyer-calendar-agenda">
          {filtered.length === 0 ? (
            <p className="eds-type-small">Пока нет событий</p>
          ) : (
            filtered.map((e) => (
              <div key={pick(e, "id")} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--ew-border)] py-2">
                <button type="button" className="text-left" onClick={() => openDetail(e)}>
                  {pick(e, "starts_at")} · {pick(e, "title")} · {ruStatus(pick(e, "event_type"))}
                </button>
                <span className="flex gap-1">
                  <Button size="sm" variant="ghost" onClick={() => onEdit(e)}>
                    Изменить
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onArchive(e)}>
                    Удалить
                  </Button>
                </span>
              </div>
            ))
          )}
        </div>
      ) : null}

      {selected ? (
        <div className="mt-4 rounded-md border border-[var(--ew-border)] p-3" data-testid="lawyer-calendar-event-detail">
          <div className="font-medium">Карточка события</div>
          <div className="eds-type-small mt-2 grid gap-1 sm:grid-cols-2">
            <div>Название: {pick(selected, "title")}</div>
            <div>Тип: {ruStatus(pick(selected, "event_type"))}</div>
            <div>Дата: {pick(selected, "starts_at").slice(0, 10)}</div>
            <div>Время: {pick(selected, "starts_at").slice(11, 16) || "—"}</div>
            <div>Клиент: {clientName(pick(selected, "client_id"))}</div>
            <div>Дело: {caseName(pick(selected, "case_id"))}</div>
            <div>Ответственный: {pick(selected, "responsible_user_id") || "—"}</div>
            <div>Источник: {originBadge(selected)}</div>
            <div className="sm:col-span-2">Описание: {pick(selected, "description") || "—"}</div>
            <div className="sm:col-span-2">Google: {syncLabel(selected)}</div>
          </div>
          <div className="mt-3 flex flex-wrap gap-1">
            <Button size="sm" onClick={() => onEdit(selected)}>
              Изменить
            </Button>
            <Button size="sm" variant="ghost" onClick={() => onArchive(selected)}>
              Удалить
            </Button>
            {pick(selected, "case_id") ? (
              <Button size="sm" variant="ghost" onClick={() => onOpenRelated?.("case", pick(selected, "case_id"))}>
                Открыть связанное дело
              </Button>
            ) : null}
            {pick(selected, "client_id") ? (
              <Button size="sm" variant="ghost" onClick={() => onOpenRelated?.("client", pick(selected, "client_id"))}>
                Открыть клиента
              </Button>
            ) : null}
            {onSyncGoogle ? (
              <Button size="sm" variant="ghost" onClick={() => onSyncGoogle(selected)}>
                Синхронизировать
              </Button>
            ) : null}
            <Button size="sm" variant="ghost" onClick={() => setSelected(null)}>
              Закрыть
            </Button>
          </div>
        </div>
      ) : null}

      <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
        Типы: {EVENT_TYPES.map((t) => t.label).join(" · ")}
      </p>
    </Card>
  );
}
