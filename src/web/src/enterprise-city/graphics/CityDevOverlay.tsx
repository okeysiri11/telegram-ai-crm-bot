/**
 * Enterprise City Graphics Engine — Developer Overlay.
 * Sprint CG-3. Renders the `debug` render layer (off by default, per `layerSystem.ts`'s
 * `DEFAULT_LAYERS`) — real, live numbers read from the Graphics Engine's own render pipeline and
 * performance monitor, not placeholder text. Presentation only: no business logic, no store.
 */

import type { GraphicsQuality, GraphicsSettings } from "./types";
import type { PerformanceSnapshot } from "./performanceMonitor";

const QUALITY_TIERS: GraphicsQuality[] = ["low", "medium", "high", "ultra"];

export function CityDevOverlay({
  perf,
  objects,
  visibleBuildings,
  animationQueueLength,
  settings,
  onQualityChange,
  onClose,
}: {
  perf: PerformanceSnapshot;
  objects: number;
  visibleBuildings: number;
  animationQueueLength: number;
  settings: GraphicsSettings;
  onQualityChange: (quality: GraphicsQuality) => void;
  onClose: () => void;
}) {
  const fpsTone = perf.fps === 0 ? "var(--eds-text-muted)" : perf.fps >= 50 ? "var(--eds-success)" : perf.fps >= 30 ? "var(--eds-warning)" : "var(--eds-danger)";

  return (
    <div
      className="ews-glass"
      role="region"
      aria-label="City graphics developer overlay"
      style={{
        position: "fixed",
        right: "1rem",
        bottom: "1rem",
        zIndex: 80,
        width: "15rem",
        padding: "0.75rem",
        borderRadius: "0.75rem",
        fontSize: "0.72rem",
        lineHeight: 1.5,
        fontVariantNumeric: "tabular-nums",
      }}
    >
      <div className="flex items-center justify-between mb-1">
        <strong className="eds-type-caption uppercase tracking-[0.14em]">Graphics Debug</strong>
        <button type="button" onClick={onClose} aria-label="Close developer overlay" style={{ opacity: 0.7 }}>
          ✕
        </button>
      </div>
      <dl className="grid grid-cols-2 gap-x-2 gap-y-0.5">
        <dt className="opacity-60">FPS</dt>
        <dd style={{ color: fpsTone, fontWeight: 600 }}>{perf.fps.toFixed(0)}</dd>
        <dt className="opacity-60">Objects</dt>
        <dd>{objects}</dd>
        <dt className="opacity-60">Visible buildings</dt>
        <dd>{visibleBuildings}</dd>
        <dt className="opacity-60">Animation queue</dt>
        <dd>{animationQueueLength}</dd>
        <dt className="opacity-60">Memory</dt>
        <dd>{perf.memoryMb != null ? `${perf.memoryMb.toFixed(1)} MB` : "n/a"}</dd>
        <dt className="opacity-60">CPU time</dt>
        <dd>{perf.cpuTimeMs.toFixed(2)} ms</dd>
        <dt className="opacity-60">Render time</dt>
        <dd>{perf.renderTimeMs.toFixed(2)} ms</dd>
      </dl>
      <div className="mt-2 flex items-center justify-between">
        <span className="opacity-60">Quality</span>
        <select
          aria-label="Graphics quality"
          value={settings.quality}
          onChange={(e) => onQualityChange(e.target.value as GraphicsQuality)}
          style={{ fontSize: "0.7rem", background: "transparent", border: "1px solid var(--eds-border)", borderRadius: "0.35rem" }}
        >
          {QUALITY_TIERS.map((tier) => (
            <option key={tier} value={tier}>
              {tier}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
