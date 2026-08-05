/**
 * Persistent “what next?” strip — EP-06.
 * Shows one concrete continue action; no new Engine.
 */

import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/ui";
import { DECISION_CHAIN, readDecisionContext, rememberNavDecision, resolveContinue } from "./decisionFlow";
import { telemetry } from "@/integrations/telemetry";

export function DecisionContinueBar() {
  const loc = useLocation();
  const ctx = readDecisionContext();
  const next = useMemo(() => resolveContinue(loc.pathname, ctx), [loc.pathname, ctx, loc.key]);

  if (!next) return null;

  const stepMeta = DECISION_CHAIN[next.chainIndex] || DECISION_CHAIN[0];

  return (
    <div className="df-continue edm-page-soft" role="navigation" aria-label="Continue decision">
      <div className="df-continue-meta">
        <span className="eds-quiet-label">Next decision · {stepMeta.label}</span>
        <p className="df-continue-why">{next.why}</p>
      </div>
      <div className="df-continue-chain" aria-hidden>
        {DECISION_CHAIN.map((s, i) => (
          <span key={s.step} className={`df-step${i <= next.chainIndex ? " is-on" : ""}`} />
        ))}
      </div>
      <Link
        to={next.route}
        onClick={() => {
          rememberNavDecision(loc.pathname, next.route, next.why, next.step);
          void telemetry.userActivity(`decision_continue:${next.step}`);
        }}
      >
        <Button size="sm">{next.cta}</Button>
      </Link>
    </div>
  );
}
