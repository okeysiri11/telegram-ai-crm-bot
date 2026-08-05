/**
 * CEO Morning Experience — EP-01.
 * Answers in ~10 seconds: happening · attention · AI · risks · opportunities.
 * Presentation only over deriveMorningBrief (no new Engine).
 */

import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import type { BriefItem, MorningBrief } from "./deriveMorningBrief";
import { telemetry } from "@/integrations/telemetry";
import { deriveCeoPrimaryAction, pushDecisionContext, withDecisionQuery, CROSS_MODULE_FLOW, pathKey } from "@/decision-flow";

const TONE_BADGE: Record<MorningBrief["tone"], "success" | "warning" | "danger"> = {
  calm: "success",
  watch: "warning",
  alert: "danger",
};

function BriefCard({
  item,
  accent,
}: {
  item: BriefItem;
  accent?: "primary" | "muted";
}) {
  return (
    <Link
      to={item.route}
      className={`ex-brief-card${accent === "primary" ? " is-primary" : ""}`}
      onClick={() => void telemetry.userActivity(`morning_brief:${item.id}`)}
    >
      <div className="ex-brief-card-top">
        <Badge
          tone={
            item.tone === "alert" ? "danger" : item.tone === "watch" ? "warning" : item.tone === "opportunity" ? "success" : "default"
          }
        >
          {item.tone === "alert" ? "risk" : item.tone === "watch" ? "attention" : item.tone === "opportunity" ? "opportunity" : "ok"}
        </Badge>
        {item.confidence ? (
          <Badge tone={item.confidence === "high" ? "success" : item.confidence === "low" ? "warning" : "default"}>
            {item.confidence === "high" ? "High" : item.confidence === "medium" ? "Likely" : "Explore"}
          </Badge>
        ) : null}
      </div>
      <p className="ex-brief-what">{item.what}</p>
      <p className="ex-brief-why">{item.why}</p>
      <span className="ex-brief-next">{item.next} →</span>
      {item.impact ? <span className="ex-brief-impact">Impact: {item.impact}</span> : null}
    </Link>
  );
}

function Column({
  title,
  subtitle,
  items,
  primary,
}: {
  title: string;
  subtitle: string;
  items: BriefItem[];
  primary?: boolean;
}) {
  return (
    <section className={`ex-brief-col${primary ? " is-primary" : ""}`} aria-label={title}>
      <header className="ex-brief-col-head">
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </header>
      <div className="ex-brief-col-body">
        {items.map((item) => (
          <BriefCard key={item.id} item={item} accent={primary ? "primary" : "muted"} />
        ))}
      </div>
    </section>
  );
}

export function ExecutiveMorningBrief({
  brief,
  conciergeName,
}: {
  brief: MorningBrief;
  conciergeName?: string;
}) {
  const guide = conciergeName || "AI Concierge";
  const primary = deriveCeoPrimaryAction({
    tone: brief.tone,
    unread: brief.unread,
    healthBad: brief.healthOk < brief.healthTotal,
  });
  const primaryHref = withDecisionQuery(primary.route, { from: "/dashboard", step: primary.step, focus: brief.tone });

  return (
    <Card className="ex-morning" aria-label="CEO Morning Briefing">
      <header className="ex-morning-hero">
        <div>
          <p className="eds-type-caption uppercase tracking-[0.18em] text-[var(--eds-text-muted)]">
            Morning Briefing · Executive Advisor · {guide}
          </p>
          <h2 className="ex-morning-title">
            {brief.greeting}, {brief.company}
          </h2>
          <p className="ex-morning-summary">{brief.summaryLine}</p>
        </div>
        <div className="ex-morning-meta edm-stagger">
          <Badge tone={TONE_BADGE[brief.tone]}>
            {brief.tone === "calm" ? "Under control" : brief.tone === "watch" ? "Needs review" : "Action required"}
          </Badge>
          <Badge tone="success">
            Health {brief.healthOk}/{brief.healthTotal}
          </Badge>
          <Badge tone={brief.unread ? "warning" : "default"}>Notif {brief.unread}</Badge>
          <Link
            to={primaryHref}
            onClick={() => {
              const follow = CROSS_MODULE_FLOW[pathKey(primary.route)];
              pushDecisionContext({
                from: "/dashboard",
                step: primary.step,
                focus: brief.tone,
                label: primary.why,
                nextRoute: follow?.next || "/platform-builder/mission-control",
                nextCta: follow?.cta || "Confirm live health",
              });
              void telemetry.userActivity(`morning_primary:${primary.step}`);
            }}
          >
            <Button size="sm">{primary.cta}</Button>
          </Link>
        </div>
      </header>

      <div className="ex-morning-grid edm-stagger" role="group" aria-label="Five executive answers">
        <Column title="1 · Observation" subtitle="What is true now" items={brief.happening} />
        <Column title="2 · Attention" subtitle="Decide today" items={brief.attention} primary />
        <Column title="3 · Recommendation" subtitle="Advisor next actions" items={brief.aiActions} primary />
        <Column title="4 · Risks" subtitle="Where control slipped" items={brief.risks} />
        <Column title="5 · Opportunities" subtitle="Where value opened" items={brief.opportunities} />
      </div>

      <footer className="ex-morning-foot">
        <span className="eds-quiet-label">Decision chain</span>
        <Link
          to={withDecisionQuery("/platform-builder/control-tower", { from: "/dashboard", step: "decide" })}
          className="eds-type-small text-[var(--eds-primary)]"
          onClick={() =>
            pushDecisionContext({
              from: "/dashboard",
              step: "decide",
              label: "Owner decision in Control Tower",
              nextRoute: "/platform-builder/mission-control",
              nextCta: "Confirm live health",
            })
          }
        >
          Decide →
        </Link>
        <Link
          to={withDecisionQuery("/platform-builder/mission-control", { from: "/dashboard", step: "act" })}
          className="eds-type-small text-[var(--eds-primary)]"
        >
          Act in Mission Control →
        </Link>
        <Link to={withDecisionQuery("/enterprise-city", { from: "/dashboard", step: "observe" })} className="eds-type-small text-[var(--eds-primary)]">
          Observe City →
        </Link>
        <Link
          to={withDecisionQuery("/platform-builder/digital-twin", { from: "/dashboard", step: "understand" })}
          className="eds-type-small text-[var(--eds-primary)]"
        >
          Understand Twin →
        </Link>
        <Link
          to={withDecisionQuery("/platform-builder/concierge", { from: "/dashboard", step: "recommend" })}
          className="eds-type-small text-[var(--eds-primary)]"
        >
          Recommend with Advisor →
        </Link>
      </footer>
    </Card>
  );
}
