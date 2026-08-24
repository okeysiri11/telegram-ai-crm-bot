import { Card } from "@/ui";

type Coverage = {
  connected_sources?: number;
  numeric_observations?: number;
  metadata_observations?: number;
  observations_last_24h?: number;
  coverage_pct?: number;
  confidence_pct?: number;
  unresolved_gaps?: number;
};

export function AgroCoverageCard(props: { coverage?: Coverage | null }) {
  const c = props.coverage || {};
  return (
    <Card title="Покрытие данных">
      <div className="eds-type-small grid gap-1" data-testid="agro-coverage-card">
        <div>Источников подключено: {Number(c.connected_sources || 0)}</div>
        <div>Реальных наблюдений: {Number(c.numeric_observations || 0)}</div>
        <div>Метаданных: {Number(c.metadata_observations || 0)}</div>
        <div>Данные за последние 24 часа: {Number(c.observations_last_24h || 0)}</div>
        <div>
          Coverage:
          <div>{Number(c.coverage_pct || 0)}%</div>
        </div>
        <div>
          Confidence:
          <div>{Number(c.confidence_pct || 0)}%</div>
        </div>
        <div>
          Unresolved gaps:
          <div>{Number(c.unresolved_gaps || 0)}</div>
        </div>
      </div>
    </Card>
  );
}
