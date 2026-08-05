/**
 * Digital Citizens Center — Sprint 29.1 foundation UI.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import {
  digitalCitizenEngine,
  EDC_CITIZEN_OWNER,
  EDC_CITIZEN_DEV,
} from "@/runtime/digitalCitizen";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "citizens" | "membership" | "workspace" | "ai" | "presence" | "activity" | "city";

export function DigitalCitizenPage() {
  const [tab, setTab] = useState<Tab>("citizens");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return digitalCitizenEngine.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Digital Citizens · ADOS";
    rememberModuleRoute("/digital-citizens");
    digitalCitizenEngine.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2500);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "citizens", label: "Citizens" },
    { id: "membership", label: "Membership" },
    { id: "workspace", label: "Workspace" },
    { id: "ai", label: "Personal AI" },
    { id: "presence", label: "Presence" },
    { id: "activity", label: "Activity" },
    { id: "city", label: "City" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Digital Citizens</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.stats.citizens} citizens · {snap.stats.online} online · human
            layer of Enterprise City
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              digitalCitizenEngine.setPresence(EDC_CITIZEN_OWNER, "meeting", {
                cityBuildingId: "mission_control",
              });
              refresh();
            }}
          >
            Owner → Meeting
          </Button>
          <Link to="/business-network" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Business Network →
          </Link>
          <Link to="/enterprise-city" className="eds-type-helper text-[var(--eds-primary)] self-center">
            City →
          </Link>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button
            key={t.id}
            size="sm"
            variant={tab === t.id ? "primary" : "ghost"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "citizens" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.citizens.map((c) => (
            <Card key={c.id} title={c.displayName}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{c.presence.status}</Badge>
                <Badge>{c.verification}</Badge>
                <Badge>{c.status}</Badge>
              </div>
              <p className="eds-type-helper">{c.title || "—"} · {c.identity.email}</p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "membership" ? (
        <Card title="Organization Membership">
          <ul className="space-y-2">
            {snap.memberships.map((m) => (
              <li key={m.id} className="eds-type-small border-b border-[var(--eds-border)] pb-2">
                {m.citizenId} · {m.role} · org {m.orgId}
                {m.managerCitizenId ? ` · mgr ${m.managerCitizenId}` : ""}
                {m.active ? "" : " · left"}
                {m.businessProfileId ? ` · biz ${m.businessProfileId}` : ""}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "workspace" ? (
        <Card title="Owner Workspace">
          {(() => {
            const ws = snap.workspaces.find((w) => w.citizenId === EDC_CITIZEN_OWNER);
            if (!ws) return <p className="eds-type-helper">Empty</p>;
            return (
              <ul className="eds-type-small space-y-1">
                <li>Tasks: {ws.tasks.length}</li>
                <li>Projects: {ws.projects.map((p) => p.projectName).join(", ") || "—"}</li>
                <li>Favorites: {ws.favorites.join(", ") || "—"}</li>
                <li>Documents: {ws.documentRefs.length}</li>
                <li>Calendar: {ws.calendar.length}</li>
              </ul>
            );
          })()}
        </Card>
      ) : null}

      {tab === "ai" ? (
        <Card title="Assistant Registry">
          <ul className="space-y-2">
            {snap.ai.map((a) => (
              <li key={a.id} className="eds-type-small flex flex-wrap gap-2 items-center">
                <Badge>{a.kind}</Badge> {a.name}
                {a.assignedCitizenId ? ` → ${a.assignedCitizenId}` : " (unassigned)"}
                {!a.assignedCitizenId ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      digitalCitizenEngine.assignAi(a.id, EDC_CITIZEN_DEV);
                      refresh();
                    }}
                  >
                    Assign to Dev
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "presence" ? (
        <Card title="Presence">
          <ul className="space-y-1 eds-type-small">
            {snap.presence.map((p) => (
              <li key={p.citizenId}>
                {p.displayName}: <Badge>{p.status}</Badge>
                {p.cityBuildingId ? ` · ${p.cityBuildingId}` : ""}
                {p.locationLabel ? ` · ${p.locationLabel}` : ""}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "activity" ? (
        <Card title="Activity">
          <ul className="space-y-1 eds-type-small">
            {snap.activity.map((a) => (
              <li key={a.id}>
                {a.at.slice(11, 19)} · {a.name} · {a.citizenId}
              </li>
            ))}
            {!snap.activity.length ? <li className="eds-type-helper">No events yet</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "city" ? (
        <Card title="City Citizen Facade">
          {snap.city.owner ? (
            <ul className="eds-type-small space-y-1">
              <li>{snap.city.owner.displayName}</li>
              <li>Presence: {snap.city.owner.presence}</li>
              <li>Role: {snap.city.owner.role}</li>
              <li>Company: {snap.city.owner.companyBusinessProfileId}</li>
              <li>Office: {snap.city.owner.officeId}</li>
              <li>Building: {snap.city.owner.cityBuildingId}</li>
              <li>AI: {snap.city.owner.aiAssignmentIds.join(", ") || "—"}</li>
            </ul>
          ) : (
            <p className="eds-type-helper">No facade</p>
          )}
        </Card>
      ) : null}
    </FullLayout>
  );
}
