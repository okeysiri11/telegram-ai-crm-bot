/**
 * Spatial Runtime Center — Sprint 29.4 foundation UI (no map rendering).
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { rememberModuleRoute } from "@/modules/lastModuleStore";
import { resolveSpatialBuildingId } from "@/runtime/spatialRuntime/citySpatialQuery";

type Tab = "hierarchy" | "districts" | "locations" | "routing" | "city" | "events";

export function SpatialRuntimePage() {
  const [tab, setTab] = useState<Tab>("hierarchy");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return spatialRuntime.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Spatial Runtime · ADOS";
    rememberModuleRoute("/spatial");
    spatialRuntime.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2500);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "hierarchy", label: "Hierarchy" },
    { id: "districts", label: "Districts" },
    { id: "locations", label: "Locations" },
    { id: "routing", label: "Routing" },
    { id: "city", label: "City Query" },
    { id: "events", label: "Events" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Spatial Runtime</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.odessa.name} Digital Twin · {snap.stats.entities} entities ·{" "}
            {snap.stats.buildings} buildings · {snap.stats.districts} districts
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              spatialRuntime.assignLocation({
                subjectKind: "citizen",
                subjectId: EDC_CITIZEN_OWNER,
                kind: "current",
                entityId: resolveSpatialBuildingId("developer"),
              });
              refresh();
            }}
          >
            Move Owner → Developer
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              spatialRuntime.moveAsset("ast_drone_1", {
                kind: "building",
                buildingId: "mission_control",
                districtId: "enterprise",
              });
              refresh();
            }}
          >
            Move Drone Asset
          </Button>
          <Link to="/assets" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Assets →
          </Link>
          <Link to="/city-visualization" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Viz →
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

      {tab === "hierarchy" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {(
            [
              "country",
              "region",
              "city",
              "district",
              "street",
              "building",
              "floor",
              "room",
              "workspace",
              "virtual_space",
            ] as const
          ).map((kind) => (
            <Card key={kind} title={`${kind} (${snap.hierarchy[kind]?.length || 0})`}>
              <ul className="eds-type-small space-y-1 max-h-40 overflow-auto">
                {(snap.hierarchy[kind] || []).slice(0, 12).map((e) => (
                  <li key={e.id}>
                    {e.name} <span className="eds-type-helper">· {e.id}</span>
                  </li>
                ))}
              </ul>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "districts" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.districts.map((d) => (
            <Card key={d.id} title={d.name}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{d.districtKind || "custom"}</Badge>
                {d.cityDistrictId ? <Badge>{d.cityDistrictId}</Badge> : null}
              </div>
              <p className="eds-type-helper">
                Buildings: {spatialRuntime.buildingsByDistrict(d.cityDistrictId || d.id).length}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "locations" ? (
        <Card title="Location Assignments">
          <ul className="eds-type-small space-y-1">
            {snap.assignments.map((a) => (
              <li key={a.id}>
                {a.subjectKind}:{a.subjectId} · {a.kind} → {a.entityId}
              </li>
            ))}
            {!snap.assignments.length ? <li className="eds-type-helper">No assignments</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "routing" ? (
        <Card title="Sample Route (Hub → Developer)">
          {snap.sampleRoute ? (
            <ul className="eds-type-small space-y-1">
              <li>
                Distance: {Math.round(snap.sampleRoute.distanceM)} m · Travel:{" "}
                {snap.sampleRoute.travelTimeSec}s · Mode: {snap.sampleRoute.mode}
              </li>
              <li>Nodes: {snap.sampleRoute.nodeIds.join(" → ")}</li>
              <li>Path points: {snap.sampleRoute.path.length}</li>
            </ul>
          ) : (
            <p className="eds-type-helper">No route</p>
          )}
        </Card>
      ) : null}

      {tab === "city" ? (
        <Card title="City Spatial Query">
          <ul className="eds-type-small space-y-1">
            <li>Entities: {snap.city.stats.entities}</li>
            <li>Buildings: {snap.city.stats.buildings}</li>
            <li>Districts: {snap.city.stats.districts}</li>
            <li>Citizen locations: {Object.keys(snap.city.citizensByLocation).length}</li>
            <li>Asset buildings: {Object.keys(snap.city.assetsByBuilding).length}</li>
            <li>Company buildings: {Object.keys(snap.city.companiesByBuilding).length}</li>
            <li>Meetings by office: {Object.keys(snap.city.meetingsByOffice).length}</li>
            <li>Projects by area: {Object.keys(snap.city.projectsByArea).length}</li>
          </ul>
        </Card>
      ) : null}

      {tab === "events" ? (
        <Card title="Spatial Events">
          <ul className="eds-type-small space-y-1">
            {snap.events.map((e) => (
              <li key={e.id}>
                {e.at.slice(11, 19)} · {e.name}
                {e.entityId ? ` · ${e.entityId}` : ""}
              </li>
            ))}
            {!snap.events.length ? <li className="eds-type-helper">No events yet</li> : null}
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
