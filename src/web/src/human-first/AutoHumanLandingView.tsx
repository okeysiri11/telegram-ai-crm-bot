/**
 * Sprint 42.3 — Human-First Auto landing: one screen, one primary action, AI-first.
 */

import { Link } from "react-router-dom";
import { Button, Card } from "@/ui";
import type { ModuleLandingDef } from "@/modules/moduleLandingCatalog";
import { SimpleProModeToggle, useExperienceModeStore } from "@/ux-revolution";
import { HumanAiCommandBar } from "./HumanAiCommandBar";

const SIMPLE_QUICK: Array<{ label: string; route: string; primary?: boolean }> = [
  { label: "Добавить автомобиль", route: "/workspace/auto?action=vehicle", primary: true },
  { label: "Автомобили", route: "/workspace/auto?view=cars" },
  { label: "Клиенты", route: "/workspace/auto?view=clients" },
  { label: "Продажи", route: "/workspace/auto?view=sales" },
  { label: "Импорт", route: "/workspace/auto?view=import" },
  { label: "Склад", route: "/workspace/auto?view=warehouse" },
];

export function AutoHumanLandingView({ landing }: { landing: ModuleLandingDef }) {
  const mode = useExperienceModeStore((s) => s.mode);
  const isSimple = mode === "simple";

  return (
    <div
      className="hf-auto-landing space-y-4"
      data-testid="landing-auto"
      data-human-first="1"
      data-experience-mode={mode}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="eds-type-caption text-[var(--eds-text-muted)]">Авто · дилерское пространство</p>
        <SimpleProModeToggle />
      </div>

      <HumanAiCommandBar moduleId="auto" />

      {/* Unified orientation card — replaces welcome + hero + next duplicates */}
      <header
        className="hf-unified-hero ews-glass rounded-xl border border-[var(--ew-border)] p-5"
        data-testid="action-header"
      >
        <h1 className="eds-type-title text-2xl lg:text-3xl">{landing.title}</h1>
        <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">{landing.description}</p>
        <p className="mt-3 eds-type-helper">
          <span className="font-medium">Что можно делать: </span>
          {SIMPLE_QUICK.map((a) => a.label).join(" · ")}
        </p>
        <p className="mt-1 eds-type-helper">
          <span className="font-medium">Дальше: </span>
          {landing.nextStep}
        </p>
        <div className="mt-4">
          <Link to={landing.primaryAction.route}>
            <Button className="ews-primary-cta" size="lg" data-testid="primary-cta">
              {landing.primaryAction.label}
            </Button>
          </Link>
        </div>
      </header>

      {/* Compact AI guide */}
      <Card className="hf-ai-guide border-[var(--eds-success)]" data-testid="ai-guide">
        <p className="eds-type-body font-medium">{landing.aiGuide.greeting}</p>
        <p className="mt-1 eds-type-helper">Сегодня:</p>
        <ul className="mt-1 list-disc space-y-0.5 pl-5 eds-type-body">
          {landing.aiGuide.bullets.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
        <p className="mt-3 eds-type-body">
          Рекомендуем: {landing.aiRecommendation}
        </p>
        <div className="mt-3">
          <Link to={landing.aiGuide.recommendedAction.route}>
            <Button className="ews-primary-cta" size="sm" data-testid="ai-fix-cta">
              {landing.aiGuide.recommendedAction.label}
            </Button>
          </Link>
        </div>
      </Card>

      <section className="hf-quick-actions" data-testid="auto-quick-actions">
        <h2 className="eds-type-section mb-2">Быстрые действия</h2>
        <div className="flex flex-wrap gap-2">
          {SIMPLE_QUICK.map((a) => (
            <Link key={a.route + a.label} to={a.route}>
              <Button
                className={a.primary ? "ews-primary-cta" : undefined}
                variant={a.primary ? undefined : "secondary"}
              >
                {a.label}
              </Button>
            </Link>
          ))}
        </div>
      </section>

      {!isSimple ? (
        <div className="eds-grid eds-grid--dashboard" data-testid="auto-pro-panels">
          <Card title="Статистика">
            <div className="flex flex-wrap gap-3">
              {landing.stats.map((s) => (
                <div key={s.label} className="rounded-md border border-[var(--ew-border)] px-3 py-2 min-w-[5rem]">
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{s.label}</p>
                  <p className="eds-type-title text-xl">{s.value}</p>
                </div>
              ))}
            </div>
          </Card>
          <Card title="Недавние">
            <ul className="space-y-2">
              {landing.recentObjects.map((r, i) => (
                <li key={`${r.title}-${i}`}>
                  {r.route ? (
                    <Link to={r.route} className="block rounded-md border border-[var(--ew-border)] px-3 py-2">
                      <span className="font-medium eds-type-small">{r.title}</span>
                      <span className="block eds-type-helper">{r.detail}</span>
                    </Link>
                  ) : (
                    <span className="eds-type-small">{r.title}</span>
                  )}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
