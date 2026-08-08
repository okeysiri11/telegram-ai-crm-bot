/**
 * Epic 45.2 — AI Workspace / Continuous Memory UI.
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

type WorkspacePayload = {
  title?: string;
  projects?: { id: string; title: string }[];
  documents?: { id: string; title: string }[];
  images?: { id: string; title: string }[];
  videos?: { id: string; title: string }[];
  generations?: { id: string; title: string }[];
  prompts?: { id: string; title: string }[];
  favorites?: { id: string; title: string }[];
  drafts?: { id: string; title: string }[];
  continue?: { id: string; title: string; kind?: string }[];
  suggestions?: { label: string; ref_id?: string }[];
  resume?: {
    welcome_ru?: string;
    suggestions_ru?: string[];
    unfinished_tasks?: { title: string }[];
  };
};

function ListBlock({ title, items }: { title: string; items?: { id?: string; title: string }[] }) {
  return (
    <Card title={title}>
      <ul className="flex flex-col gap-1 text-sm">
        {(items || []).length === 0 ? <li className="text-[var(--ew-muted)]">Пусто</li> : null}
        {(items || []).map((item, idx) => (
          <li key={item.id || `${title}-${idx}`}>• {item.title}</li>
        ))}
      </ul>
    </Card>
  );
}

export function AiWorkspacePage() {
  const [data, setData] = useState<WorkspacePayload | null>(null);
  const [timeline, setTimeline] = useState<{ events?: { title: string; action: string }[] } | null>(null);
  const [query, setQuery] = useState("");
  const [searchHits, setSearchHits] = useState<{ title: string; kind?: string; score?: number }[]>([]);

  const load = useCallback(async () => {
    try {
      const [ws, tl] = await Promise.all([
        fetch("/api/v1/memory/workspace", { credentials: "include" }),
        fetch("/api/v1/memory/timeline?window=today", { credentials: "include" }),
      ]);
      if (ws.ok) {
        const json = await ws.json();
        setData(json.data || json);
      } else {
        setData({
          title: "Моя рабочая область",
          continue: [],
          suggestions: [
            { label: "Продолжить рекламу" },
            { label: "Закончить документ" },
            { label: "Опубликовать пост" },
          ],
          resume: { welcome_ru: "Добро пожаловать." },
        });
      }
      if (tl.ok) {
        const json = await tl.json();
        setTimeline(json.data || json);
      }
    } catch {
      setData({
        title: "Моя рабочая область",
        resume: { welcome_ru: "Добро пожаловать." },
        suggestions: [{ label: "Продолжить работу" }],
      });
    }
  }, []);

  useEffect(() => {
    document.title = "Моя рабочая область · ADOS";
    void load();
  }, [load]);

  async function runSearch() {
    const q = query.trim();
    if (!q) return;
    try {
      const res = await fetch(`/api/v1/memory/search?q=${encodeURIComponent(q)}`, {
        credentials: "include",
      });
      if (!res.ok) return;
      const json = await res.json();
      setSearchHits((json.data || json).results || []);
    } catch {
      setSearchHits([]);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mx-auto flex max-w-6xl flex-col gap-4 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">{data?.title || "Моя рабочая область"}</h1>
            <p className="text-sm text-[var(--ew-muted)]">
              {data?.resume?.welcome_ru || "Непрерывная память между Telegram, Web, Desktop и Voice."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone="success">Continuous Memory</Badge>
            <Link to="/ai-command" className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm">
              AI Command
            </Link>
            <Link to="/settings/ai-mode" className="rounded-md border border-[var(--ew-border)] px-3 py-1.5 text-sm">
              Режим работы
            </Link>
          </div>
        </div>

        <Card title="Продолжить работу">
          <ul className="mb-3 flex flex-col gap-1 text-sm">
            {(data?.continue || []).length === 0 ? (
              <li className="text-[var(--ew-muted)]">Нет незавершённой работы</li>
            ) : (
              (data?.continue || []).map((item) => (
                <li key={item.id}>
                  • {item.title} {item.kind ? <span className="text-[var(--ew-muted)]">({item.kind})</span> : null}
                </li>
              ))
            )}
          </ul>
          <div className="flex flex-wrap gap-2">
            {(data?.suggestions || []).map((s) => (
              <span
                key={s.label}
                className="rounded-full border border-[var(--ew-border)] px-3 py-1 text-xs"
              >
                {s.label}
              </span>
            ))}
          </div>
        </Card>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <ListBlock title="Последние проекты" items={data?.projects} />
          <ListBlock title="Недавние документы" items={data?.documents} />
          <ListBlock title="Последние изображения" items={data?.images} />
          <ListBlock title="Последние видео" items={data?.videos} />
          <ListBlock title="Последние генерации" items={data?.generations} />
          <ListBlock title="Последние промпты" items={data?.prompts} />
          <ListBlock title="Избранное" items={data?.favorites} />
          <ListBlock title="Черновики" items={data?.drafts} />
          <Card title="AI Timeline · Сегодня">
            <ul className="flex flex-col gap-1 text-sm">
              {(timeline?.events || []).length === 0 ? (
                <li className="text-[var(--ew-muted)]">Пока нет событий</li>
              ) : (
                (timeline?.events || []).slice(0, 12).map((e, i) => (
                  <li key={`${e.title}-${i}`}>
                    • {e.title} <span className="text-[var(--ew-muted)]">({e.action})</span>
                  </li>
                ))
              )}
            </ul>
          </Card>
        </div>

        <Card title="Search Everywhere">
          <div className="flex flex-wrap gap-2">
            <input
              className="min-w-[16rem] flex-1 rounded-md border border-[var(--ew-border)] bg-transparent px-3 py-2 text-sm"
              placeholder="CRM · ERP · Knowledge · Memory · Projects…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void runSearch();
              }}
              data-testid="memory-search-input"
            />
            <button
              type="button"
              className="rounded-md border border-[var(--ew-border)] px-3 py-2 text-sm"
              onClick={() => void runSearch()}
              data-testid="memory-search-btn"
            >
              Найти
            </button>
          </div>
          <ul className="mt-3 flex flex-col gap-1 text-sm">
            {searchHits.map((h, i) => (
              <li key={`${h.title}-${i}`}>
                • {h.title} {h.kind ? `(${h.kind})` : ""} {h.score != null ? `· ${h.score}` : ""}
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
