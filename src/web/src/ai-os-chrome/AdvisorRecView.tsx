/**
 * Compact Executive Advisor recommendation card — EP-04.
 * Observation · Why · Action · Impact · quiet confidence.
 */

import { Badge } from "@/ui";
import { confidenceBadgeTone, confidenceShort, toneChip, type AdvisorRecommendation } from "./aiPersonality";

export function AdvisorRecView({
  rec,
  compact = false,
}: {
  rec: AdvisorRecommendation;
  compact?: boolean;
}) {
  return (
    <div className={`ai-advisor-rec${compact ? " is-compact" : ""}`}>
      <div className="ai-advisor-rec-top">
        <Badge>{toneChip(rec.tone)}</Badge>
        <Badge tone={confidenceBadgeTone(rec.confidence)}>{confidenceShort(rec.confidence)}</Badge>
      </div>
      <p className="ai-advisor-obs">{rec.observation}</p>
      {!compact ? <p className="ai-advisor-why">{rec.why}</p> : null}
      <p className="ai-advisor-action">{rec.action}</p>
      <p className="ai-advisor-impact">Impact: {rec.impact}</p>
    </div>
  );
}
