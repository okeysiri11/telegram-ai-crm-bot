/**
 * Asset Runtime Center — Sprint 29.3 foundation UI.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import { assetRuntime } from "@/runtime/assetRuntime";
import { EDC_CITIZEN_DEV, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { EBN_PARTNER_PROFILE_ID } from "@/runtime/businessNetwork";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "assets" | "ownership" | "location" | "lifecycle" | "city" | "events";

export function AssetRuntimePage() {
  const [tab, setTab] = useState<Tab>("assets");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return assetRuntime.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Asset Runtime · ADOS";
    rememberModuleRoute("/assets");
    assetRuntime.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2500);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "assets", label: "Assets" },
    { id: "ownership", label: "Ownership" },
    { id: "location", label: "Location" },
    { id: "lifecycle", label: "Lifecycle" },
    { id: "city", label: "City" },
    { id: "events", label: "Events" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Asset Runtime</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.stats.assets} assets · {snap.stats.available} available ·{" "}
            {snap.stats.inUse} in use · {snap.stats.types} types
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              assetRuntime.assign("ast_van_1", { citizenId: EDC_CITIZEN_OWNER });
              refresh();
            }}
          >
            Assign Van → Owner
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              assetRuntime.move("ast_drone_1", {
                kind: "building",
                buildingId: "mission_control",
                districtId: "enterprise",
              });
              refresh();
            }}
          >
            Move Drone
          </Button>
          <Link to="/life-engine" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Life →
          </Link>
          <Link to="/spatial" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Spatial →
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

      {tab === "assets" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.assets.map((a) => (
            <Card key={a.id} title={a.profile.name}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{a.type}</Badge>
                <Badge>{a.status}</Badge>
                <Badge>{a.ownership.kind}</Badge>
                {a.available ? <Badge>available</Badge> : <Badge>busy</Badge>}
              </div>
              <p className="eds-type-helper">
                {a.location.kind}
                {a.location.buildingId ? ` · ${a.location.buildingId}` : ""}
                {a.assignedCitizenId ? ` · assignee ${a.assignedCitizenId}` : ""}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "ownership" ? (
        <Card title="Transfers">
          <ul className="space-y-2">
            {snap.transfers.map((t) => (
              <li key={t.id} className="eds-type-small">
                {t.assetId}: {t.from.kind} → {t.to.kind} {t.reason ? `(${t.reason})` : ""}
              </li>
            ))}
            {!snap.transfers.length ? (
              <li className="eds-type-helper">
                No transfers yet.{" "}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    assetRuntime.transfer(
                      "ast_digital_pack",
                      {
                        kind: "partner",
                        companyId: EBN_PARTNER_PROFILE_ID,
                        partnerCompanyId: EBN_PARTNER_PROFILE_ID,
                      },
                      EDC_CITIZEN_OWNER,
                      "Partner distribution",
                    );
                    refresh();
                  }}
                >
                  Transfer pack → partner
                </Button>
              </li>
            ) : null}
          </ul>
        </Card>
      ) : null}

      {tab === "location" ? (
        <Card title="By Building">
          <ul className="eds-type-small space-y-1">
            {Object.entries(snap.city.byBuilding).map(([b, list]) => (
              <li key={b}>
                {b}: {list.map((a) => a.profile.name).join(", ")}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "lifecycle" ? (
        <Card title="Lifecycle actions">
          <div className="flex flex-wrap gap-2 mb-3">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                assetRuntime.maintain("ast_server_1", "Firmware update");
                refresh();
              }}
            >
              Maintain server
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                assetRuntime.setLifecycle("ast_server_1", "in_use");
                refresh();
              }}
            >
              Return to use
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                assetRuntime.assign("ast_laptop_dev", { citizenId: EDC_CITIZEN_DEV });
                refresh();
              }}
            >
              Reassign laptop
            </Button>
          </div>
          <ul className="eds-type-small space-y-1">
            {snap.assets
              .filter((a) => a.status === "maintenance" || a.lifecycle.phase === "maintenance")
              .map((a) => (
                <li key={a.id}>
                  {a.profile.name} · {a.lifecycle.phase}
                </li>
              ))}
          </ul>
        </Card>
      ) : null}

      {tab === "city" ? (
        <Card title="City Asset Query">
          <ul className="eds-type-small space-y-1">
            <li>Total: {snap.city.totals.assets}</li>
            <li>Available: {snap.city.totals.available}</li>
            <li>In use: {snap.city.totals.inUse}</li>
            <li>Maintenance: {snap.city.totals.maintenance}</li>
            <li>Buildings with assets: {Object.keys(snap.city.byBuilding).length}</li>
            <li>Districts: {Object.keys(snap.city.byDistrict).length}</li>
          </ul>
        </Card>
      ) : null}

      {tab === "events" ? (
        <Card title="Asset Events">
          <ul className="eds-type-small space-y-1">
            {snap.events.map((e) => (
              <li key={e.id}>
                {e.at.slice(11, 19)} · {e.name} · {e.assetId}
              </li>
            ))}
            {!snap.events.length ? <li className="eds-type-helper">No events yet</li> : null}
          </ul>
        </Card>
      ) : null}
    </FullLayout>
  );
}
