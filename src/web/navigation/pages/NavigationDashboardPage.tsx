import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Input } from "@/ui";
import { buildNavigationDashboard } from "../dashboard/navigationDashboard";
import { favoritesManager, menuEngine, searchProvider, shortcutManager } from "../managers";
import { navigationPerformance } from "../performance";
import { useNavigationUi } from "../components/NavigationProvider";

export function NavigationDashboardPage() {
  const dash = buildNavigationDashboard();
  const [q, setQ] = useState("");
  const hits = useMemo(() => searchProvider.search(q), [q]);
  const { openPalette } = useNavigationUi();

  return (
    <WorkspaceLayout>
      <div className="space-y-6 eds-anim-fade">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="eds-type-h1">Navigation Platform</h1>
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              Command Palette · Global Search · Dynamic Menu · Shortcuts
            </p>
          </div>
          <Button onClick={openPalette}>Open Command Palette (⌘/Ctrl+K)</Button>
        </div>

        <div className="eds-grid eds-grid--dashboard">
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
          <Card title="Search analytics">
            <p className="eds-type-small">Categories: {dash.searchAnalytics.categories}</p>
            <p className="eds-type-caption mt-1">Recent: {dash.searchAnalytics.recent.join(", ")}</p>
          </Card>
          <Card title="Most used pages">
            <ul className="space-y-1 eds-type-small">
              {dash.mostUsedPages.map((p) => (
                <li key={p.id}>{p.label}</li>
              ))}
            </ul>
          </Card>
          <Card title="Favorite modules">
            <ul className="space-y-1 eds-type-small">
              {dash.favoriteModules.map((f) => (
                <li key={f.id}>
                  <Link className="text-[var(--eds-primary)]" to={f.path}>
                    {f.label}
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Recent activity">
            <ul className="space-y-1 eds-type-small">
              {dash.recentActivity.map((a) => (
                <li key={a.id}>
                  {a.kind}: {a.label}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Shortcut usage">
            <ul className="space-y-1 eds-type-small">
              {dash.shortcutUsage.map((s) => (
                <li key={s.id}>
                  {s.keys} → {s.action} <Badge>{s.scope}</Badge>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Command usage">
            <ul className="space-y-1 eds-type-small">
              {dash.commandUsage.map((c) => (
                <li key={c.id}>{c.label}</li>
              ))}
            </ul>
          </Card>
          <Card title="Performance">
            <p className="eds-type-small">{navigationPerformance.features.join(" · ")}</p>
            <p className="eds-type-caption mt-1">
              Prefetch: {navigationPerformance.prefetchRoutes.join(", ")}
            </p>
          </Card>
        </div>

        <div className="eds-grid eds-grid--dashboard">
          <Card title="Global search (realtime)">
            <Input
              className="eds-focus-ring mb-3"
              placeholder="Search modules, CRM, AI, workflows…"
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
            <p className="eds-type-caption">Mega groups: {menuEngine.megaGroups().length}</p>
          </Card>
          <Card title="Favorites">
            <ul className="space-y-1 eds-type-small">
              {favoritesManager.list().map((f) => (
                <li key={f.id}>
                  {f.kind}: {f.label}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Shortcuts">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => shortcutManager.update("sc_search", "Meta+Shift+/")}
            >
              Customize search shortcut
            </Button>
            <ul className="mt-2 space-y-1 eds-type-small">
              {shortcutManager.list().map((s) => (
                <li key={s.id}>
                  {s.keys} · {s.scope}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
