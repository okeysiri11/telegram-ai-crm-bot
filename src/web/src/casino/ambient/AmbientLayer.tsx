import type { PerformanceTier } from "../hooks/usePerformanceTier";

export function AmbientLayer({ tier }: { tier: PerformanceTier }) {
  if (tier === "LOW") return null;
  return (
    <div className={`op-ambient is-${tier.toLowerCase()}`} data-testid="casino-ambient" aria-hidden>
      <span className="op-light-sweep" />
      <span className="op-reflect" />
      {tier === "HIGH" ? (
        <>
          <span className="op-bokeh" />
          <span className="op-bokeh is-2" />
          <span className="op-dust" />
          <span className="op-fog is-ambient" />
          <span className="op-silhouettes" />
        </>
      ) : (
        <>
          <span className="op-fog is-ambient" />
          <span className="op-silhouettes is-static" />
        </>
      )}
    </div>
  );
}
