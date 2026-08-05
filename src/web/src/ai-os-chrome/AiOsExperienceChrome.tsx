/**
 * AI Operating System chrome — Sprint 32.4.
 * Concierge dock + Pulse + Executive Snapshot — no new engines.
 */

import { useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { loadFirstEntry } from "@/onboarding/firstEntryStore";
import { firstEntryRoleCatalog } from "@/onboarding/firstEntryRoles";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useCommandCenterUi } from "../../command-center/components/CommandCenterProvider";
import { useLiveEnterprise, type LiveEnterpriseSnapshot } from "@/live-ops";
import { detectActiveEcosystem } from "@/workspace-chrome/workspaceContext";
import { telemetry } from "@/integrations/telemetry";
import { suggestionsForPath, sectionKeyFromPath, toAdvisor } from "./smartSuggestions";
import { advisorContextLine, markAdvisorSeen } from "./aiPersonality";
import { AdvisorRecView } from "./AdvisorRecView";
import { getBuilding } from "@/enterprise-city/cityCatalog";
import { getCityFocus, buildingIdentity } from "@/enterprise-city/cityVisualLanguage";

export function AiOsExperienceChrome() {
  const loc = useLocation();
  const navigate = useNavigate();
  const { openAi, openPalette, openOmnibox } = useCommandCenterUi();
  const { snapshot, busy } = useLiveEnterprise(true);
  const unread = useNotificationStore((s) => s.items.filter((i) => !i.read).length);
  const ws = useWorkspaceStore((s) => s.workspace);
  const user = useAuthStore((s) => s.user);
  const first = loadFirstEntry();
  const role = firstEntryRoleCatalog.get(first.roleId);
  const [snapOpen, setSnapOpen] = useState(false);
  const [dockOpen, setDockOpen] = useState(true);

  const concierge = first.conciergeName || "AI Concierge";
  const roleLabel = role?.label || user?.roleId || "User";
  const ecosystem = detectActiveEcosystem(loc.pathname) || "Platform";
  const section = sectionKeyFromPath(loc.pathname);
  const healthOk = snapshot.health.filter((h) => h.ok).length;
  const healthTotal = snapshot.health.length || 1;
  const aiBusy = snapshot.aiOps.running.length > 0;
  // EP-04: dock is Executive Advisor surface (not a chatbot).
  const suggestions = useMemo(() => suggestionsForPath(loc.pathname, 2, snapshot), [loc.pathname, snapshot]);
  const cityFocus = getCityFocus();
  const cityBuilding = cityFocus ? getBuilding(cityFocus) : null;
  const contextLine = useMemo(() => {
    const base = advisorContextLine({
      section,
      company: first.companyName || ws.company,
      healthOk,
      healthTotal,
      unread,
      aiBusy,
    });
    if (cityBuilding) {
      return `${base} City focus: ${cityBuilding.short} · ${buildingIdentity(cityBuilding.id).purposeRu}.`;
    }
    return base;
  }, [section, first.companyName, ws.company, healthOk, healthTotal, unread, aiBusy, cityBuilding]);

  return (
    <div className="aios-chrome eds-anim-fade">
      <WorkspacePulse
        aiActive={aiBusy}
        notifications={unread}
        health={`${healthOk}/${healthTotal}`}
        busy={busy || aiBusy}
      />

      {dockOpen ? (
        <aside className={`aios-dock${busy || aiBusy ? " is-analyzing edm-ai-analyzing" : " edm-ai-live"}`} aria-label="AI Concierge">
          <div className="aios-dock-head">
            <div>
              <p className="eds-type-caption uppercase tracking-[0.14em] text-[var(--eds-text-muted)]">
                Executive Advisor
              </p>
              <p className="font-semibold">{concierge}</p>
            </div>
            <div className="flex flex-wrap gap-1">
              <Badge tone={aiBusy ? "success" : "warning"}>{aiBusy ? "Active" : "Ready"}</Badge>
              {busy || aiBusy ? <span className="edm-stream-bar w-16 self-center" aria-hidden /> : null}
              <Button size="sm" variant="ghost" onClick={() => setDockOpen(false)} aria-label="Collapse Concierge">
                −
              </Button>
            </div>
          </div>

          <p className="eds-type-small text-[var(--eds-text-muted)] ai-advisor-context">{contextLine}</p>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Context · {section} · {roleLabel} · {ecosystem}
          </p>

          <div className="aios-dock-block">
            <p className="mb-1 font-medium eds-type-small">Next decisions · top 2</p>
            <ul className="space-y-1 edm-stagger">
              {suggestions.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className="aios-suggest edm-ai-suggest"
                    onClick={() => {
                      markAdvisorSeen(s.id);
                      void telemetry.userActivity(`aios_suggest:${s.id}`);
                      navigate(s.route);
                    }}
                  >
                    <AdvisorRecView rec={toAdvisor(s)} compact />
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => {
                void telemetry.userActivity("aios_open_ai");
                openAi();
              }}
            >
              AI · ⌘⇧P
            </Button>
            <Button size="sm" variant="secondary" onClick={() => openPalette()}>
              Search · ⌘K
            </Button>
            <Button size="sm" variant="secondary" onClick={() => openOmnibox()}>
              Commands · ⌘/
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setSnapOpen((v) => !v)}>
              {snapOpen ? "Hide Snapshot" : "Executive Snapshot"}
            </Button>
            <Link to="/platform-builder/concierge">
              <Button size="sm" variant="ghost">
                Настроить
              </Button>
            </Link>
          </div>
        </aside>
      ) : (
        <button
          type="button"
          className="aios-dock-collapsed edm-ai-done"
          onClick={() => setDockOpen(true)}
          aria-label="Expand AI Concierge"
        >
          <Badge tone="success">AI</Badge> {concierge} · показать панель
        </button>
      )}

      {snapOpen ? (
        <ExecutiveSnapshot
          company={first.companyName || ws.company}
          snapshot={snapshot}
          unread={unread}
          onClose={() => setSnapOpen(false)}
        />
      ) : null}
    </div>
  );
}

