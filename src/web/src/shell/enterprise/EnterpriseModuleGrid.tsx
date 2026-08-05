import { Link } from "react-router-dom";
import { Button } from "@/ui";
import { ShellIcon } from "@/shell/enterprise/ShellIcons";
import type { ShellIconId } from "@/shell/enterprise/enterpriseNav";
import {
  ENTERPRISE_MODULE_CARDS,
  type EnterpriseModuleCard,
} from "@/dashboard/enterpriseModuleCards";
import { rememberNavDecision, withDecisionQuery } from "@/decision-flow";
import { telemetry } from "@/integrations/telemetry";

function iconFor(card: EnterpriseModuleCard): ShellIconId {
  return card.icon;
}

export function EnterpriseModuleGrid({ cards = ENTERPRISE_MODULE_CARDS }: { cards?: EnterpriseModuleCard[] }) {
  return (
    <div className="ews-modules edm-stagger" data-testid="enterprise-module-grid">
      {cards.map((m) => (
        <article key={m.id} className="ews-module-card ews-glass">
          <div className="ews-module-card-top">
            <span className="ews-module-icon" aria-hidden>
              <ShellIcon id={iconFor(m)} />
            </span>
            <div className="min-w-0">
              <h3 className="ews-module-title">{m.label}</h3>
              <p className="eds-type-helper">{m.description}</p>
            </div>
          </div>
          <dl className="ews-module-stats">
            {m.stats.map((s) => (
              <div key={s.label}>
                <dt>{s.label}</dt>
                <dd>{s.value}</dd>
              </div>
            ))}
          </dl>
          <Link
            to={withDecisionQuery(m.route, { from: "/dashboard", step: "act", focus: m.id })}
            onClick={() => {
              rememberNavDecision("/dashboard", m.route, m.label, "act");
              void telemetry.userActivity(`module_open:${m.id}`);
            }}
          >
            <Button size="sm" className="w-full edm-press">
              Open {m.label}
            </Button>
          </Link>
        </article>
      ))}
    </div>
  );
}
