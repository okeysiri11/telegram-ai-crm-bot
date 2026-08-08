/**
 * Sprint 42.0 — guided module landing: never empty, AI guide, stats, action header.
 */

import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import type { ModuleLandingDef } from "./moduleLandingCatalog";
import { ModuleWelcomeCard } from "./ModuleWelcomeCard";
import { ModuleHelpIcon } from "@/help/ModuleHelpIcon";
import { useI18n } from "@/i18n";

export function ModuleLandingView({
  landing,
  forceEmpty = false,
}: {
  landing: ModuleLandingDef;
  /** Test / demo: treat as no data */
  forceEmpty?: boolean;
}) {
  const t = useI18n((s) => s.t);
  const hasData = !forceEmpty && (landing.recentObjects.length > 0 || landing.recent.length > 0);

  return (
    <div className="ews-module-landing space-y-4" data-testid={`landing-${landing.id}`}>
      <ModuleWelcomeCard moduleId={landing.id} landing={landing} />

      {/* Action header */}
      <header
        className="ews-module-hero ews-glass ews-hierarchy-header ews-action-header rounded-lg border border-[var(--ew-border)] p-4"
        data-testid="action-header"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="eds-type-caption text-[var(--eds-text-muted)]">{t("page.where")}</p>
            <h1 className="eds-type-title text-2xl lg:text-3xl">{landing.title}</h1>
            <p className="mt-1 font-medium">{landing.purpose}</p>
            <p className="mt-2 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
              {landing.description}
            </p>
            <p className="mt-2 eds-type-helper">
              <span className="font-medium">{t("page.actions")}: </span>
              {landing.actions.map((a) => a.label).join(" · ")}
            </p>
            <p className="eds-type-helper">
              <span className="font-medium">{t("landing.next")}: </span>
              {landing.nextStep}
            </p>
            <p className="eds-type-helper">
              <span className="font-medium">{t("page.time")}: </span>~{landing.estimatedMinutes}{" "}
              {t("common.minutes")}
            </p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex items-center gap-2">
              <Link to={landing.helpRoute} className="eds-type-caption text-[var(--eds-accent)]">
                {t("page.help")}
              </Link>
              <ModuleHelpIcon pathname={landing.route} />
            </div>
            <Link to={landing.primaryAction.route}>
              <Button className="ews-primary-cta" data-testid="primary-cta">
                {landing.primaryAction.label}
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* AI Guide */}
      <div data-testid="ai-guide">
        <Card title={t("landing.aiGuide")} className="ews-ai-guide border-[var(--eds-success)]">
          <Badge tone="success">{t("landing.aiBadge")}</Badge>
          <p className="mt-2 eds-type-body font-medium">{landing.aiGuide.greeting}</p>
          <p className="mt-1 eds-type-helper">{t("landing.aiToday")}</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 eds-type-body">
            {landing.aiGuide.bullets.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
          <p className="mt-3 eds-type-helper">
            <span className="font-medium">{t("landing.aiRecAction")}: </span>
            {landing.aiGuide.recommendedAction.label}
          </p>
          <div className="mt-3">
            <Link to={landing.aiGuide.recommendedAction.route}>
              <Button className="ews-primary-cta" size="sm">
                {landing.aiGuide.recommendedAction.label}
              </Button>
            </Link>
          </div>
        </Card>
      </div>

      <section className="ews-hierarchy-actions">
        <h2 className="eds-type-section mb-2">{t("landing.primaryActions")}</h2>
        <div className="flex flex-wrap gap-2">
          <Link to={landing.primaryAction.route}>
            <Button className="ews-primary-cta">{landing.primaryAction.label}</Button>
          </Link>
          {landing.actions.map((a) => (
            <Link key={a.route + a.label} to={a.route}>
              <Button variant="secondary">{a.label}</Button>
            </Link>
          ))}
        </div>
      </section>

      {!hasData ? (
        <div data-testid="empty-workspace">
          <Card title={t("empty.title")} className="ews-empty-workspace">
            <p className="eds-type-body">{t("empty.hint")}</p>
            <p className="mt-2 eds-type-helper">
              {t("welcome.firstAction")}: {landing.primaryAction.label}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Link to={landing.primaryAction.route}>
                <Button className="ews-primary-cta" size="sm">
                  {landing.primaryAction.label}
                </Button>
              </Link>
              <Link to={landing.emptyDemoRoute}>
                <Button size="sm" variant="secondary">
                  {t("empty.demo")}
                </Button>
              </Link>
              <Link to={landing.emptyTutorialRoute}>
                <Button size="sm" variant="ghost">
                  {t("empty.tutorial")}
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      ) : (
        <div className="eds-grid eds-grid--dashboard ews-hierarchy-content">
          <Card title={t("landing.stats")}>
            <div className="flex flex-wrap gap-3">
              {landing.stats.map((s) => (
                <div key={s.label} className="rounded-md border border-[var(--ew-border)] px-3 py-2 min-w-[5rem]">
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{s.label}</p>
                  <p className="eds-type-title text-xl">{s.value}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card title={t("landing.recentObjects")}>
            <ul className="space-y-2">
              {landing.recentObjects.map((r, i) => (
                <li key={`${r.title}-${i}`}>
                  {r.route ? (
                    <Link to={r.route} className="block rounded-md border border-[var(--ew-border)] px-3 py-2">
                      <span className="font-medium eds-type-small">{r.title}</span>
                      <span className="block eds-type-helper">{r.detail}</span>
                    </Link>
                  ) : (
                    <div className="rounded-md border border-[var(--ew-border)] px-3 py-2">
                      <span className="font-medium eds-type-small">{r.title}</span>
                      <span className="block eds-type-helper">{r.detail}</span>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </Card>

          <Card title={t("landing.recent")}>
            <ul className="space-y-2">
              {landing.recent.map((r, i) => (
                <li key={`${r.title}-act-${i}`}>
                  {r.route ? (
                    <Link to={r.route} className="block rounded-md border border-[var(--ew-border)] px-3 py-2">
                      <span className="font-medium eds-type-small">{r.title}</span>
                      <span className="block eds-type-helper">{r.detail}</span>
                    </Link>
                  ) : (
                    <div className="rounded-md border border-[var(--ew-border)] px-3 py-2">
                      <span className="font-medium eds-type-small">{r.title}</span>
                      <span className="block eds-type-helper">{r.detail}</span>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </Card>

          <Card title={t("landing.next")}>
            <p className="eds-type-body">{landing.nextStep}</p>
            <div className="mt-3">
              <Link to={landing.primaryAction.route}>
                <Button className="ews-primary-cta" size="sm">
                  {landing.primaryAction.label}
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
