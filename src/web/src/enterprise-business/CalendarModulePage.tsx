/**
 * Sprint 30.8 — Calendar: day / week / month · meetings · tasks · reminders.
 */

import { useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import { loadJson, saveJson, newId } from "./persist";

export type CalEvent = {
  id: string;
  title: string;
  at: string;
  kind: "meeting" | "task" | "reminder" | "general";
  module?: string;
};

type CalState = { events: CalEvent[] };

function read(): CalState {
  return loadJson("calendar", { events: [] });
}
function write(s: CalState) {
  saveJson("calendar", s);
}

const TABS = [
  { id: "day", label: "День" },
  { id: "week", label: "Неделя" },
  { id: "month", label: "Месяц" },
  { id: "meetings", label: "Встречи" },
  { id: "tasks", label: "Задачи" },
  { id: "reminders", label: "Напоминания" },
] as const;

function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

export function CalendarModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "week";
  const [state, setState] = useState(read);
  const [title, setTitle] = useState("");
  const [when, setWhen] = useState(() => new Date().toISOString().slice(0, 16));
  const active = TABS.some((t) => t.id === view) ? view : "week";
  const now = useMemo(() => new Date(), []);

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  const filtered = useMemo(() => {
    const day0 = startOfDay(now).getTime();
    const dayEnd = day0 + 86400000;
    const weekEnd = day0 + 7 * 86400000;
    const monthEnd = day0 + 31 * 86400000;
    return state.events.filter((e) => {
      const t = new Date(e.at).getTime();
      if (active === "day") return t >= day0 && t < dayEnd;
      if (active === "week") return t >= day0 && t < weekEnd;
      if (active === "month") return t >= day0 && t < monthEnd;
      if (active === "meetings") return e.kind === "meeting";
      if (active === "tasks") return e.kind === "task";
      if (active === "reminders") return e.kind === "reminder";
      return true;
    });
  }, [state.events, active, now]);

  function add(kind: CalEvent["kind"]) {
    if (!title.trim()) return;
    const ev: CalEvent = {
      id: newId("cal"),
      title: title.trim(),
      at: new Date(when).toISOString(),
      kind,
      module: "enterprise",
    };
    const next = { events: [ev, ...state.events] };
    write(next);
    setState(next);
    setTitle("");
  }

  return (
    <BusinessModuleShell
      title="Календарь"
      subtitle="День · неделя · месяц · встречи · задачи · напоминания"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source="Workspace · CalendarService"
      testId="calendar-module"
      actions={
        <Link to="/crm?view=activity">
          <Button size="sm" variant="ghost">
            CRM активность
          </Button>
        </Link>
      }
    >
      <Card title="Новое событие">
        <div className="flex flex-wrap gap-2">
          <Input placeholder="Название" value={title} onChange={(e) => setTitle(e.target.value)} />
          <Input type="datetime-local" value={when} onChange={(e) => setWhen(e.target.value)} />
          <Button size="sm" onClick={() => add("meeting")}>
            Встреча
          </Button>
          <Button size="sm" variant="secondary" onClick={() => add("task")}>
            Задача
          </Button>
          <Button size="sm" variant="ghost" onClick={() => add("reminder")}>
            Напоминание
          </Button>
        </div>
      </Card>
      <div className="eds-grid eds-grid--dashboard mt-3">
        {filtered.map((e) => (
          <Card key={e.id} title={e.title} status={<Badge>{e.kind}</Badge>}>
            <p className="eds-type-helper">{new Date(e.at).toLocaleString("ru-RU")}</p>
          </Card>
        ))}
        {!filtered.length ? <p className="eds-type-helper">Нет событий в этом представлении</p> : null}
      </div>
    </BusinessModuleShell>
  );
}

export function countCalendarEvents(): number {
  return read().events.length;
}
