/**
 * Enterprise Demo Scenario — Sprint 32.3.5.
 * Guided path across existing routes only.
 */

import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card } from "@/ui";
import { DEMO_SCENARIO_STEPS } from "./demoScenarioCatalog";

export function DemoScenarioPage() {
  return (
    <WorkspaceLayout>
      <div className="demo-scenario eds-anim-page">
        <header className="demo-header">
          <p className="eds-type-caption uppercase tracking-[0.16em] text-[var(--eds-text-muted)]">
            Enterprise Demo
          </p>
          <h1 className="text-2xl font-semibold tracking-tight lg:text-3xl">Демонстрационный сценарий</h1>
          <p className="mt-2 max-w-2xl eds-type-small text-[var(--eds-text-muted)]">
            Плавный путь First Entry → Dashboard → Mission Control → City → AI → CRM и обратно. Все экраны —
            существующие маршруты платформы.
          </p>
        </header>

        <ol className="demo-steps">
          {DEMO_SCENARIO_STEPS.map((step, i) => (
            <li key={step.id} className="demo-step eds-anim-slide" style={{ animationDelay: `${i * 40}ms` }}>
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

        <Card title="Быстрый старт Executive" className="mt-6">
          <p className="mb-3 eds-type-small text-[var(--eds-text-muted)]">
            Режим руководителя открывает KPI, health, AI и рекомендации на одном экране Dashboard.
          </p>
          <div className="flex flex-wrap gap-2">
            <Link to="/dashboard?mode=executive">
              <Button size="sm">Открыть Executive Mode</Button>
            </Link>
            <Link to="/dashboard?mode=full">
              <Button size="sm" variant="secondary">
                Полный Command Center
              </Button>
            </Link>
            <Link to="/onboarding/first-entry">
              <Button size="sm" variant="secondary">
                Пройти First Entry
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
