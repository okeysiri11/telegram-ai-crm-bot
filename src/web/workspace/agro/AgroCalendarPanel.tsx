/**
 * AGRO 1.2 — month calendar even when empty.
 */

import { useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsPost, pick } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

function monthCells(year: number, month: number) {
  const first = new Date(year, month, 1);
  const start = first.getDay() === 0 ? 6 : first.getDay() - 1;
  const days = new Date(year, month + 1, 0).getDate();
  const cells: Array<{ date: string; day: number | null }> = [];
  for (let i = 0; i < start; i += 1) cells.push({ date: "", day: null });
  for (let d = 1; d <= days; d += 1) {
    const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    cells.push({ date: iso, day: d });
  }
  return cells;
}

export function AgroCalendarPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  events: Row[];
  onChanged: () => void;
  onOpen: (id: string) => void;
}) {
  const now = new Date();
  const [cursor, setCursor] = useState({ y: now.getFullYear(), m: now.getMonth() });
  const [title, setTitle] = useState("");
  const [when, setWhen] = useState("");
  const [msg, setMsg] = useState("");
  const [field, setField] = useState("");
  const [workType, setWorkType] = useState("");
  const [manager, setManager] = useState("");
  const [machine, setMachine] = useState("");
  const cells = useMemo(() => monthCells(cursor.y, cursor.m), [cursor]);
  const byDay = useMemo(() => {
    const map: Record<string, Row[]> = {};
    for (const ev of props.events) {
      if (field && String(ev.field_id || "") !== field) continue;
      if (workType && String(ev.event_type || ev.work_type || "") !== workType) continue;
      if (manager && String(ev.owner || ev.responsible || "") !== manager) continue;
      if (machine && String(ev.machine_id || "") !== machine) continue;
      const key = String(ev.starts_at || "").slice(0, 10);
      if (!key) continue;
      map[key] = map[key] || [];
      map[key].push(ev);
    }
    return map;
  }, [props.events, field, workType, manager, machine]);

  return (
    <div className="grid gap-3" data-testid="agro-calendar-panel">
      <div className="flex items-center justify-between">
        <Button size="sm" variant="ghost" onClick={() => setCursor((c) => ({ y: c.m === 0 ? c.y - 1 : c.y, m: c.m === 0 ? 11 : c.m - 1 }))}>
          ←
        </Button>
        <h3 className="eds-type-small">
          {new Date(cursor.y, cursor.m, 1).toLocaleDateString("ru-RU", { month: "long", year: "numeric" })}
        </h3>
        <Button size="sm" variant="ghost" onClick={() => setCursor((c) => ({ y: c.m === 11 ? c.y + 1 : c.y, m: c.m === 11 ? 0 : c.m + 1 }))}>
          →
        </Button>
      </div>
      <div className="grid gap-2 sm:grid-cols-4" data-testid="agro-calendar-filters">
        <Input placeholder="Field" value={field} onChange={(e) => setField(e.target.value)} />
        <Input placeholder="Work type" value={workType} onChange={(e) => setWorkType(e.target.value)} />
        <Input placeholder="Manager" value={manager} onChange={(e) => setManager(e.target.value)} />
        <Input placeholder="Machine" value={machine} onChange={(e) => setMachine(e.target.value)} />
      </div>
      <div className="grid grid-cols-7 gap-1" data-testid="agro-calendar-month">
        {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((d) => (
          <div key={d} className="eds-type-caption text-center">{d}</div>
        ))}
        {cells.map((c, i) => (
          <div key={`${c.date}-${i}`} className="min-h-16 rounded border border-[var(--ew-border)] p-1 eds-type-caption">
            {c.day ?? ""}
            {(byDay[c.date] || []).map((ev) => (
              <button key={pick(ev, "id")} type="button" className="mt-1 block w-full truncate text-left underline" onClick={() => props.onOpen(pick(ev, "id"))}>
                {pick(ev, "title")}
              </button>
            ))}
          </div>
        ))}
      </div>
      {props.canOperate ? (
        <Card title="Создать событие">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Название" value={title} onChange={(e) => setTitle(e.target.value)} />
            <Input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
          </div>
          <Button
            className="mt-2"
            size="sm"
            onClick={async () => {
              const r = await agroOpsPost("/entities/calendar", { title, starts_at: when }, props.headers);
              const j = r.json as { ok?: boolean; message_ru?: string };
              setMsg(j.ok ? "Событие создано" : j.message_ru || "Ошибка");
              if (j.ok) {
                setTitle("");
                props.onChanged();
              }
            }}
          >
            Сохранить событие
          </Button>
        </Card>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
