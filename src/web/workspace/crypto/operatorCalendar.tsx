/**
 * Sprint 50.3 — month / week / day operator calendar with filters and day drawer.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Button, Card, Input } from "@/ui";

export type CalView = "month" | "week" | "day";

export const CAL_FILTERS: { key: string; label: string }[] = [
  { key: "macro", label: "Макроэкономика" },
  { key: "news", label: "Новости" },
  { key: "analysis", label: "Анализы" },
  { key: "agent", label: "AI-специалисты" },
  { key: "signal", label: "Сигналы" },
  { key: "session", label: "Сессии" },
  { key: "paper", label: "Paper Trading" },
  { key: "manual", label: "Ручные" },
];

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

function parseEventDate(ev: Record<string, unknown>): Date | null {
  const raw = String(ev.scheduled_at || "");
  if (!raw) return null;
  const d = new Date(raw);
  return Number.isNaN(d.getTime()) ? null : d;
}

function monthMatrix(anchor: Date): Date[][] {
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const start = addDays(first, -((first.getDay() + 6) % 7)); // Monday-first
  const weeks: Date[][] = [];
  let cur = start;
  for (let w = 0; w < 6; w++) {
    const row: Date[] = [];
    for (let i = 0; i < 7; i++) {
      row.push(cur);
      cur = addDays(cur, 1);
    }
    weeks.push(row);
  }
  return weeks;
}

function weekDays(anchor: Date): Date[] {
  const dow = (anchor.getDay() + 6) % 7;
  const mon = addDays(startOfDay(anchor), -dow);
  return Array.from({ length: 7 }, (_, i) => addDays(mon, i));
}

export function OperatorCalendarPanel({
  events,
  filters,
  onFiltersChange,
  onCreateManual,
}: {
  events: Record<string, unknown>[];
  filters: Record<string, boolean>;
  onFiltersChange: (next: Record<string, boolean>) => void;
  onCreateManual: (body: Record<string, unknown>) => void;
}) {
  const [view, setView] = useState<CalView>("month");
  const [cursor, setCursor] = useState(() => startOfDay(new Date()));
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [manualOpen, setManualOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [time, setTime] = useState("12:00");
  const [instrument, setInstrument] = useState("EUR/USD");
  const [description, setDescription] = useState("");
  const [reminder, setReminder] = useState(false);

  const byDay = useMemo(() => {
    const map = new Map<string, Record<string, unknown>[]>();
    for (const ev of events) {
      const d = parseEventDate(ev);
      if (!d) continue;
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      const list = map.get(key) || [];
      list.push(ev);
      map.set(key, list);
    }
    return map;
  }, [events]);

  const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
  const dayEvents = selectedDay ? byDay.get(dayKey(selectedDay)) || [] : [];

  const navLabel =
    view === "month"
      ? cursor.toLocaleDateString("ru-RU", { month: "long", year: "numeric" })
      : view === "week"
        ? `Неделя · ${weekDays(cursor)[0].toLocaleDateString("ru-RU")} – ${weekDays(cursor)[6].toLocaleDateString("ru-RU")}`
        : cursor.toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  const shift = (dir: -1 | 1) => {
    if (view === "month") setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + dir, 1));
    else if (view === "week") setCursor(addDays(cursor, dir * 7));
    else setCursor(addDays(cursor, dir));
  };

  return (
    <div className="space-y-3" data-testid="operator-calendar">
      <div className="flex flex-wrap items-center gap-2">
        {(["month", "week", "day"] as CalView[]).map((v) => (
          <Button key={v} size="sm" variant={view === v ? "primary" : "secondary"} onClick={() => setView(v)}>
            {v === "month" ? "Месяц" : v === "week" ? "Неделя" : "День"}
          </Button>
        ))}
        <Button size="sm" variant="secondary" onClick={() => shift(-1)}>
          ←
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setCursor(startOfDay(new Date()))}>
          Сегодня
        </Button>
        <Button size="sm" variant="secondary" onClick={() => shift(1)}>
          →
        </Button>
        <span className="eds-type-small capitalize">{navLabel}</span>
        <Button size="sm" className="ews-primary-cta" onClick={() => setManualOpen(true)}>
          Ручное событие
        </Button>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="calendar-filters">
        {CAL_FILTERS.map((f) => (
          <label key={f.key} className="eds-type-caption flex items-center gap-1">
            <input
              type="checkbox"
              checked={filters[f.key] !== false}
              onChange={(e) => onFiltersChange({ ...filters, [f.key]: e.target.checked })}
            />
            {f.label}
          </label>
        ))}
      </div>

      {view === "month" ? (
        <div className="overflow-x-auto" data-testid="calendar-month">
          <div className="grid grid-cols-7 gap-1 text-center eds-type-caption text-[var(--eds-text-muted)]">
            {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => (
              <div key={d}>{d}</div>
            ))}
          </div>
          {monthMatrix(cursor).map((week, wi) => (
            <div key={wi} className="grid grid-cols-7 gap-1">
              {week.map((d) => {
                const evs = byDay.get(dayKey(d)) || [];
                const inMonth = d.getMonth() === cursor.getMonth();
                return (
                  <button
                    key={dayKey(d)}
                    type="button"
                    className={`min-h-[72px] rounded border border-[var(--eds-border)] p-1 text-left ${inMonth ? "" : "opacity-40"}`}
                    onClick={() => {
                      setSelectedDay(d);
                      setView("day");
                      setCursor(d);
                    }}
                  >
                    <div className="eds-type-small font-medium">{d.getDate()}</div>
                    <div className="eds-type-caption text-[var(--eds-text-muted)]">{evs.length ? `${evs.length} соб.` : ""}</div>
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      ) : null}

      {view === "week" ? (
        <div className="grid gap-2 md:grid-cols-7" data-testid="calendar-week">
          {weekDays(cursor).map((d) => {
            const evs = byDay.get(dayKey(d)) || [];
            return (
              <button
                key={dayKey(d)}
                type="button"
                className="rounded border border-[var(--eds-border)] p-2 text-left"
                onClick={() => {
                  setSelectedDay(d);
                  setView("day");
                  setCursor(d);
                }}
              >
                <div className="eds-type-small font-medium">{d.toLocaleDateString("ru-RU", { weekday: "short", day: "numeric" })}</div>
                {evs.slice(0, 4).map((e) => (
                  <p key={String(e.event_id)} className="eds-type-caption truncate">
                    {String(e.title || "—")}
                  </p>
                ))}
              </button>
            );
          })}
        </div>
      ) : null}

      {view === "day" ? (
        <Card title={`День · ${cursor.toLocaleDateString("ru-RU")}`} data-testid="calendar-day-drawer">
          {(byDay.get(dayKey(cursor)) || []).length === 0 ? (
            <p className="eds-type-small text-[var(--eds-text-muted)]">Нет данных</p>
          ) : (
            (byDay.get(dayKey(cursor)) || []).map((e) => (
              <div key={String(e.event_id)} className="mb-3 border-b border-[var(--eds-border)] pb-2 eds-type-small">
                <p className="font-medium">{String(e.title)}</p>
                <p>
                  Время: {String(e.scheduled_at || "—").slice(11, 16) || "—"} · {String(e.category)} · {String(e.instrument || "—")}
                </p>
                <p>
                  Источник: {String(e.source || "—")} · Статус: {String(e.status || "—")} · Важность: {String(e.importance || "—")}
                </p>
                {e.description ? <p>{String(e.description)}</p> : null}
                <div className="mt-1 flex flex-wrap gap-2">
                  {(e.links as Record<string, string> | undefined)?.analysis ? (
                    <Link className="underline" to={`/workspace/crypto${String((e.links as Record<string, string>).analysis)}`}>
                      Анализ
                    </Link>
                  ) : null}
                  {(e.links as Record<string, string> | undefined)?.signal ? (
                    <Link className="underline" to={`/workspace/crypto${String((e.links as Record<string, string>).signal)}`}>
                      Сигнал
                    </Link>
                  ) : null}
                  {(e.links as Record<string, string> | undefined)?.paper ? (
                    <Link className="underline" to={`/workspace/crypto${String((e.links as Record<string, string>).paper)}`}>
                      Бумажная сделка
                    </Link>
                  ) : (
                    <Link className="underline" to="/workspace/crypto?view=paper">
                      Бумажная сделка
                    </Link>
                  )}
                  {(e.links as Record<string, string> | undefined)?.agent ? (
                    <Link className="underline" to="/workspace/crypto?view=specialists">
                      Агент
                    </Link>
                  ) : null}
                </div>
              </div>
            ))
          )}
        </Card>
      ) : null}

      {selectedDay && view !== "day" ? (
        <Card title={`События · ${selectedDay.toLocaleDateString("ru-RU")}`}>
          {dayEvents.length === 0 ? <p className="eds-type-small">Нет данных</p> : null}
          {dayEvents.map((e) => (
            <p key={String(e.event_id)} className="eds-type-small">
              {String(e.scheduled_at || "").slice(11, 16)} · {String(e.title)} · {String(e.instrument)}
            </p>
          ))}
        </Card>
      ) : null}

      {manualOpen ? (
        <Card title="Новое событие">
          <div className="grid gap-2 sm:grid-cols-2 eds-type-small">
            <label>
              Название
              <Input className="mt-1" value={title} onChange={(e) => setTitle(e.target.value)} />
            </label>
            <label>
              Дата
              <Input className="mt-1" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <label>
              Время
              <Input className="mt-1" type="time" value={time} onChange={(e) => setTime(e.target.value)} />
            </label>
            <label>
              Инструмент
              <select className="mt-1 w-full rounded border px-2 py-1" value={instrument} onChange={(e) => setInstrument(e.target.value)}>
                <option>EUR/USD</option>
                <option>DXY</option>
              </select>
            </label>
            <label className="sm:col-span-2">
              Описание
              <Input className="mt-1" value={description} onChange={(e) => setDescription(e.target.value)} />
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={reminder} onChange={(e) => setReminder(e.target.checked)} />
              Reminder
            </label>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button
              size="sm"
              className="ews-primary-cta"
              onClick={() => {
                onCreateManual({
                  action: "create",
                  title,
                  date,
                  time,
                  instrument,
                  description,
                  reminder,
                  category: "MANUAL",
                  create_signal: false,
                });
                setManualOpen(false);
                setTitle("");
              }}
            >
              Сохранить
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                onCreateManual({
                  action: "create",
                  title: title || "Событие → сигнал",
                  date,
                  time,
                  instrument,
                  description,
                  reminder,
                  category: "MANUAL",
                  create_signal: true,
                });
                setManualOpen(false);
              }}
            >
              Сохранить + сигнал
            </Button>
            <Button size="sm" variant="secondary" onClick={() => setManualOpen(false)}>
              Отмена
            </Button>
          </div>
        </Card>
      ) : null}

      {sameDay(cursor, new Date()) ? null : null}
    </div>
  );
}
