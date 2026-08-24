/**
 * Ukraine oblast choropleth from simplified OSM geometry.
 * Fill encodes the selected agro/weather layer — never decorative.
 */

import { useMemo, useState } from "react";
import { UKRAINE_MAP_VIEWBOX, UKRAINE_OBLAST_PATHS, projectUkraine } from "./data/ukraineOblastPaths";
import { UKRAINE_REGIONS } from "./data/ukraineRegions";

export type WeatherLayer = "agro_risk" | "temperature" | "precip" | "humidity" | "wind" | "drought" | "frost";

type OblastRow = {
  id?: string;
  label_ru?: string;
  macro?: string;
  temperature?: number | null;
  precip_7?: number | null;
  humidity?: number | null;
  wind_speed?: number | null;
  tmin?: number | null;
  agro_risk?: { level?: string | null; label_ru?: string; missing?: boolean };
  missing?: boolean;
  has_data?: boolean;
};

const MACRO_STROKE: Record<string, string> = {
  south: "#2bb894",
  center: "#3ecfad",
  west: "#5b8def",
  north: "#8fb0d8",
  east: "#d97706",
};

function clamp(n: number, a: number, b: number) {
  return Math.max(a, Math.min(b, n));
}

function lerpColor(t: number, from: [number, number, number], to: [number, number, number]) {
  const x = clamp(t, 0, 1);
  const c = from.map((v, i) => Math.round(v + (to[i] - v) * x));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

function riskFill(level?: string | null, missing?: boolean) {
  if (missing || !level) return "#1a2740";
  if (level === "Low") return "#1a7f4c";
  if (level === "Medium") return "#c9a227";
  if (level === "High") return "#c2410c";
  return "#1a2740";
}

export function layerFill(layer: WeatherLayer, row?: OblastRow | null) {
  if (!row || row.missing) return "#1a2740";
  const risk = row.agro_risk;
  if (layer === "agro_risk") return riskFill(risk?.level, risk?.missing);
  if (layer === "temperature") {
    if (row.temperature == null) return "#1a2740";
    const t = (Number(row.temperature) - 8) / 28;
    return lerpColor(t, [37, 99, 140], [196, 64, 28]);
  }
  if (layer === "precip") {
    if (row.precip_7 == null) return "#1a2740";
    const t = Number(row.precip_7) / 40;
    return lerpColor(t, [30, 58, 72], [56, 189, 248]);
  }
  if (layer === "humidity") {
    if (row.humidity == null) return "#1a2740";
    const t = Number(row.humidity) / 100;
    return lerpColor(t, [120, 80, 40], [45, 180, 160]);
  }
  if (layer === "wind") {
    if (row.wind_speed == null) return "#1a2740";
    const t = Number(row.wind_speed) / 14;
    return lerpColor(t, [30, 64, 80], [14, 165, 164]);
  }
  if (layer === "drought") {
    if (row.precip_7 == null && row.temperature == null) return "#1a2740";
    const dry = row.precip_7 != null && row.precip_7 < 8 && (row.temperature || 0) >= 28;
    if (dry) return "#c2410c";
    if (row.precip_7 != null && row.precip_7 < 12) return "#c9a227";
    return "#1a7f4c";
  }
  if (layer === "frost") {
    if (row.tmin == null) return "#1a2740";
    if (row.tmin <= 0) return "#7c3aed";
    if (row.tmin <= 2) return "#6366f1";
    return "#1a7f4c";
  }
  return "#1a2740";
}

export function AgroUkraineMap(props: {
  oblasts: OblastRow[];
  layer: WeatherLayer;
  selectedId?: string | null;
  selectedMacro?: string | null;
  onSelect: (oblastId: string) => void;
  loading?: boolean;
}) {
  const [hover, setHover] = useState<string | null>(null);
  const byId = useMemo(() => {
    const m = new Map<string, OblastRow>();
    for (const row of props.oblasts) {
      if (row.id) m.set(String(row.id), row);
    }
    return m;
  }, [props.oblasts]);
  const tip = hover ? byId.get(hover) : null;
  const tipPath = hover ? UKRAINE_OBLAST_PATHS.find((p) => p.id === hover) : null;

  return (
    <div className="agro-wx-map-wrap" data-testid="agro-weather-map">
      {props.loading ? <div className="agro-wx-map-skel" data-testid="agro-weather-map-loading" /> : null}
      <svg viewBox={UKRAINE_MAP_VIEWBOX} className="agro-wx-map" role="img" aria-label="Карта Украины">
        <rect width="920" height="620" fill="#0b1220" />
        {UKRAINE_OBLAST_PATHS.map((feat) => {
          const row = byId.get(feat.id);
          const selected = props.selectedId === feat.id || (props.selectedMacro && feat.macro === props.selectedMacro);
          const active = hover === feat.id || selected;
          return (
            <path
              key={feat.id}
              d={feat.d}
              fill={layerFill(props.layer, row)}
              stroke={active ? "#e8eef7" : MACRO_STROKE[feat.macro] || "#3ecfad"}
              strokeWidth={active ? 2.4 : 1}
              className="agro-wx-oblast"
              opacity={props.selectedMacro && feat.macro !== props.selectedMacro && props.selectedId !== feat.id ? 0.55 : 1}
              data-testid={`agro-weather-oblast-${feat.id}`}
              onMouseEnter={() => setHover(feat.id)}
              onMouseLeave={() => setHover((h) => (h === feat.id ? null : h))}
              onClick={() => props.onSelect(feat.id)}
            />
          );
        })}
        <g className="agro-wx-labels" pointerEvents="none" aria-hidden="true">
          {UKRAINE_REGIONS.map((region) => {
            const feat = UKRAINE_OBLAST_PATHS.find((p) => p.id === region.id);
            if (!feat) return null;
            const [ldx, ldy] = region.labelOffset || [0, 0];
            const x = feat.cx + ldx;
            const y = feat.cy + ldy;
            const active = hover === region.id || props.selectedId === region.id;
            return (
              <text
                key={`label-${region.id}`}
                x={x}
                y={y}
                textAnchor="middle"
                className={`agro-wx-region-label${active ? " is-active" : ""}`}
                data-testid={`agro-weather-region-label-${region.id}`}
              >
                {region.regionLines.map((line, i) => (
                  <tspan key={line} x={x} dy={i === 0 ? 0 : 12}>
                    {line}
                  </tspan>
                ))}
              </text>
            );
          })}
        </g>
        <g className="agro-wx-capitals" pointerEvents="none" aria-hidden="true">
          {UKRAINE_REGIONS.map((region) => {
            const pt = projectUkraine(region.capitalLon, region.capitalLat);
            const [cdx, cdy] = region.capitalLabelOffset || [8, 3];
            const active = hover === region.id || props.selectedId === region.id;
            return (
              <g key={`cap-${region.id}`} data-testid={`agro-weather-capital-${region.id}`}>
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={active ? 3.6 : 3.1}
                  className={`agro-wx-capital-dot${active ? " is-active" : ""}`}
                />
                <text
                  x={pt.x + cdx}
                  y={pt.y + cdy}
                  className="agro-wx-capital-name"
                  data-testid={`agro-weather-capital-name-${region.id}`}
                >
                  {region.capitalName}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
      {tip && tipPath ? (
        <div
          className="agro-wx-tooltip"
          data-testid="agro-weather-tooltip"
          style={{ left: `${(tipPath.cx / 920) * 100}%`, top: `${(tipPath.cy / 620) * 100}%` }}
        >
          <div className="font-medium">{String(tip.label_ru || tipPath.label_ru)}</div>
          <div>Температура: {tip.temperature != null ? `${tip.temperature > 0 ? "+" : ""}${tip.temperature}°C` : "нет данных"}</div>
          <div>Осадки 7 дней: {tip.precip_7 != null ? `${tip.precip_7} мм` : "нет данных"}</div>
          <div>Влажность: {tip.humidity != null ? `${tip.humidity}%` : "нет данных"}</div>
          <div>Ветер: {tip.wind_speed != null ? `${tip.wind_speed} м/с` : "нет данных"}</div>
          <div>Риск засухи: {tip.precip_7 != null && tip.precip_7 < 8 && (tip.temperature || 0) >= 28 ? "высокий" : tip.precip_7 == null ? "нет данных" : "низкий"}</div>
          <div>Агро-риск: {String(tip.agro_risk?.label_ru || "нет данных")}</div>
        </div>
      ) : null}
    </div>
  );
}
