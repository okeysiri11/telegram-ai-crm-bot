/**
 * Sprint 41.3 — first-visit onboarding card per module (dismiss forever).
 */

import { useState } from "react";
import { Link } from "react-router-dom";
import { Button, Card } from "@/ui";
import type { ModuleLandingDef } from "./moduleLandingCatalog";
import { useI18n } from "@/i18n";

const KEY = "ewp_module_welcome_dismissed_v1";

function readDismissed(): Set<string> {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return new Set();
    return new Set(JSON.parse(raw) as string[]);
  } catch {
    return new Set();
  }
}

function writeDismissed(ids: Set<string>) {
  try {
    localStorage.setItem(KEY, JSON.stringify([...ids]));
  } catch {
    /* ignore */
  }
}

export function ModuleWelcomeCard({
  moduleId,
  landing,
}: {
  moduleId: string;
  landing: ModuleLandingDef;
}) {
  const t = useI18n((s) => s.t);
  const [hidden, setHidden] = useState(() => readDismissed().has(moduleId));

  if (hidden) return null;

  function dismiss() {
    const next = readDismissed();
    next.add(moduleId);
    writeDismissed(next);
    setHidden(true);
  }

  return (
    <Card title={t("welcome.title")} className="ews-welcome-card border-[var(--eds-primary)]">
      <p className="eds-type-body">
        {t("welcome.allows")} <strong>{landing.title}</strong>: {landing.description}
      </p>
      <p className="mt-2 eds-type-helper">
        {t("welcome.firstAction")}: {landing.primaryAction.label}
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to={landing.primaryAction.route}>
          <Button className="ews-primary-cta" size="sm">
            {landing.primaryAction.label}
          </Button>
        </Link>
        <Link to="/knowledge">
          <Button size="sm" variant="secondary">
            {t("welcome.docs")}
          </Button>
        </Link>
        <Link to="/knowledge?view=guide">
          <Button size="sm" variant="ghost">
            {t("welcome.guide")}
          </Button>
        </Link>
        <Link to={landing.primaryAction.route}>
          <Button size="sm" variant="secondary">
            {t("welcome.create")}
          </Button>
        </Link>
        <Button size="sm" variant="ghost" onClick={dismiss}>
          {t("welcome.dismiss")}
        </Button>
      </div>
    </Card>
  );
}
