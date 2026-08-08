/**
 * Sprint 42.8 / 42.9 — универсальный дашборд вертикали.
 * AI Консьерж общий; специалисты зависят от вертикали.
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { ContextualAiChat, QuickCreatePanel } from "@/owner-experience";
import { UnifiedIntentBar } from "@/workspace-chrome/unified-intent";
import type { VerticalDef } from "./types";

export function VerticalDashboard({
  vertical,
  sectionId = "home",
}: {
  vertical: VerticalDef;
  sectionId?: string;
}) {
  const section = vertical.nav.find((n) => n.id === sectionId);
  const isHome = !sectionId || sectionId === "home";
  const specialists = vertical.agents.filter((a) => a.id !== "concierge");
  const concierge = vertical.agents.find((a) => a.id === "concierge");
  const [aiOpen, setAiOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <div className="uvw-dashboard space-y-4" data-testid={`vertical-dashboard-${vertical.id}`}>
      {isHome ? (
        <header
          className="rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-4"
          data-testid="vertical-welcome"
        >
          <p className="eds-type-body font-medium">Добро пожаловать.</p>
          <p className="mt-1 eds-type-helper text-[var(--eds-text-muted)]">Вы работаете в разделе:</p>
          <h1 className="eds-type-title text-2xl uppercase tracking-wide">{vertical.label}</h1>
          <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">{vertical.purpose}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button className="ews-primary-cta" size="sm" onClick={() => setAiOpen(true)}>
              Поговорить с AI
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setCreateOpen(true)}>
              Создать
            </Button>
            <Link to="/ai-tasks">
              <Button variant="secondary" size="sm">
                AI-задачи
              </Button>
            </Link>
          </div>
        </header>
      ) : null}

      {!isHome && section ? (
        <header className="rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-4">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">{vertical.label}</p>
          <h1 className="eds-type-title text-2xl">{section.label}</h1>
          <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
            Раздел рабочего пространства «{vertical.label}». Данные и действия подключены к платформе.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link to={vertical.route}>
              <Button variant="secondary" size="sm">
                ← К обзору
              </Button>
            </Link>
            <Button size="sm" onClick={() => setAiOpen(true)}>
              Открыть AI
            </Button>
            {vertical.legacyRoute ? (
              <Link to={vertical.legacyRoute}>
                <Button size="sm" variant="secondary">
                  Открыть полный модуль
                </Button>
              </Link>
            ) : null}
          </div>
        </header>
      ) : null}

      {/* AI Консьерж — единый во всех вертикалях */}
      <Card title="AI Консьерж" className="border-[var(--eds-success)]">
        <div className="flex flex-wrap items-start justify-between gap-3" data-testid="vertical-ai-concierge">
          <div>
            <Badge tone="success">{concierge?.name || "AI Консьерж"}</Badge>
            <p className="mt-2 eds-type-body font-medium">{vertical.aiGuide.greeting}</p>
            <p className="mt-1 eds-type-helper text-[var(--eds-text-muted)]">
              Сегодня рекомендуется:
            </p>
            <ul className="mt-2 list-disc space-y-1 pl-5 eds-type-body">
              {vertical.aiGuide.bullets.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link to={vertical.aiGuide.recommendedAction.route}>
                <Button className="ews-primary-cta" size="sm">
                  {vertical.aiGuide.recommendedAction.label}
                </Button>
              </Link>
              <Button size="sm" variant="secondary" onClick={() => setAiOpen(true)}>
                Поговорить с AI
              </Button>
            </div>
          </div>
          <div className="min-w-[12rem] rounded-md border border-[var(--ew-border)] p-3">
            <p className="eds-type-caption font-semibold">Специалисты</p>
            <ul className="mt-2 space-y-1 eds-type-small">
              {specialists.map((a) => (
                <li key={a.id}>
                  <span className="font-medium">{a.name}</span>
                  <span className="text-[var(--eds-text-muted)]"> — {a.role}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {isHome ? (
        <>
          <div className="flex flex-col gap-3">
            <UnifiedIntentBar verticalId={vertical.id} showQuickHints showRecent />
            <div className="flex flex-wrap items-center gap-2">
              <Link to={vertical.primaryAction.route}>
                <Button className="ews-primary-cta">{vertical.primaryAction.label}</Button>
              </Link>
              <Button variant="secondary" onClick={() => setCreateOpen(true)}>
                Создать…
              </Button>
            </div>
          </div>

          <section>
            <h2 className="eds-type-section mb-2">Быстрые действия</h2>
            <div className="flex flex-wrap gap-2">
              {vertical.quickActions.map((a) => (
                <Link key={a.label + a.route} to={a.route}>
                  <Button variant="secondary">{a.label}</Button>
                </Link>
              ))}
            </div>
          </section>

          <section className="grid gap-3 sm:grid-cols-3">
            {vertical.stats.map((s) => (
              <Card key={s.label} title={s.label}>
                <p className="eds-type-title text-2xl">{s.value}</p>
              </Card>
            ))}
          </section>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Последние объекты">
              <ul className="space-y-2 eds-type-small">
                {vertical.recentObjects.map((o) => (
                  <li key={o.title}>
                    {o.route ? (
                      <Link to={o.route} className="font-medium text-[var(--eds-accent)]">
                        {o.title}
                      </Link>
                    ) : (
                      <span className="font-medium">{o.title}</span>
                    )}
                    <p className="text-[var(--eds-text-muted)]">{o.detail}</p>
                  </li>
                ))}
              </ul>
            </Card>
            <Card title="Уведомления и события">
              <ul className="space-y-2 eds-type-small">
                {vertical.events.map((e) => (
                  <li key={e.title}>
                    <span className="font-medium">{e.title}</span>
                    <p className="text-[var(--eds-text-muted)]">{e.detail}</p>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Задачи">
              <ul className="space-y-2 eds-type-small">
                {vertical.tasks.map((t) => (
                  <li key={t.title} className="flex justify-between gap-2">
                    <span>{t.title}</span>
                    <Badge>{t.status}</Badge>
                  </li>
                ))}
              </ul>
            </Card>
            <Card title="Рекомендации">
              <ul className="list-disc space-y-1 pl-5 eds-type-small">
                {vertical.recommendations.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
              <p className="mt-3 eds-type-helper">
                Следующий шаг:{" "}
                <Link
                  to={vertical.primaryAction.route}
                  className="font-medium text-[var(--eds-accent)]"
                >
                  {vertical.primaryAction.label}
                </Link>
              </p>
            </Card>
          </div>

          <Card title="AI-агенты вертикали">
            <p className="eds-type-helper mb-2">
              Консьерж общий для всей платформы. Ниже — специалисты этой вертикали.
            </p>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {vertical.agents.map((a) => (
                <div
                  key={a.id}
                  className="rounded-md border border-[var(--ew-border)] p-3 eds-type-small"
                >
                  <p className="font-semibold">{a.name}</p>
                  <p className="text-[var(--eds-text-muted)]">{a.role}</p>
                </div>
              ))}
            </div>
          </Card>
        </>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Рекомендации по разделу">
            <ul className="list-disc space-y-1 pl-5 eds-type-small">
              {vertical.recommendations.slice(0, 3).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </Card>
          <Card title="Специалисты">
            <ul className="space-y-1 eds-type-small">
              {specialists.map((a) => (
                <li key={a.id}>
                  {a.name} — {a.role}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      )}

      <ContextualAiChat
        open={aiOpen}
        onClose={() => setAiOpen(false)}
        verticalId={vertical.id}
      />
      <QuickCreatePanel open={createOpen} onClose={() => setCreateOpen(false)} />
    </div>
  );
}
