/**
 * Enterprise City map + chrome — Sprint 32.3.3.
 * Lightweight CSS/DOM city (no WebGL). Click → existing routes only.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Input } from "@/ui";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { searchIndex } from "../../navigation/managers/searchIndex";
import { telemetry } from "@/integrations/telemetry";
import { useLiveEnterprise } from "@/live-ops";
import { deriveWorkflowAutomation, getWorkflowTemplate } from "@/enterprise-workflow";
import {
  CITY_BUILDINGS,
  searchBuildings,
  type CityBuilding,
  type CityBuildingId,
  type CityLiveStatus,
} from "./cityCatalog";
import { useCityLiveStatus } from "./useCityLiveStatus";

function registerCitySearchDocs() {
  for (const b of CITY_BUILDINGS) {
    searchIndex.upsert({
      id: `city_${b.id}`,
      category: "modules",
      title: `${b.label} · Enterprise City`,
      path: b.route,
      tokens: [...b.searchTokens, "city", "enterprise", "building"],
      rankBoost: 8,
    });
  }
  searchIndex.upsert({
    id: "city_map",
    category: "modules",
    title: "Enterprise City",
    path: "/enterprise-city",
    tokens: ["enterprise", "city", "map", "navigation", "buildings"],
    rankBoost: 12,
  });
}

export function EnterpriseCityPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { statusById, unread, mcLinked, refreshMc } = useCityLiveStatus();
  const { snapshot } = useLiveEnterprise(true);
  const [q, setQ] = useState("");
  const [focusId, setFocusId] = useState<CityBuildingId | null>(null);
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });
  const planeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    registerCitySearchDocs();
  }, []);

  const wfBundle = useMemo(() => deriveWorkflowAutomation(snapshot, [], params.get("wf")), [snapshot, params]);
  const cityPath = useMemo(() => {
    const tpl = params.get("wf") ? getWorkflowTemplate(params.get("wf") || "") : null;
    return tpl?.cityPath || wfBundle.cityRoute;
  }, [params, wfBundle.cityRoute]);
  const pathSet = useMemo(() => new Set(cityPath), [cityPath]);

  const filtered = useMemo(() => searchBuildings(q), [q]);
  const globalHits = useMemo(() => (q.trim() ? searchProvider.search(q).slice(0, 6) : []), [q]);

  function openBuilding(b: CityBuilding) {
    setFocusId(b.id);
    void telemetry.userActivity(`city_enter:${b.id}`);
    navigate(b.route);
  }

  function panTo(b: CityBuilding) {
    setFocusId(b.id);
    setViewport((v) => ({
      ...v,
      x: Math.min(20, Math.max(-20, 50 - b.x)),
      y: Math.min(20, Math.max(-20, 50 - b.y)),
    }));
  }

  return (
    <WorkspaceLayout>
      <div className="enterprise-city eds-anim-fade">
        <header className="ec-header">
          <div className="min-w-0">
            <p className="eds-type-caption uppercase tracking-[0.16em] text-[var(--eds-text-muted)]">
              Enterprise City Navigation
            </p>
            <h1 className="text-2xl font-semibold tracking-tight lg:text-3xl xl:text-4xl">
              Город модулей
            </h1>
            <p className="mt-2 max-w-2xl eds-type-small text-[var(--eds-text-muted)]">
              Альтернативная навигация к существующим Workspace и Platform Builder страницам. Dashboard не
              заменяется — это визуальная карта.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone={mcLinked ? "success" : "warning"}>MC {mcLinked ? "linked" : "check"}</Badge>
            <Badge>{unread} alerts</Badge>
            <Badge tone="success">Live city</Badge>
            {cityPath.length ? <Badge tone="warning">WF route</Badge> : null}
            <Button size="sm" variant="secondary" onClick={() => void refreshMc()}>
              Refresh status
            </Button>
            <Link to="/platform-builder/workflow-center">
              <Button size="sm" variant="secondary">
                Workflow Center
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button size="sm" variant="secondary">
                Command Center
              </Button>
            </Link>
            <Link to="/platform-builder/digital-twin">
              <Button size="sm" variant="secondary">
                Digital Twin
              </Button>
            </Link>
          </div>
        </header>

        <div className="ec-toolbar">
          <div className="ec-search">
            <Input
              placeholder="Поиск модуля · workspace · сотрудников · документов"
              aria-label="City search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const hit = filtered[0] || (globalHits[0] ? CITY_BUILDINGS.find((b) => b.route === globalHits[0].path) : undefined);
                  if (hit) openBuilding(hit);
                  else if (globalHits[0]) navigate(globalHits[0].path);
                }
              }}
            />
            {q.trim() ? (
              <Card title="Результаты" className="ec-search-panel">
                <ul className="space-y-1 eds-type-small">
                  {filtered.map((b) => (
                    <li key={b.id}>
                      <button type="button" className="ec-search-hit" onClick={() => openBuilding(b)}>
                        <span>
                          {b.icon} {b.label}
                        </span>
                        <Badge>{b.short}</Badge>
                      </button>
                    </li>
                  ))}
                  {globalHits.map((h) => (
                    <li key={h.id}>
                      <button
                        type="button"
                        className="ec-search-hit"
                        onClick={() => {
                          void telemetry.userActivity(`city_search:${h.path}`);
                          navigate(h.path);
                        }}
                      >
                        <span>
                          {h.title} · {h.category}
                        </span>
                        <Badge>index</Badge>
                      </button>
                    </li>
                  ))}
                </ul>
              </Card>
            ) : null}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="ghost" onClick={() => setViewport({ x: 0, y: 0, zoom: 1 })}>
              Reset view
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setViewport((v) => ({ ...v, zoom: Math.min(1.4, v.zoom + 0.1) }))}
            >
              Zoom +
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setViewport((v) => ({ ...v, zoom: Math.max(0.75, v.zoom - 0.1) }))}
            >
              Zoom −
            </Button>
          </div>
        </div>

        <div className="ec-stage">
          <div className="ec-map-shell" ref={planeRef}>
            <div
              className="ec-plane"
              style={{
                transform: `translate(${viewport.x}%, ${viewport.y}%) scale(${viewport.zoom})`,
              }}
            >
              <div className="ec-grid" aria-hidden />
              {cityPath.length >= 2 ? (
                <svg className="ec-wf-route" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
                  <polyline
                    fill="none"
                    stroke="color-mix(in oklab, #0f766e 75%, #0369a1)"
                    strokeWidth="0.9"
                    strokeDasharray="2 1.2"
                    points={cityPath
                      .map((id) => {
                        const b = CITY_BUILDINGS.find((x) => x.id === id);
                        if (!b) return null;
                        return `${b.x + b.w / 2},${b.y + b.h / 2}`;
                      })
                      .filter(Boolean)
                      .join(" ")}
                  />
                  {cityPath.map((id, i) => {
                    const b = CITY_BUILDINGS.find((x) => x.id === id);
                    if (!b) return null;
                    return (
                      <circle
                        key={`${id}_${i}`}
                        cx={b.x + b.w / 2}
                        cy={b.y + b.h / 2}
                        r="1.4"
                        fill={i === 0 ? "#0f766e" : i === cityPath.length - 1 ? "#0369a1" : "#14857c"}
                      />
                    );
                  })}
                </svg>
              ) : null}
              {CITY_BUILDINGS.map((b) => (
                <CityBuildingTile
                  key={b.id}
                  building={b}
                  status={statusById[b.id]}
                  focused={focusId === b.id || pathSet.has(b.id)}
                  dimmed={
                    (filtered.length < CITY_BUILDINGS.length && !filtered.some((f) => f.id === b.id)) ||
                    (pathSet.size > 0 && !pathSet.has(b.id) && focusId !== b.id)
                  }
                  onOpen={() => openBuilding(b)}
                  onFocus={() => setFocusId(b.id)}
                />
              ))}
            </div>
          </div>

          <aside className="ec-side">
            <CityMinimap
              focusId={focusId}
              statusById={statusById}
              onSelect={(b) => {
                panTo(b);
                setFocusId(b.id);
              }}
            />
            <Card title="Live status">
              <ul className="space-y-2 eds-type-small">
                {CITY_BUILDINGS.filter((b) => statusById[b.id].tone !== "idle")
                  .slice(0, 6)
                  .map((b) => (
                    <li key={b.id} className="flex items-center justify-between gap-2">
                      <button type="button" className="text-left underline-offset-2 hover:underline" onClick={() => panTo(b)}>
                        {b.icon} {b.short}
                      </button>
                      <Badge tone={statusById[b.id].tone === "alert" ? "warning" : "success"}>
                        {statusById[b.id].processLabel}
                      </Badge>
                    </li>
                  ))}
              </ul>
            </Card>
            <Card title="Districts">
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Commerce · Ops · People · Intel · Hub — клик по зданию открывает существующий маршрут без
                новой бизнес-логики.
              </p>
            </Card>
          </aside>
        </div>
      </div>
    </WorkspaceLayout>
  );
}

function CityBuildingTile({
  building,
  status,
  focused,
  dimmed,
  onOpen,
  onFocus,
}: {
  building: CityBuilding;
  status: CityLiveStatus;
  focused: boolean;
  dimmed: boolean;
  onOpen: () => void;
  onFocus: () => void;
}) {
  return (
    <button
      type="button"
      className={`ec-building ec-tone-${status.tone}${focused ? " is-focused" : ""}${dimmed ? " is-dimmed" : ""}`}
      style={{
        left: `${building.x}%`,
        top: `${building.y}%`,
        width: `${building.w}%`,
        height: `${building.h}%`,
      }}
      onClick={onOpen}
      onMouseEnter={onFocus}
      onFocus={onFocus}
      aria-label={`${building.label} — ${status.processLabel}`}
      title={`${building.label}\n${status.processLabel}`}
    >
      <span className="ec-building-icon" aria-hidden>
        {building.icon}
      </span>
      <span className="ec-building-label">{building.short}</span>
      {status.notifications > 0 ? <span className="ec-badge">{status.notifications}</span> : null}
      {status.aiActive ? <span className="ec-ai-dot" title="AI activity" /> : null}
      {status.tasks > 0 ? <span className="ec-tasks">{status.tasks}</span> : null}
    </button>
  );
}

function CityMinimap({
  focusId,
  statusById,
  onSelect,
}: {
  focusId: CityBuildingId | null;
  statusById: Record<CityBuildingId, CityLiveStatus>;
  onSelect: (b: CityBuilding) => void;
}) {
  return (
    <Card title="Minimap">
      <div className="ec-minimap" role="img" aria-label="City minimap">
        {CITY_BUILDINGS.map((b) => (
          <button
            key={b.id}
            type="button"
            className={`ec-mini-dot ec-tone-${statusById[b.id].tone}${focusId === b.id ? " is-focused" : ""}`}
            style={{ left: `${b.x + b.w / 2}%`, top: `${b.y + b.h / 2}%` }}
            onClick={() => onSelect(b)}
            aria-label={`Go to ${b.label}`}
            title={b.label}
          />
        ))}
      </div>
      <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">Быстрый переход к району</p>
    </Card>
  );
}
