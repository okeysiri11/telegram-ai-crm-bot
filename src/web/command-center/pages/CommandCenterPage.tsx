import { Link } from "react-router-dom";
import { buildCommandCenterDashboard, PRODUCTIVITY_WIDGET_IDS } from "../dashboard/commandCenterDashboard";
import { PRODUCTIVITY_WIDGETS } from "../dashboard/widgets";
import { useCommandCenterUi } from "../components/CommandCenterProvider";
import { commandAnalytics } from "../managers/analytics";
import { UniversalQuickActionsBar } from "@/command-center-runtime/UniversalQuickActionsBar";
import { AiCommandCenterPanel } from "@/command-center-runtime/AiCommandCenterPanel";
import { GlobalActivityFeed } from "@/command-center-runtime/GlobalActivityFeedPanel";
import { EnterpriseMetricsStrip } from "@/command-center-runtime/EnterpriseMetricsStrip";

/** Sprint 27.5 — Productivity Hub / Enterprise Command Center page. */
export function CommandCenterPage() {
  const ui = useCommandCenterUi();
  const dash = buildCommandCenterDashboard();
  const analytics = commandAnalytics.snapshot();

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <header className="space-y-2">
        <p className="eds-type-caption text-[var(--eds-text-muted)]">Enterprise Command Center · Sprint 27.5</p>
        <h1 className="eds-type-h1 text-[var(--eds-text)]">Command Center</h1>
        <p className="eds-type-body text-[var(--eds-text-muted)]">
          Central control hub — palette, activity, AI ops, metrics, and keyboard-first navigation.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-md bg-[var(--eds-primary)] px-3 py-2 text-[var(--eds-on-primary)] eds-type-small"
            onClick={ui.openPalette}
          >
            Open Palette (⌘K)
          </button>
          <button
            type="button"
            className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small"
            onClick={ui.openOmnibox}
          >
            Omnibox (Ctrl+P)
          </button>
          <button
            type="button"
            className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small"
            onClick={ui.openAi}
          >
            AI Commands (Ctrl+Shift+P)
          </button>
          <Link to="/dashboard" className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
            Dashboard
          </Link>
        </div>
      </header>

      <EnterpriseMetricsStrip />
      <UniversalQuickActionsBar />
      <AiCommandCenterPanel />
      <GlobalActivityFeed compact />

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {PRODUCTIVITY_WIDGETS.map((w) => (
          <article
            key={w.id}
            id={w.id}
            className="rounded-[var(--eds-radius-md)] border border-[var(--eds-border)] bg-[var(--eds-surface)] p-4"
          >
            <h2 className="eds-type-h3">{w.title}</h2>
            <p className="mt-1 eds-type-caption text-[var(--eds-text-muted)]">
              {w.id === "most_used_commands"
                ? analytics.popular_commands.map((c) => c.id).slice(0, 3).join(", ") || "No usage yet"
                : w.id === "recently_opened"
                  ? dash.context.openedPages.slice(-3).join(", ") || "None"
                  : "Ready"}
            </p>
          </article>
        ))}
      </section>

      <section className="rounded-[var(--eds-radius-md)] border border-[var(--eds-border)] bg-[var(--eds-surface)] p-4">
        <h2 className="eds-type-h3">Command Analytics</h2>
        <dl className="mt-3 grid gap-2 sm:grid-cols-4 eds-type-small">
          <div>
            <dt className="text-[var(--eds-text-muted)]">Success rate</dt>
            <dd>{(analytics.success_rate * 100).toFixed(0)}%</dd>
          </div>
          <div>
            <dt className="text-[var(--eds-text-muted)]">AI usage</dt>
            <dd>{analytics.ai_usage}</dd>
          </div>
          <div>
            <dt className="text-[var(--eds-text-muted)]">Index entries</dt>
            <dd>{dash.index_count}</dd>
          </div>
          <div>
            <dt className="text-[var(--eds-text-muted)]">Widgets</dt>
            <dd>{PRODUCTIVITY_WIDGET_IDS.length}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
