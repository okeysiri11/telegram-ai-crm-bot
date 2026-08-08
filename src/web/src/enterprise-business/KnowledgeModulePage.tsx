/**
 * Sprint 30.8 — Knowledge Base / Wiki / Docs / Semantic + AI search.
 * Binds to /api/enterprise-ekp/v1 when available; workspace cache otherwise.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { apiFetch } from "@/integrations/apiClient";
import { BusinessModuleShell } from "./BusinessModuleShell";
import { loadJson, saveJson, newId } from "./persist";

export type KnowledgeArticle = {
  id: string;
  title: string;
  body: string;
  category: string;
  tags: string[];
  kind: "wiki" | "doc" | "kb";
  updatedAt: string;
};

type KnowledgeState = {
  articles: KnowledgeArticle[];
  source: "api" | "workspace";
};

const EMPTY: KnowledgeState = { articles: [], source: "workspace" };
const EKP = "/api/enterprise-ekp/v1";

const TABS = [
  { id: "kb", label: "База знаний" },
  { id: "wiki", label: "Wiki" },
  { id: "docs", label: "Документация" },
  { id: "search", label: "Поиск" },
  { id: "categories", label: "Категории" },
  { id: "tags", label: "Теги" },
  { id: "ai", label: "AI-поиск" },
] as const;

function read(): KnowledgeState {
  return loadJson("knowledge", EMPTY);
}
function write(s: KnowledgeState) {
  saveJson("knowledge", s);
}

export async function hydrateKnowledge(): Promise<KnowledgeState> {
  const cached = read();
  try {
    const res = await apiFetch(`${EKP}/documents`);
    if (!res.ok) return { ...cached, source: "workspace" };
    const json = (await res.json()) as { items?: Array<Record<string, unknown>>; documents?: Array<Record<string, unknown>> };
    const items = json.items || json.documents || [];
    if (!items.length) return { ...cached, source: "api" };
    const articles: KnowledgeArticle[] = items.map((raw) => ({
      id: String(raw.id || raw.document_id || newId("kb")),
      title: String(raw.title || raw.name || "Документ"),
      body: String(raw.body || raw.content || raw.summary || ""),
      category: String(raw.category || "general"),
      tags: Array.isArray(raw.tags) ? (raw.tags as string[]) : [],
      kind: "kb",
      updatedAt: String(raw.updated_at || raw.updatedAt || new Date().toISOString()),
    }));
    const next = { articles, source: "api" as const };
    write(next);
    return next;
  } catch {
    return { ...cached, source: "workspace" };
  }
}

export function KnowledgeModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "kb";
  const [state, setState] = useState(read);
  const [q, setQ] = useState("");
  const [form, setForm] = useState({ title: "", body: "", category: "general", tags: "" });
  const active = TABS.some((t) => t.id === view) ? view : "kb";

  const refresh = useCallback(async () => {
    setState(await hydrateKnowledge());
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let list = state.articles;
    if (active === "wiki") list = list.filter((a) => a.kind === "wiki");
    if (active === "docs") list = list.filter((a) => a.kind === "doc");
    if (active === "kb") list = list.filter((a) => a.kind === "kb" || a.kind === "wiki" || a.kind === "doc");
    if (!needle) return list;
    return list.filter(
      (a) =>
        a.title.toLowerCase().includes(needle) ||
        a.body.toLowerCase().includes(needle) ||
        a.tags.some((t) => t.toLowerCase().includes(needle)) ||
        a.category.toLowerCase().includes(needle),
    );
  }, [state.articles, q, active]);

  const categories = useMemo(() => [...new Set(state.articles.map((a) => a.category))], [state.articles]);
  const tags = useMemo(() => [...new Set(state.articles.flatMap((a) => a.tags))], [state.articles]);

  function addArticle(kind: KnowledgeArticle["kind"]) {
    if (!form.title.trim()) return;
    const article: KnowledgeArticle = {
      id: newId("kb"),
      title: form.title.trim(),
      body: form.body.trim(),
      category: form.category.trim() || "general",
      tags: form.tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
      kind,
      updatedAt: new Date().toISOString(),
    };
    const next = { articles: [article, ...state.articles], source: "workspace" as const };
    write(next);
    setState(next);
    setForm({ title: "", body: "", category: "general", tags: "" });
  }

  return (
    <BusinessModuleShell
      title="Знания"
      subtitle="Knowledge · wiki · документация · семантический и AI-поиск"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source={state.source === "api" ? "EKP API" : "Workspace"}
      testId="knowledge-module"
      actions={
        <>
          <Button size="sm" variant="secondary" onClick={() => void refresh()}>
            Обновить
          </Button>
          <Link to="/platform-builder/knowledge">
            <Button size="sm" variant="ghost">
              Граф
            </Button>
          </Link>
        </>
      }
    >
      {active === "search" || active === "ai" ? (
        <Card title={active === "ai" ? "AI-поиск" : "Семантический поиск"}>
          <div className="flex flex-wrap gap-2">
            <Input
              className="min-w-[240px] flex-1"
              placeholder={active === "ai" ? "Спросите базу знаний…" : "Поиск по статьям…"}
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <ul className="mt-3 space-y-2">
            {filtered.map((a) => (
              <li key={a.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                <strong>{a.title}</strong>
                <span className="block eds-type-helper">{a.body.slice(0, 160)}</span>
              </li>
            ))}
            {!filtered.length ? <li className="eds-type-helper">Ничего не найдено</li> : null}
          </ul>
        </Card>
      ) : null}

      {active === "categories" ? (
        <div className="flex flex-wrap gap-2">
          {categories.map((c) => (
            <Badge key={c}>{c}</Badge>
          ))}
          {!categories.length ? <p className="eds-type-helper">Категорий пока нет</p> : null}
        </div>
      ) : null}

      {active === "tags" ? (
        <div className="flex flex-wrap gap-2">
          {tags.map((t) => (
            <Badge key={t}>{t}</Badge>
          ))}
          {!tags.length ? <p className="eds-type-helper">Тегов пока нет</p> : null}
        </div>
      ) : null}

      {active === "kb" || active === "wiki" || active === "docs" ? (
        <section className="space-y-3">
          <Card title={active === "wiki" ? "Новая wiki-страница" : active === "docs" ? "Новый документ" : "Новая статья"}>
            <div className="grid gap-2 md:grid-cols-2">
              <Input placeholder="Заголовок" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              <Input placeholder="Категория" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
              <Input
                className="md:col-span-2"
                placeholder="Текст"
                value={form.body}
                onChange={(e) => setForm({ ...form, body: e.target.value })}
              />
              <Input placeholder="Теги через запятую" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
              <Button size="sm" onClick={() => addArticle(active === "wiki" ? "wiki" : active === "docs" ? "doc" : "kb")}>
                Сохранить
              </Button>
            </div>
          </Card>
          <div className="eds-grid eds-grid--dashboard">
            {filtered.map((a) => (
              <Card key={a.id} title={a.title} status={<Badge>{a.category}</Badge>}>
                <p className="eds-type-helper line-clamp-3">{a.body || "—"}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {a.tags.map((t) => (
                    <Badge key={t}>{t}</Badge>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </section>
      ) : null}
    </BusinessModuleShell>
  );
}

export function countKnowledge(): number {
  return read().articles.length;
}
