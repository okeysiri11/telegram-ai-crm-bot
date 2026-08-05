/**
 * Sprint 30.3 / 31.1 — City preview strip → live Enterprise City (no placeholder map).
 */

import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { CITY_DISTRICTS } from "./cityDistricts";
import { CITY_BUILDINGS } from "./cityCatalog";

export function CityPreviewPanel() {
  const districts = CITY_DISTRICTS.slice(0, 6);
  const stats = [
    { label: "Районы", value: String(CITY_DISTRICTS.length) },
    { label: "Здания", value: String(CITY_BUILDINGS.length) },
    { label: "Карта", value: "live" },
    { label: "Навигация", value: "pan · zoom" },
  ];

  return (
    <div className="space-y-4 edm-page-soft" data-testid="city-preview-panel">
      <Card title="Enterprise City" status={<Badge tone="success">live</Badge>}>
        <p className="eds-type-helper mb-3">
          Интерактивная карта модулей: pan · zoom · hover · клик · мини-карта · Owner God Mode.
        </p>
        <Link
          to="/city"
          className="relative mb-4 block overflow-hidden rounded-lg border border-[var(--ew-border)] transition-[border-color,box-shadow] hover:border-[var(--eds-primary)]"
          style={{
            minHeight: 160,
            background:
              "linear-gradient(135deg, color-mix(in srgb, var(--eds-primary) 14%, transparent), color-mix(in srgb, var(--eds-surface) 80%, var(--ew-border)))",
          }}
          aria-label="Открыть Enterprise City"
        >
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <p className="eds-type-h3">Открыть город →</p>
              <p className="eds-type-helper">Здания ведут в реальные модули платформы</p>
            </div>
          </div>
          <div className="absolute bottom-2 right-2 flex flex-wrap justify-end gap-1">
            {stats.map((s) => (
              <Badge key={s.label} tone="success">
                {s.label}: {s.value}
              </Badge>
            ))}
          </div>
        </Link>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {districts.map((d) => (
            <Link
              key={d.id}
              to={`/city?district=${d.id}`}
              className="rounded-md border border-[var(--ew-border)] px-3 py-2 hover:border-[var(--eds-primary)]"
            >
              <p className="font-medium eds-type-small">{d.labelRu || d.label}</p>
              <p className="eds-type-helper">{d.id}</p>
            </Link>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-3">
          <Link className="text-[var(--eds-primary)] eds-type-small" to="/city">
            Интерактивная карта →
          </Link>
          <Link className="text-[var(--eds-primary)] eds-type-small" to="/city-visualization">
            Инспектор визуализации →
          </Link>
          <Link className="text-[var(--eds-primary)] eds-type-small" to="/dashboard">
            На главную →
          </Link>
        </div>
      </Card>
    </div>
  );
}
