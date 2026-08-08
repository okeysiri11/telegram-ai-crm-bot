/**
 * Sprint 41.2 / 41.3 / 42.3 — page orientation chrome:
 * Where am I · Purpose · Actions · Result · Time · Help
 */

import { Link, useLocation, useSearchParams } from "react-router-dom";
import { ModuleHelpIcon } from "./ModuleHelpIcon";
import { helpForRoute } from "./moduleHelpCatalog";
import { useI18n } from "@/i18n";
import { landingForPath } from "@/modules/moduleLandingCatalog";

export function PageOrientationBar({
  title,
  what,
  actions,
  result,
}: {
  title?: string;
  what?: string;
  actions?: string;
  result?: string;
}) {
  const { pathname } = useLocation();
  const [params] = useSearchParams();
  const t = useI18n((s) => s.t);
  const help = helpForRoute(pathname);
  const landing = landingForPath(pathname);
  const deep =
    Boolean(params.get("view")) ||
    Boolean(params.get("action")) ||
    params.get("demo") === "1";

  // ModuleLandingView already answers Where/What/Do/Next — avoid duplicate chrome.
  if (landing && !deep && !title && !what) {
    return null;
  }

  const heading = title || landing?.title || help?.purpose || t("page.here");
  const whatText = what || landing?.purpose || help?.why || "";
  const actionsText =
    actions ||
    (landing ? landing.actions.map((a) => a.label).join(" · ") : "") ||
    help?.workflow ||
    "";
  const resultText = result || landing?.nextStep || help?.expectedResult || "";
  const minutes = landing?.estimatedMinutes;

  const trail: string[] = [];
  if (landing) {
    if (landing.id === "drone" || landing.id === "auto" || landing.id === "crypto") {
      trail.push(t("role.owner"));
    }
    trail.push(landing.title);
  } else if (heading) {
    trail.push(heading);
  }

  return (
    <div
      className="mb-4 flex flex-wrap items-start justify-between gap-3 rounded-md border border-[var(--ew-border)] bg-[var(--eds-surface)] px-3 py-2 ews-hierarchy-header"
      data-testid="page-orientation"
    >
      <div className="min-w-0 flex-1">
        <p className="eds-type-caption text-[var(--eds-text-muted)]">{t("page.where")}</p>
        <nav className="ews-context-trail eds-type-helper mb-1" aria-label={t("page.where")}>
          <Link to="/dashboard" className="text-[var(--eds-accent)]">
            {t("nav.dashboard")}
          </Link>
          {trail.map((seg, i) => (
            <span key={`${seg}-${i}`}>
              <span className="mx-1 text-[var(--eds-text-muted)]">/</span>
              <span className={i === trail.length - 1 ? "font-medium text-[var(--eds-text)]" : undefined}>
                {seg}
              </span>
            </span>
          ))}
        </nav>
        <p className="eds-type-section">{heading}</p>
        {whatText ? (
          <p className="eds-type-helper mt-1">
            <span className="font-medium">{t("page.what")}: </span>
            {whatText}
          </p>
        ) : null}
        {actionsText ? (
          <p className="eds-type-helper">
            <span className="font-medium">{t("page.actions")}: </span>
            {actionsText}
          </p>
        ) : null}
        {resultText ? (
          <p className="eds-type-helper">
            <span className="font-medium">{t("page.result")}: </span>
            {resultText}
          </p>
        ) : null}
        {minutes != null ? (
          <p className="eds-type-helper">
            <span className="font-medium">{t("page.time")}: </span>~{minutes} {t("common.minutes")}
          </p>
        ) : null}
      </div>
      <div className="flex items-center gap-2">
        <span className="eds-type-caption text-[var(--eds-text-muted)]">{t("page.help")}</span>
        <ModuleHelpIcon pathname={pathname} />
      </div>
    </div>
  );
}
