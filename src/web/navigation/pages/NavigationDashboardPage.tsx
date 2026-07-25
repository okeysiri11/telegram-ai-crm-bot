import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Input } from "@/ui";
import { buildNavigationDashboard } from "../dashboard/navigationDashboard";
import {
  applicationRegistry,
  favoritesManager,
  menuEngine,
  searchProvider,
  shortcutManager,
  workspaceFederation,
} from "../managers";
import { navigationPerformance } from "../performance";
import { useNavigationUi } from "../components/NavigationProvider";
import { navigationAnalytics } from "../managers/navigationAnalytics";

export function NavigationDashboardPage() {
  const dash = buildNavigationDashboard();
  const [q, setQ] = useState("");
  const hits = useMemo(() => {
    const result = searchProvider.search(q);
    navigationAnalytics.trackSearch(q, result.length);
    return result;
  }, [q]);
  const { openPalette, openQuickSwitcher } = useNavigationUi();

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="eds-type-h1">Enterprise Navigation</h1>
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              Federation · Global Search · Smart Favorites · Quick Switcher · Analytics
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={openPalette}>Command Palette (⌘K)</Button>
            <Button variant="secondary" onClick={openQuickSwitcher}>
              Quick Switcher (Ctrl+Tab)
            </Button>
          </div>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Workspace federation">
            <p className="eds-type-caption mb-2">Current: {dash.currentWorkspace.name}</p>
            <ul className="space-y-1 eds-type-small">
              {dash.workspaces.map((w) => (
                <li key={w.id}>
                  <button
                    type="button"
                    className="text-[var(--eds-primary)]"
                    onClick={() => workspaceFederation.switchTo(w.kind)}
                  >
                    {w.name}
                  </button>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Application registry">
            <ul className="max-h-48 space-y-1 overflow-auto eds-type-small">
              {applicationRegistry.list().map((a) => (
                <li key={a.id}>
                  <Badge>{a.icon}</Badge> {a.name} · v{a.version} · {a.health}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Active navigation">
            <ul className="space-y-1 eds-type-small">
              {dash.activeNavigation.map((n) => (
                <li key={n.id}>
                  <Link className="text-[var(--eds-primary)]" to={n.route}>
                    {n.name}
                  </Link>{" "}
                  {n.badge ? <Badge>{n.badge}</Badge> : null}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Smart favorites">
            <ul className="space-y-1 eds-type-small">
              {favoritesManager.list().map((f) => (
                <li key={f.id}>
                  {f.kind}: {f.label}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Recent history">
            <ul className="space-y-1 eds-type-small">
              {dash.recentActivity.map((a) => (
                <li key={a.id}>
                  {a.kind}: {a.label}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Navigation analytics">
            <p className="eds-type-small">Searches: {dash.analytics.search_statistics.total}</p>
            <p className="eds-type-caption">Abandoned: {dash.analytics.abandoned_searches}</p>
            <p className="eds-type-caption mt-1">{dash.analytics.ai_recommendations.join(" · ")}</p>
          </Card>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Global search">
            <Input
              className="eds-focus-ring mb-3"
              placeholder="Search CRM, ERP, Knowledge, Agents, Apps…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <ul className="max-h-56 space-y-1 overflow-auto">
              {hits.map((h) => (
                <li key={h.id} className="eds-type-small">
                  <Link className="text-[var(--eds-primary)]" to={h.path}>
                    {h.category}: {h.title}
                  </Link>{" "}
                  <span className="eds-type-caption">
                    {h.match} · {h.score}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Menu engine">
            <p className="eds-type-small">Groups: {menuEngine.groups().join(", ")}</p>
            <p className="eds-type-caption mt-1">Nested menus: {menuEngine.nested().length}</p>
          </Card>
          <Card title="Shortcuts">
            <ul className="space-y-1 eds-type-small">
              {shortcutManager.list().map((s) => (
                <li key={s.id}>
                  {s.keys} · {s.scope}
                </li>
              ))}
              <li>Ctrl+Tab · quick switcher</li>
            </ul>
          </Card>
          <Card title="Performance">
            <p className="eds-type-small">{navigationPerformance.features.join(" · ")}</p>
          </Card>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
