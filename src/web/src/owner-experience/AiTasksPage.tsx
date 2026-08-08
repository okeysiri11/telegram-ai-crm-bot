/**
 * Sprint 42.9 — Центр AI-задач (лёгкий UX-слой без нового engine).
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { create } from "zustand";
import { wsKey } from "@/multi-role/workspaceSlot";
import { VERTICAL_WORKSPACES } from "@/vertical-workspace/catalog";

type AiTask = {
  id: string;
  title: string;
  description: string;
  assignee: string;
  priority: "низкий" | "средний" | "высокий";
  status: "черновик" | "запущена" | "выполняется" | "готово";
};

const KEY = wsKey("ewp_ai_tasks_v1");

function load(): AiTask[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as AiTask[];
  } catch {
    /* ignore */
  }
  return [];
}

type Store = {
  tasks: AiTask[];
  add: (t: Omit<AiTask, "id" | "status">) => void;
  run: (id: string) => void;
};

const useAiTasksStore = create<Store>((set, get) => ({
  tasks: typeof localStorage !== "undefined" ? load() : [],
  add: (t) => {
    const next: AiTask = {
      ...t,
      id: `task_${Date.now()}`,
      status: "черновик",
    };
    const tasks = [next, ...get().tasks].slice(0, 40);
    try {
      localStorage.setItem(KEY, JSON.stringify(tasks));
    } catch {
      /* ignore */
    }
    set({ tasks });
  },
  run: (id) => {
    const tasks = get().tasks.map((t) =>
      t.id === id ? { ...t, status: "запущена" as const } : t,
    );
    // simulate progress
    try {
      localStorage.setItem(KEY, JSON.stringify(tasks));
    } catch {
      /* ignore */
    }
    set({ tasks });
    window.setTimeout(() => {
      const progressed = useAiTasksStore
        .getState()
        .tasks.map((t) => (t.id === id ? { ...t, status: "выполняется" as const } : t));
      try {
        localStorage.setItem(KEY, JSON.stringify(progressed));
      } catch {
        /* ignore */
      }
      useAiTasksStore.setState({ tasks: progressed });
      window.setTimeout(() => {
        const done = useAiTasksStore
          .getState()
          .tasks.map((t) => (t.id === id ? { ...t, status: "готово" as const } : t));
        try {
          localStorage.setItem(KEY, JSON.stringify(done));
        } catch {
          /* ignore */
        }
        useAiTasksStore.setState({ tasks: done });
      }, 1200);
    }, 800);
  },
}));

const ASSIGNEES = [
  "AI Консьерж",
  "CRM AI",
  "Crypto AI",
  "Drone AI",
  "Travel AI",
  "Construction AI",
  "Production AI",
  "Knowledge AI",
  "Marketing AI",
  ...VERTICAL_WORKSPACES.flatMap((v) =>
    v.agents.filter((a) => a.id !== "concierge").map((a) => a.name),
  ),
].filter((v, i, a) => a.indexOf(v) === i);

export function AiTasksPage() {
  const tasks = useAiTasksStore((s) => s.tasks);
  const add = useAiTasksStore((s) => s.add);
  const run = useAiTasksStore((s) => s.run);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignee, setAssignee] = useState(ASSIGNEES[0]!);
  const [priority, setPriority] = useState<AiTask["priority"]>("средний");
  const createMode =
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("action") === "create";

  function submit() {
    if (!title.trim()) return;
    add({ title: title.trim(), description: description.trim(), assignee, priority });
    setTitle("");
    setDescription("");
  }

  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="ai-tasks-center">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="eds-type-title text-2xl">Центр AI-задач</h1>
            <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
              Владелец ставит задачу Консьержу — тот распределяет её между специалистами.
            </p>
          </div>
          <Link to="/ai-agents">
            <Button variant="secondary">AI-агенты</Button>
          </Link>
        </header>

        <Card title={createMode ? "Создать задачу" : "Новая AI-задача"}>
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block space-y-1">
              <span className="eds-type-caption">Описание / название</span>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Например: Подготовить отчёт по сделкам"
              />
            </label>
            <label className="block space-y-1">
              <span className="eds-type-caption">Исполнитель AI</span>
              <select
                className="eds-control w-full"
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
              >
                {ASSIGNEES.map((a) => (
                  <option key={a} value={a}>
                    {a}
                  </option>
                ))}
              </select>
            </label>
            <label className="block space-y-1 md:col-span-2">
              <span className="eds-type-caption">Подробности</span>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Что нужно сделать"
              />
            </label>
            <label className="block space-y-1">
              <span className="eds-type-caption">Приоритет</span>
              <select
                className="eds-control w-full"
                value={priority}
                onChange={(e) => setPriority(e.target.value as AiTask["priority"])}
              >
                <option value="низкий">Низкий</option>
                <option value="средний">Средний</option>
                <option value="высокий">Высокий</option>
              </select>
            </label>
            <div className="flex items-end">
              <Button className="ews-primary-cta" onClick={submit}>
                Создать задачу
              </Button>
            </div>
          </div>
        </Card>

        <Card title="Задачи">
          {tasks.length === 0 ? (
            <p className="eds-type-helper">Пока нет AI-задач. Создайте первую.</p>
          ) : (
            <ul className="space-y-3">
              {tasks.map((t) => (
                <li
                  key={t.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--ew-border)] p-3"
                >
                  <div>
                    <p className="font-semibold">{t.title}</p>
                    <p className="eds-type-helper">
                      {t.assignee} · приоритет {t.priority}
                    </p>
                    {t.description ? (
                      <p className="eds-type-small text-[var(--eds-text-muted)]">{t.description}</p>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge>{t.status}</Badge>
                    {t.status === "черновик" ? (
                      <Button size="sm" onClick={() => run(t.id)}>
                        Запустить
                      </Button>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
