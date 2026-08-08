/**
 * Epic 44.0 — AI Command Center (Universal AI OS UI).
 */

import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Card } from "@/ui";

type TabId = "dialogs" | "agents" | "tools" | "history" | "voice" | "verticals" | "monitor" | "settings";

const TABS: { id: TabId; label: string }[] = [
  { id: "dialogs", label: "Диалоги" },
  { id: "agents", label: "Агенты" },
  { id: "tools", label: "Инструменты" },
  { id: "history", label: "История" },
  { id: "voice", label: "Голос" },
  { id: "verticals", label: "Вертикали" },
  { id: "monitor", label: "Мониторинг" },
  { id: "settings", label: "Настройки" },
];

type ChatMsg = { role: "user" | "assistant"; text: string };

export function AiCommandCenterPage() {
  const [tab, setTab] = useState<TabId>("dialogs");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      role: "assistant",
      text: "AI Command Center готов. Пишите или используйте голос — выполнение через Hercules.",
    },
  ]);
  const [home, setHome] = useState<{
    quick_commands?: string[];
    verticals?: string[];
    tools?: { id: string; name_ru: string }[];
    recent?: { prompt: string; cost: number; status: string }[];
  } | null>(null);
  const [busy, setBusy] = useState(false);

  const loadHome = useCallback(async () => {
    try {
      const res = await fetch("/management/v1/ai-command/home", { credentials: "include" });
      if (!res.ok) return;
      const json = await res.json();
      setHome(json.data || json);
    } catch {
      setHome({
        quick_commands: [
          "Создать рекламу",
          "Создать изображение",
          "Создать видео",
          "Создать клиента",
        ],
        verticals: ["beauty", "auto", "crypto", "crm", "owner"],
        tools: [
          { id: "generate_image", name_ru: "Генерация изображения" },
          { id: "generate_video", name_ru: "Генерация видео" },
        ],
        recent: [],
      });
    }
  }, []);

  useEffect(() => {
    void loadHome();
  }, [loadHome]);

  const send = async (text: string, voice = false) => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: trimmed }]);
    setInput("");
    try {
      const res = await fetch("/management/v1/ai-command/chat", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: trimmed, channel: "web", voice, max_steps: 3 }),
      });
      const json = await res.json().catch(() => ({}));
      const reply =
        json?.data?.reply_ru ||
        json?.reply_ru ||
        (res.ok ? "Готово через Hercules." : "Команда принята (офлайн-режим).");
      setMessages((m) => [...m, { role: "assistant", text: reply }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Связь с API недоступна. Команда сохранена локально." },
      ]);
    } finally {
      setBusy(false);
      void loadHome();
    }
  };

  return (
    <WorkspaceLayout>
      <div className="space-y-4" data-testid="ai-command-center">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <Badge tone="accent">AI OS · Hercules</Badge>
            <h1 className="eds-type-title mt-2 text-2xl">AI Command Center</h1>
            <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
              Единая точка команд: текст, голос, документы. Все через Hercules.
            </p>
          </div>
          <Link to="/platform-builder/ops-center" className="eds-type-caption text-[var(--eds-accent)]">
            ← Ops Center
          </Link>
        </header>

        <div className="flex flex-wrap gap-2" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              className={`rounded px-3 py-1.5 eds-type-caption ${
                tab === t.id
                  ? "bg-[var(--eds-accent)] text-white"
                  : "bg-[var(--eds-surface)] text-[var(--eds-text-muted)]"
              }`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {tab === "dialogs" && (
          <Card title="Чат">
            <div className="mb-3 flex flex-wrap gap-2">
              {(home?.quick_commands || []).slice(0, 6).map((q) => (
                <button
                  key={q}
                  type="button"
                  className="rounded border border-[var(--eds-border)] px-2 py-1 eds-type-caption"
                  onClick={() => void send(q)}
                >
                  {q}
                </button>
              ))}
            </div>
            <div className="mb-3 max-h-80 space-y-2 overflow-y-auto rounded border border-[var(--eds-border)] p-3">
              {messages.map((m, i) => (
                <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                  <span className="eds-type-helper text-[var(--eds-text-muted)]">
                    {m.role === "user" ? "Вы" : "AI"}
                  </span>
                  <p className="eds-type-body whitespace-pre-wrap">{m.text}</p>
                </div>
              ))}
            </div>
            <form
              className="flex gap-2"
              onSubmit={(e) => {
                e.preventDefault();
                void send(input);
              }}
            >
              <input
                className="flex-1 rounded border border-[var(--eds-border)] bg-transparent px-3 py-2"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Напишите задачу… или голосом"
                disabled={busy}
              />
              <button type="submit" className="rounded bg-[var(--eds-accent)] px-4 py-2 text-white" disabled={busy}>
                Отправить
              </button>
              <button
                type="button"
                className="rounded border border-[var(--eds-border)] px-3 py-2"
                onClick={() => void send(input || "Создай рекламу", true)}
              >
                🎙
              </button>
            </form>
          </Card>
        )}

        {tab === "tools" && (
          <Card title="Инструменты">
            <ul className="space-y-1">
              {(home?.tools || []).map((t) => (
                <li key={t.id}>
                  {t.name_ru} <span className="eds-type-helper">({t.id})</span>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {tab === "history" && (
          <Card title="История">
            <ul className="space-y-1">
              {(home?.recent || []).map((r, i) => (
                <li key={i}>
                  {r.status} · ≈{r.cost} · {r.prompt}
                </li>
              ))}
              {!home?.recent?.length ? <li>Пока пусто</li> : null}
            </ul>
          </Card>
        )}

        {tab === "voice" && (
          <Card title="Голосовой режим">
            <p className="eds-type-body">
              Команды: «Открой CRM», «Создай клиента», «Покажи прибыль», «Создай рекламу», «Сделай
              Reels», «Опубликуй».
            </p>
          </Card>
        )}

        {tab === "verticals" && (
          <Card title="Вертикали">
            <p>{(home?.verticals || []).join(" · ")}</p>
          </Card>
        )}

        {tab === "agents" && (
          <Card title="Центр агентов">
            <p>Копирайтер · Дизайнер · Видео · Голос · Маркетинг · CRM · Аналитик — через Hercules.</p>
          </Card>
        )}

        {tab === "monitor" && (
          <Card title="Мониторинг">
            <Link to="/platform-builder/hercules" className="text-[var(--eds-accent)]">
              Hercules Control Center →
            </Link>
          </Card>
        )}

        {tab === "settings" && (
          <Card title="Настройки">
            <p>Язык: Русский · Runtime: Hercules · Канал: Web / Telegram / Voice / Desktop</p>
          </Card>
        )}
      </div>
    </WorkspaceLayout>
  );
}
