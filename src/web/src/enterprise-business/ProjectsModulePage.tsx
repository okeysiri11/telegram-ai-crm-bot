/**
 * Sprint 30.8 — Projects module: projects, kanban, tasks, milestones, timeline, docs, team.
 * Workspace-backed until a platform Project entity exists (see PROJECT_LIFECYCLE.md).
 */

import { useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import { loadJson, saveJson, newId } from "./persist";

export type ProjectRecord = {
  id: string;
  name: string;
  status: "active" | "paused" | "done";
  owner: string;
};

export type ProjectTask = {
  id: string;
  projectId: string;
  title: string;
  status: "backlog" | "doing" | "review" | "done";
};

export type Milestone = { id: string; projectId: string; title: string; due: string };
export type ProjectDoc = { id: string; projectId: string; title: string };
export type TeamMember = { id: string; projectId: string; name: string; role: string };
export type TimelineItem = { id: string; projectId: string; title: string; at: string };

type ProjectsState = {
  projects: ProjectRecord[];
  tasks: ProjectTask[];
  milestones: Milestone[];
  docs: ProjectDoc[];
  team: TeamMember[];
  timeline: TimelineItem[];
};

const EMPTY: ProjectsState = { projects: [], tasks: [], milestones: [], docs: [], team: [], timeline: [] };

function read(): ProjectsState {
  return loadJson("projects", EMPTY);
}
function write(s: ProjectsState) {
  saveJson("projects", s);
}

const TABS = [
  { id: "projects", label: "Проекты" },
  { id: "kanban", label: "Канбан" },
  { id: "tasks", label: "Задачи" },
  { id: "milestones", label: "Веха" },
  { id: "timeline", label: "Таймлайн" },
  { id: "documents", label: "Документы" },
  { id: "team", label: "Команда" },
] as const;

const KANBAN = ["backlog", "doing", "review", "done"] as const;

export function ProjectsModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "projects";
  const [state, setState] = useState(read);
  const [form, setForm] = useState({ a: "", b: "" });
  const active = TABS.some((t) => t.id === view) ? view : "projects";
  const projectId = state.projects[0]?.id;

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  function sync(next: ProjectsState) {
    write(next);
    setState(next);
  }

  const kanban = useMemo(() => {
    const map: Record<string, ProjectTask[]> = {};
    for (const c of KANBAN) map[c] = state.tasks.filter((t) => t.status === c);
    return map;
  }, [state.tasks]);

  return (
    <BusinessModuleShell
      title="Проекты"
      subtitle="Портфель · канбан · задачи · вехи · команда"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source="Workspace · CRM tasks API"
      testId="projects-module"
      actions={
        <Link to="/tasks">
          <Button size="sm" variant="secondary">
            Центр задач
          </Button>
        </Link>
      }
    >
      {active === "projects" ? (
        <section className="space-y-3">
          <Card title="Новый проект">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Владелец" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim()) return;
                  const p: ProjectRecord = {
                    id: newId("prj"),
                    name: form.a.trim(),
                    status: "active",
                    owner: form.b.trim() || "owner",
                  };
                  const next = {
                    ...state,
                    projects: [p, ...state.projects],
                    timeline: [
                      { id: newId("tl"), projectId: p.id, title: `Создан проект ${p.name}`, at: new Date().toISOString() },
                      ...state.timeline,
                    ],
                  };
                  sync(next);
                  setForm({ a: "", b: "" });
                }}
              >
                Создать
              </Button>
            </div>
          </Card>
          <div className="eds-grid eds-grid--dashboard">
            {state.projects.map((p) => (
              <Card key={p.id} title={p.name} status={<Badge tone="success">{p.status}</Badge>}>
                <p className="eds-type-helper">Владелец: {p.owner}</p>
              </Card>
            ))}
            {!state.projects.length ? <p className="eds-type-helper">Создайте первый проект</p> : null}
          </div>
        </section>
      ) : null}

      {active === "kanban" ? (
        <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {KANBAN.map((col) => (
            <Card key={col} title={col}>
              <ul className="space-y-2 eds-type-small">
                {(kanban[col] || []).map((t) => (
                  <li key={t.id} className="rounded border border-[var(--eds-border)] px-2 py-1">
                    {t.title}
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </section>
      ) : null}

      {active === "tasks" ? (
        <section className="space-y-3">
          <Card title="Задача">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название задачи" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim() || !projectId) return;
                  const t: ProjectTask = {
                    id: newId("pt"),
                    projectId,
                    title: form.a.trim(),
                    status: "backlog",
                  };
                  sync({ ...state, tasks: [t, ...state.tasks] });
                  setForm({ a: "", b: "" });
                }}
              >
                Добавить
              </Button>
            </div>
            {!projectId ? <p className="eds-type-helper mt-2">Сначала создайте проект</p> : null}
          </Card>
          <ul className="space-y-2">
            {state.tasks.map((t) => (
              <li key={t.id} className="flex flex-wrap items-center gap-2 rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                <span className="flex-1">{t.title}</span>
                <Badge>{t.status}</Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    const order = [...KANBAN];
                    const i = order.indexOf(t.status);
                    const nextStatus = order[Math.min(i + 1, order.length - 1)];
                    sync({
                      ...state,
                      tasks: state.tasks.map((x) => (x.id === t.id ? { ...x, status: nextStatus } : x)),
                    });
                  }}
                >
                  Далее →
                </Button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {active === "milestones" ? (
        <section className="space-y-3">
          <Card title="Веха">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Срок (YYYY-MM-DD)" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim() || !projectId) return;
                  sync({
                    ...state,
                    milestones: [
                      { id: newId("ms"), projectId, title: form.a.trim(), due: form.b.trim() || new Date().toISOString().slice(0, 10) },
                      ...state.milestones,
                    ],
                  });
                  setForm({ a: "", b: "" });
                }}
              >
                Добавить
              </Button>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.milestones.map((m) => (
              <li key={m.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                {m.title} · {m.due}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {active === "timeline" ? (
        <ul className="space-y-2">
          {state.timeline.map((t) => (
            <li key={t.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
              {t.title}
              <span className="block eds-type-helper">{new Date(t.at).toLocaleString("ru-RU")}</span>
            </li>
          ))}
        </ul>
      ) : null}

      {active === "documents" ? (
        <section className="space-y-3">
          <Card title="Документ проекта">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim() || !projectId) return;
                  sync({
                    ...state,
                    docs: [{ id: newId("pd"), projectId, title: form.a.trim() }, ...state.docs],
                  });
                  setForm({ a: "", b: "" });
                }}
              >
                Добавить
              </Button>
              <Link to="/documents">
                <Button size="sm" variant="secondary">
                  Drive
                </Button>
              </Link>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.docs.map((d) => (
              <li key={d.id} className="eds-type-small">
                {d.title}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {active === "team" ? (
        <section className="space-y-3">
          <Card title="Участник">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Имя" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Роль" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim() || !projectId) return;
                  sync({
                    ...state,
                    team: [
                      { id: newId("tm"), projectId, name: form.a.trim(), role: form.b.trim() || "member" },
                      ...state.team,
                    ],
                  });
                  setForm({ a: "", b: "" });
                }}
              >
                Добавить
              </Button>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.team.map((m) => (
              <li key={m.id} className="eds-type-small">
                {m.name} · {m.role}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </BusinessModuleShell>
  );
}

export function countProjects(): number {
  return read().projects.length;
}
