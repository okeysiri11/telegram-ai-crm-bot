/** Полоска студии AI-конструктора — Sprint 42.5 RU. */

import { Link } from "react-router-dom";
import { Badge } from "@/ui";
import { telemetry } from "@/integrations/telemetry";
import { studioCatalogStats } from "./studioCatalog";

export function AIBuilderStudioStrip() {
  const stats = studioCatalogStats();
  return (
    <div className="abs-strip" aria-label="Студия AI-конструктора">
      <span className="abs-strip-label">Конструктор</span>
      <Badge>{stats.skills} навыков</Badge>
      <Badge>{stats.workflows} сцен.</Badge>
      <Badge>{stats.templates} шабл.</Badge>
      <Link
        to="/platform-builder/builder-studio"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open")}
      >
        Студия →
      </Link>
      <Link
        to="/automation"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_automation")}
      >
        Автоматизация →
      </Link>
      <Link
        to="/business-network"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_ebn")}
      >
        Сеть →
      </Link>
      <Link
        to="/digital-citizens"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_citizens")}
      >
        Граждане →
      </Link>
      <Link
        to="/life-engine"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_life")}
      >
        Жизнь →
      </Link>
      <Link
        to="/assets"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_assets")}
      >
        Ресурсы →
      </Link>
      <Link
        to="/spatial"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_spatial")}
      >
        Пространство →
      </Link>
      <Link
        to="/city-visualization"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_city_viz")}
      >
        Визуализация →
      </Link>
      <Link
        to="/interactions"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_interactions")}
      >
        Взаимодействия →
      </Link>
      <Link
        to="/intelligence"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_intelligence")}
      >
        Интеллект →
      </Link>
      <Link
        to="/orchestrator"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_orchestrator")}
      >
        Оркестратор →
      </Link>
      <Link
        to="/kernel"
        className="eds-type-small text-[var(--eds-primary)]"
        onClick={() => void telemetry.userActivity("abs_open_kernel")}
      >
        Ядро →
      </Link>
    </div>
  );
}