function WorkspacePulse({
  aiActive,
  notifications,
  health,
  busy,
}: {
  aiActive: boolean;
  notifications: number;
  health: string;
  busy: boolean;
}) {
  return (
    <div className={`aios-pulse${busy ? " is-busy" : ""}`} aria-label="Workspace Pulse">
      <span className="aios-pulse-label">Pulse</span>
      <Badge tone={aiActive ? "success" : "default"}>AI {aiActive ? "on" : "idle"}</Badge>
      <Badge tone={notifications ? "warning" : "default"}>{notifications ? `Notif ${notifications}` : "No notif"}</Badge>
      <Badge tone={busy ? "warning" : "success"}>Health {health}</Badge>
    </div>
  );
}

function ExecutiveSnapshot({
  company,
  snapshot,
  unread,
  onClose,
}: {
  company: string;
  snapshot: LiveEnterpriseSnapshot;
  unread: number;
  onClose: () => void;
}) {
  const critical = snapshot.activity.slice(0, 4);
  return (
    <Card title={`Executive Snapshot · ${company}`} className="aios-snapshot eds-anim-scale edm-card-enter">
      <div className="grid gap-3 md:grid-cols-3">
        <div>
          <p className="mb-1 font-medium eds-type-small">Что происходит</p>
          <ul className="eds-type-small space-y-1 text-[var(--eds-text-muted)]">
            {critical.map((a) => (
              <li key={a.id}>· {a.title}</li>
            ))}
            {!critical.length ? <li>· Система спокойна</li> : null}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium eds-type-small">Требует внимания</p>
          <ul className="eds-type-small space-y-1">
            <li>
              <Badge tone={unread ? "warning" : "success"}>{unread} уведомлений</Badge>
            </li>
            {snapshot.health
              .filter((h) => !h.ok)
              .slice(0, 3)
              .map((h) => (
                <li key={h.id}>
                  <Badge tone="warning">{h.label}</Badge>
                </li>
              ))}
            {snapshot.aiOps.errors.slice(0, 2).map((e) => (
              <li key={e}>
                <Badge tone="danger">{e}</Badge>
              </li>
            ))}
            {!snapshot.health.some((h) => !h.ok) && !snapshot.aiOps.errors.length && !unread ? (
              <li className="text-[var(--eds-text-muted)]">· Критичных сигналов нет</li>
            ) : null}
          </ul>
        </div>
        <div>
          <p className="mb-1 font-medium eds-type-small">Executive Advisor</p>
          <ul className="eds-type-small space-y-1 text-[var(--eds-text-muted)]">
            <li>Next decisions live in the dock — Observation, Why, Action, Impact.</li>
            <li className={unread ? "" : "text-[var(--eds-text-muted)]"}>
              {unread
                ? `${unread} notifications remain — treat them as decision items.`
                : "Signals are calm — use the window for opportunities."}
            </li>
          </ul>
          <Link to="/platform-builder/concierge" className="eds-type-small text-[var(--eds-primary)]">
            Configure Advisor →
          </Link>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Link to="/dashboard?mode=executive">
          <Button size="sm">Executive Mode</Button>
        </Link>
        <Link to="/platform-builder/mission-control">
          <Button size="sm" variant="secondary">
            Mission Control
          </Button>
        </Link>
        <Button size="sm" variant="ghost" onClick={onClose}>
          Закрыть
        </Button>
      </div>
    </Card>
  );
}
