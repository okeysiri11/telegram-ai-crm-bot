/**
 * Life Engine Center — Sprint 29.2 foundation UI.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { lifeEngine } from "@/runtime/lifeEngine";
import { EDC_CITIZEN_OWNER, EDC_CITIZEN_DEV } from "@/runtime/digitalCitizen";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "city" | "timeline" | "occupancy" | "meetings" | "projects" | "movements";

export function LifeEnginePage() {
  const [tab, setTab] = useState<Tab>("city");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return lifeEngine.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Life Engine · ADOS";
    rememberModuleRoute("/life-engine");
    lifeEngine.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const city = snap.city;
  const tabs: { id: Tab; label: string }[] = [
    { id: "city", label: "City Runtime" },
    { id: "timeline", label: "Timeline" },
    { id: "occupancy", label: "Occupancy" },
    { id: "meetings", label: "Meetings" },
    { id: "projects", label: "Projects" },
    { id: "movements", label: "Movement" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Life Engine</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {city.stats.online} present · {city.stats.activeMeetings} meetings ·{" "}
            {city.stats.events} events · real runtime (not scripted)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              lifeEngine.enterOffice(EDC_CITIZEN_OWNER, "hub");
              refresh();
            }}
          >
            Owner → Hub
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              const m = lifeEngine.createMeeting({
                title: "Ops sync",
                hostCitizenId: EDC_CITIZEN_OWNER,
                attendeeIds: [EDC_CITIZEN_DEV],
                buildingId: "mission_control",
              });
              lifeEngine.startMeeting(m.id);
              refresh();
            }}
          >
            Start meeting
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              const mov = lifeEngine.move({
                kind: "office_to_office",
                citizenId: EDC_CITIZEN_DEV,
                fromBuildingId: "ai_studio",
                toBuildingId: "developer",
                purpose: "Pairing session",
              });
              lifeEngine.arrive(mov.id);
              refresh();
            }}
          >
            Move Dev
          </Button>
          <Link to="/enterprise-city" className="eds-type-helper text-[var(--eds-primary)] self-center">
            City →
          </Link>
          <Link to="/digital-citizens" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Citizens →
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

      {tab === "city" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Citizens">
            <ul className="eds-type-small space-y-1">
              {city.citizens.map((c) => (
                <li key={c.id}>
                  {c.displayName} · <Badge>{c.presence}</Badge>
                  {c.buildingId ? ` · ${c.buildingId}` : ""}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="AI / Vehicles / Projects">
            <p className="eds-type-small">AI active: {city.ai.filter((a) => a.active).length}</p>
            <p className="eds-type-small">Vehicles: {city.vehicles.length}</p>
            <p className="eds-type-small">Projects: {city.projects.map((p) => p.projectName).join(", ")}</p>
          </Card>
        </div>
      ) : null}

      {tab === "timeline" ? (
        <Card title="Unified Timeline">
          <ul className="space-y-1 eds-type-small">
            {snap.timeline.slice(0, 30).map((e) => (
              <li key={`${e.id}-${e.subjectKind}-${e.subjectId}`}>
                {e.at.slice(11, 19)} · {e.kind} · {e.subjectKind}/{e.subjectId}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "occupancy" ? (
        <Card title="Building Occupancy">
          <ul className="space-y-2">
            {city.occupancy
              .filter((o) => o.occupants.length > 0)
              .map((o) => (
                <li key={o.buildingId} className="eds-type-small border-b border-[var(--eds-border)] pb-2">
                  <strong>{o.buildingId}</strong> · {o.occupants.length}/{o.capacity} · {o.activityLabel}
                  <div className="eds-type-helper">
                    emp {o.employeeCount} · visitors {o.visitorCount} · meetings {o.meetingCount}
                  </div>
                </li>
              ))}
          </ul>
        </Card>
      ) : null}

      {tab === "meetings" ? (
        <Card title="Meetings">
          <ul className="space-y-2">
            {city.meetings.map((m) => (
              <li key={m.id} className="eds-type-small flex flex-wrap gap-2 items-center">
                {m.title} · <Badge>{m.status}</Badge> · {m.buildingId || "—"}
                {m.status === "active" ? (
                  <Button size="sm" variant="ghost" onClick={() => { lifeEngine.endMeeting(m.id); refresh(); }}>
                    End
                  </Button>
                ) : null}
              </li>
            ))}
            {!city.meetings.length ? <li className="eds-type-helper">No meetings</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "projects" ? (
        <Card title="Project Participation">
          <ul className="space-y-1 eds-type-small">
            {snap.participation.map((p) => (
              <li key={p.id}>
                {p.projectName} · {p.citizenId} · {p.role} · score {p.participationScore} · assignments{" "}
                {p.assignments.length}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "movements" ? (
        <Card title="City Movement">
          <ul className="space-y-1 eds-type-small">
            {city.movements.map((m) => (
              <li key={m.id}>
                {m.kind} · {m.fromBuildingId || "?"} → {m.toBuildingId || "?"} · <Badge>{m.status}</Badge>
              </li>
            ))}
            {!city.movements.length ? <li className="eds-type-helper">No movements yet</li> : null}
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
