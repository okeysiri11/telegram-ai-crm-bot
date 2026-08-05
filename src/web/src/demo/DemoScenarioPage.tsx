/**
 * Enterprise Demo Scenario — Sprint 32.3.5 / EP-08 / 30.6 Live Demo.
 * Guided commercial + Beta live path across existing routes only.
 */

import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card } from "@/ui";
import { DEMO_SCENARIO_STEPS, GA_DEMO_VALUE } from "./demoScenarioCatalog";
import { BETA_LIVE_DEMO_STEPS, BETA_LIVE_DEMO_META } from "@/platform-integration/betaLiveDemo";

export function DemoScenarioPage() {
  return (
    <WorkspaceLayout>
      <div className="demo-scenario edm-page" data-testid="live-demo">
        <header className="demo-header">
          <p className="eds-type-caption uppercase tracking-[0.16em] text-[var(--eds-text-muted)]">
            {BETA_LIVE_DEMO_META.product}
          </p>
          <h1 className="text-2xl font-semibold tracking-tight lg:text-3xl">Beta Live Demo</h1>
          <p className="mt-2 max-w-2xl eds-type-small text-[var(--eds-text-muted)]">
            {BETA_LIVE_DEMO_META.pitchRu} · {BETA_LIVE_DEMO_META.durationMin}–
            {BETA_LIVE_DEMO_META.durationMax} мин.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge tone="success">Sprint {BETA_LIVE_DEMO_META.sprint}</Badge>
            <Badge>Login</Badge>
            <Badge>City</Badge>
            <Badge>AI</Badge>
            <Badge>Production</Badge>
          </div>
        </header>

        <Card title="Сценарий живого демо" className="mt-4" raised>
          <ol className="demo-steps">
            {BETA_LIVE_DEMO_STEPS.map((step, i) => (
              <li key={step.id} className="demo-step edm-row-enter" style={{ animationDelay: `${i * 40}ms` }}>
                <div className="demo-step-index">{i + 1}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-semibold">{step.titleRu}</h2>
                    <Badge>{step.title}</Badge>
                  </div>
                  <p className="mt-1 eds-type-small text-[var(--eds-text-muted)]">{step.description}</p>
                </div>
                <Link to={step.route}>
                  <Button size="sm">{step.cta}</Button>
                </Link>
              </li>
            ))}
          </ol>
        </Card>

        <header className="demo-header mt-8">
          <p className="eds-type-caption uppercase tracking-[0.16em] text-[var(--eds-text-muted)]">
            {GA_DEMO_VALUE.product} · Extended path
          </p>
          <h2 className="text-xl font-semibold tracking-tight">Executive Demo Path</h2>
        </header>

        <ol className="demo-steps">
          {DEMO_SCENARIO_STEPS.map((step, i) => (
            <li key={step.id} className="demo-step edm-row-enter" style={{ animationDelay: `${i * 40}ms` }}>
              <div className="demo-step-index">{i + 1}</div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="font-semibold">{step.title}</h2>
                  <Badge>{step.duration}</Badge>
                </div>
                <p className="mt-1 eds-type-small text-[var(--eds-text-muted)]">{step.description}</p>
              </div>
              <Link to={step.route}>
                <Button size="sm">{step.cta}</Button>
              </Link>
            </li>
          ))}
        </ol>

        <Card title="Быстрый старт" className="mt-6" raised>
          <div className="flex flex-wrap gap-2">
            <Link to="/login">
              <Button size="sm">Вход</Button>
            </Link>
            <Link to="/dashboard">
              <Button size="sm" variant="secondary">
                Дашборд
              </Button>
            </Link>
            <Link to="/city">
              <Button size="sm" variant="secondary">
                Город
              </Button>
            </Link>
            <Link to="/ai-agents">
              <Button size="sm" variant="secondary">
                AI-центр
              </Button>
            </Link>
            <Link to="/production-studio">
              <Button size="sm" variant="secondary">
                Продакшн
              </Button>
            </Link>
            <Link to="/health">
              <Button size="sm" variant="ghost">
                Health
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
