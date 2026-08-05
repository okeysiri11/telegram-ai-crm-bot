import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Button, Card, Input } from "@/ui";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { ENTERPRISE_MODULES } from "./moduleCatalog";
import { rememberModuleRoute } from "./lastModuleStore";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { logActivity } from "@/workspace-engine/activityJournal";

/**
 * Sprint 27.2 / 27.4 — Search Workspace with grouped index results.
 */
export function SearchWorkspacePage() {
  const [params] = useSearchParams();
  const [q, setQ] = useState(() => params.get("q") || "");
  const navigate = useNavigate();
  const { openPalette } = useNavigationUi();

  useEffect(() => {
    document.title = "Search · ADOS Enterprise";
    rememberModuleRoute("/search");
  }, []);

  useEffect(() => {
    const fromUrl = params.get("q");
    if (fromUrl != null) setQ(fromUrl);
  }, [params]);

  const moduleHits = ENTERPRISE_MODULES.filter((m) => {
    const hay = `${m.label} ${m.description} ${m.slug}`.toLowerCase();
    return !q.trim() || hay.includes(q.trim().toLowerCase());
  });
  const groups = useMemo(() => (q.trim() ? searchProvider.searchGrouped(q, 8) : []), [q]);

  return (
    <WorkspaceLayout>
      <div className="edm-page space-y-4">
        <header className="ews-module-hero ews-glass">
          <h1 className="eds-type-title text-2xl">Search Workspace</h1>
          <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
            CRM · ERP · AI Agents · Documents · Settings · Users · Projects · Knowledge · Commands
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Input
              className="min-w-[16rem] flex-1"
              placeholder="Search modules and pages…"
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                if (e.target.value.trim().length > 2) {
                  logActivity({ kind: "search", title: "Search query", detail: e.target.value.trim() });
                }
              }}
              aria-label="Search"
              autoFocus
            />
            <Button type="button" variant="secondary" onClick={openPalette}>
              Open Command Palette
            </Button>
          </div>
        </header>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Modules">
            <ul className="space-y-2">
              {moduleHits.map((m) => (
                <li key={m.id}>
                  <Link to={m.route} className="cc-action block">
                    <span className="font-medium">{m.label}</span>
                    <span className="eds-type-helper">{m.description}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Grouped results">
            {groups.length ? (
              <div className="space-y-4 max-h-[28rem] overflow-y-auto">
                {groups.map((g) => (
                  <div key={g.category}>
                    <p className="eds-type-section mb-1">{g.label}</p>
                    <ul className="space-y-2">
                      {g.hits.map((h) => (
                        <li key={h.id || h.path + h.title}>
                          <button
                            type="button"
                            className="cc-action w-full text-left"
                            onClick={() => navigate(h.path)}
                          >
                            <span className="font-medium">{h.title}</span>
                            <span className="eds-type-helper">{h.path}</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            ) : (
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Type a query to search the navigation index by category, or open the command palette.
              </p>
            )}
          </Card>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
