/**
 * City Visualization Runtime Center — Sprint 29.5 (no graphics).
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "scene" | "buildings" | "districts" | "citizens" | "assets" | "visible" | "events";

export function CityVisualizationPage() {
  const [tab, setTab] = useState<Tab>("scene");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return cityVisualizationRuntime.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "City Visualization Runtime · ADOS";
    rememberModuleRoute("/city-visualization");
    cityVisualizationRuntime.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 3000);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "scene", label: "Scene" },
    { id: "buildings", label: "Buildings" },
    { id: "districts", label: "Districts" },
    { id: "citizens", label: "Citizens" },
    { id: "assets", label: "Assets" },
    { id: "visible", label: "Visible Query" },
    { id: "events", label: "Events" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">City Visualization Runtime</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.scene.cityName} · rev {snap.state.revision} · LOD{" "}
            {snap.state.lod} · {snap.stats.buildings} buildings · {snap.stats.citizens} citizens
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              cityVisualizationRuntime.rebuildScene("SceneRebuilt");
              refresh();
            }}
          >
            Rebuild Scene
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              cityVisualizationRuntime.setLod("far");
              refresh();
            }}
          >
            LOD Far
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              cityVisualizationRuntime.setLod("near");
              refresh();
            }}
          >
            LOD Near
          </Button>
          <Link to="/spatial" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Spatial →
          </Link>
          <Link to="/interactions" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Interact →
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

      {tab === "scene" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Layers">
            <ul className="eds-type-small space-y-1">
              {snap.layers.map((l) => (
                <li key={l.id}>
                  <Badge>{l.enabled ? "on" : "off"}</Badge> {l.label} · lod≥{l.lodMin}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Stats">
            <ul className="eds-type-small space-y-1">
              <li>Districts: {snap.stats.districts}</li>
              <li>Companies: {snap.stats.companies}</li>
              <li>Assets: {snap.stats.assets}</li>
              <li>Activities: {snap.stats.activities}</li>
              <li>Renderer adapters: {snap.stats.adapters}</li>
              <li>Events: {snap.stats.events}</li>
            </ul>
          </Card>
        </div>
      ) : null}

      {tab === "buildings" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.scene.buildings.slice(0, 16).map((b) => (
            <Card key={b.buildingId} title={b.buildingId}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{b.status}</Badge>
                <Badge>{b.openState}</Badge>
                {b.districtId ? <Badge>{b.districtId}</Badge> : null}
              </div>
              <p className="eds-type-helper">
                occ {b.occupancy} · meetings {b.meetingCount} · assets {b.assetCount} · activity{" "}
                {b.businessActivity}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "districts" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.scene.districts.map((d) => (
            <Card key={d.districtId} title={d.districtId}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{d.runtimeStatus}</Badge>
                {d.districtKind ? <Badge>{d.districtKind}</Badge> : null}
              </div>
              <p className="eds-type-helper">
                pop {d.population} · density {d.businessDensity} · traffic {d.trafficDensity} · econ{" "}
                {d.economicActivity}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "citizens" ? (
        <Card title="Citizen Visual State">
          <ul className="eds-type-small space-y-1">
            {snap.scene.citizens.map((c) => (
              <li key={c.citizenId}>
                {c.displayName} · {c.presence} · {c.buildingId || "remote"} · {c.role || "—"}
                {c.remote ? " · remote" : ""}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "assets" ? (
        <Card title="Asset Visual State">
          <ul className="eds-type-small space-y-1">
            {snap.scene.assets.slice(0, 24).map((a) => (
              <li key={a.assetId}>
                {a.name} · {a.type} · {a.status} · {a.buildingId || "—"}
                {a.isDrone ? " · drone" : ""}
                {a.isVehicle ? " · vehicle" : ""}
                {!a.available ? " · busy" : ""}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "visible" ? (
        <Card title={`Visible Query (LOD ${snap.query.lod})`}>
          <ul className="eds-type-small space-y-1">
            <li>Buildings: {snap.query.buildings.length}</li>
            <li>Citizens: {snap.query.citizens.length}</li>
            <li>Companies: {snap.query.companies.length}</li>
            <li>Assets: {snap.query.assets.length}</li>
            <li>Activities: {snap.query.activities.length}</li>
            <li>Districts: {snap.query.districts.length}</li>
            <li>Revision: {snap.query.revision}</li>
          </ul>
        </Card>
      ) : null}

      {tab === "events" ? (
        <Card title="Visualization Events">
          <ul className="eds-type-small space-y-1">
            {snap.events.map((e) => (
              <li key={e.id}>
                {e.at.slice(11, 19)} · {e.name}
              </li>
            ))}
            {!snap.events.length ? <li className="eds-type-helper">No events</li> : null}
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
