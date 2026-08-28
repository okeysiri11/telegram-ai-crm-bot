/**
 * Enterprise City map + chrome — Sprint 32.3.3 / EP-05 / 27.8 / 30.4 Beta.
 * Interactive CSS/DOM city: pan · zoom · select · hover · open module.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent as ReactMouseEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Badge, Button, Card, Input } from "@/ui";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { searchIndex } from "../../navigation/managers/searchIndex";
import { telemetry } from "@/integrations/telemetry";
import { useLiveEnterprise } from "@/live-ops";
import { deriveWorkflowAutomation, getWorkflowTemplate } from "@/enterprise-workflow";
import { suggestionsForPath } from "@/ai-os-chrome/smartSuggestions";
import { withDecisionQuery, rememberNavDecision } from "@/decision-flow";
import { enterpriseEventBus } from "@/integration-hub";
import { EnterpriseRuntimeMonitorCompact } from "@/enterprise-runtime/EnterpriseRuntimeMonitor";
import { runtimeEngine } from "@/enterprise-runtime/runtimeEngine";
import { deriveGodModeMetrics } from "@/enterprise-business";
import {
  CITY_BUILDINGS,
  getBuilding,
  searchBuildings,
  type CityBuilding,
  type CityBuildingId,
  type CityDistrictId,
  type CityLiveStatus,
} from "./cityCatalog";
import { CITY_DISTRICTS, getPlaza, getDistrict, primaryBuildingForDistrict } from "./cityDistricts";
import {
  applyPanDelta,
  panToBuilding,
  readViewport,
  writeViewport,
  zoomBy,
  viewportRect,
  type CityViewport,
  CITY_EXPERIENCE_CORE,
} from "./cityEngine";
import { cityNavigation } from "./cityNavigation";
import { useCityLiveStatus } from "./useCityLiveStatus";
import {
  CITY_STATE_LABELS,
  advisorHintForBuilding,
  badgeToneForState,
  buildingIdentity,
  cityGlance,
  districtLinks,
  getCityFocus,
  resolveVisualState,
  setCityFocus,
  stateLabelRu,
} from "./cityVisualLanguage";
import { useCityGraphicsRuntime } from "./graphics/useCityGraphicsRuntime";
import { CityDevOverlay } from "./graphics/CityDevOverlay";
import { defaultGraphicsSettings } from "./graphics/graphicsConfig";
import type { ResolvedEffect } from "./graphics/types";
import { buildingOps, HEALTH_LABEL_RU, healthFromLiveTone } from "./buildingOps";
import { selectCityBuilding } from "./cityInteractionBridge";
import { geoSelectionBridge } from "./odessa3d/geospatial";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import type { BuildingHealth } from "./buildingOps";
import {
  Odessa3DView,
  Odessa3DQualitySelect,
  readViewMode,
  writeViewMode,
  readQualityProfile,
  writeQualityProfile,
} from "./odessa3d";
import type { QualityProfile } from "./odessa3d/types";

function registerCitySearchDocs() {
  searchIndex.remove("city_casino");
  searchIndex.remove("hub_city_casino");
  for (const b of CITY_BUILDINGS) {
    if (b.id === "casino") continue;
    searchIndex.upsert({
      id: `city_${b.id}`,
      category: "modules",
      title: `${b.label} · Enterprise City`,
      path: b.route,
      tokens: [...b.searchTokens, "city", "enterprise", "building", "город", b.district],
      rankBoost: 8,
    });
  }
  for (const d of CITY_DISTRICTS) {
    searchIndex.upsert({
      id: `city_district_${d.id}`,
      category: "modules",
      title: `District · ${d.label}`,
      path: "/enterprise-city",
      tokens: [d.id, d.label, "district", "район", "city"],
      rankBoost: 7,
    });
  }
  searchIndex.upsert({
    id: "city_map",
    category: "modules",
    title: "Enterprise City",
    path: "/enterprise-city",
    tokens: ["enterprise", "city", "map", "navigation", "buildings", "город", "plaza"],
    rankBoost: 12,
  });
}

function withEmbed(path: string, embed: boolean): string {
  if (!embed || path.includes("embed=1")) return path;
  return `${path}${path.includes("?") ? "&" : "?"}embed=1`;
}

export function EnterpriseCityPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const embed = params.get("embed") === "1";
  const { statusById, unread, mcLinked, refreshMc } = useCityLiveStatus();
  const { snapshot } = useLiveEnterprise(true);
  const [q, setQ] = useState("");
  const [focusId, setFocusId] = useState<CityBuildingId | null>(() => getCityFocus());
  const [hoverId, setHoverId] = useState<CityBuildingId | null>(null);
  const [viewport, setViewport] = useState<CityViewport>(() => readViewport());
  const [overlay, setOverlay] = useState<"all" | "health" | "activity" | "ai">("all");
  const [favTick, setFavTick] = useState(0);
  const [showDevOverlay, setShowDevOverlay] = useState(false);
  const [cityViewMode, setCityViewMode] = useState<"2d" | "3d">(() => readViewMode());
  const [qualityProfile, setQualityProfile] = useState<QualityProfile>(() => readQualityProfile());
  const [bridgeGeo, setBridgeGeo] = useState<{ lat: number; lon: number } | null>(null);
  const ownerView = useRoleSwitcher((s) => s.isOwnerView());
  const planeRef = useRef<HTMLDivElement>(null);
  const cityRootRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ sx: number; sy: number; vx: number; vy: number } | null>(null);

  const graphics = useCityGraphicsRuntime(planeRef, cityRootRef, viewport, setViewport, statusById);
  const graphicsRef = useRef(graphics);
  useEffect(() => {
    graphicsRef.current = graphics;
  }, [graphics]);

  useEffect(() => {
    registerCitySearchDocs();
    runtimeEngine.publishStream("city", { surface: "city" });
  }, []);

  useEffect(() => {
    const building = params.get("building");
    if (building === "casino") {
      setFocusId("casino");
      setCityFocus("casino");
    }
  }, [params]);

  useEffect(() => {
    return geoSelectionBridge.subscribe((state) => {
      if (state.intent === "show-2d" && state.geo) {
        const geo = geoSelectionBridge.consumeShow2d();
        if (geo) {
          setBridgeGeo(geo);
          setCityViewMode("2d");
          writeViewMode("2d");
        }
        return;
      }
      if (state.intent === "show-3d" && state.geo) {
        setBridgeGeo(state.geo);
        setCityViewMode("3d");
        writeViewMode("3d");
      }
    });
  }, []);

  useEffect(() => {
    const building = params.get("building") as CityBuildingId | null;
    if (building && getBuilding(building)) {
      const b = getBuilding(building)!;
      setFocusId(b.id);
      setViewport((v) => panToBuilding(b, v));
    }
  }, [params]);

  useEffect(() => {
    setCityFocus(focusId);
  }, [focusId]);

  useEffect(() => {
    writeViewport(viewport);
  }, [viewport]);

  const wfBundle = useMemo(() => deriveWorkflowAutomation(snapshot, [], params.get("wf")), [snapshot, params]);
  const cityPath = useMemo(() => {
    const tpl = params.get("wf") ? getWorkflowTemplate(params.get("wf") || "") : null;
    return tpl?.cityPath || wfBundle.cityRoute;
  }, [params, wfBundle.cityRoute]);
  const pathSet = useMemo(() => new Set(cityPath), [cityPath]);
  const links = useMemo(() => districtLinks(), []);
  const glance = useMemo(() => cityGlance(statusById), [statusById]);
  const focused = focusId ? CITY_BUILDINGS.find((b) => b.id === focusId) : null;
  const focusedStatus = focusId ? statusById[focusId] : null;
  const focusedOps = focused
    ? {
        ...buildingOps(focused.id, focused.route),
        health: healthFromLiveTone(
          focusedStatus?.tone || "idle",
          focusedStatus?.notifications || 0,
          focusedStatus?.tasks || 0,
        ),
      }
    : null;
  const advisor = focused && focusedStatus ? advisorHintForBuilding(focused.id, focusedStatus) : null;
  const cityAdvice = useMemo(() => suggestionsForPath("/enterprise-city", 2, snapshot), [snapshot]);
  const crumbs = useMemo(() => cityNavigation.breadcrumbs(focused || null), [focused]);
  const recentIds = useMemo(() => cityNavigation.recent(), [focusId, favTick]);
  const historyIds = useMemo(() => cityNavigation.history().slice(0, 8), [focusId, favTick]);
  const favoriteIds = useMemo(() => cityNavigation.favorites(), [favTick]);
  const plaza = useMemo(() => getPlaza(), []);
  const miniRect = useMemo(() => viewportRect(viewport), [viewport]);

  const filtered = useMemo(() => searchBuildings(q), [q]);
  const globalHits = useMemo(() => (q.trim() ? searchProvider.search(q).slice(0, 6) : []), [q]);

  const platformActiveUsers = useMemo(
    () => CITY_BUILDINGS.reduce((sum, b) => sum + buildingOps(b.id, b.route).activeUsers, 0),
    [],
  );
  const healthCounts = useMemo(() => {
    const counts: Record<BuildingHealth, number> = {
      online: 0,
      warning: 0,
      critical: 0,
      maintenance: 0,
    };
    for (const b of CITY_BUILDINGS) {
      const st = statusById[b.id];
      if (!st) continue;
      counts[
        healthFromLiveTone(st.tone, st.notifications, st.tasks)
      ] += 1;
    }
    return counts;
  }, [statusById]);
  const runtimeSnap = useMemo(() => runtimeEngine.getSnapshot(), [favTick, focusId]);

  const selectBuilding = useCallback((b: CityBuilding) => {
    setFocusId(b.id);
    setCityFocus(b.id);
    cityNavigation.pushRecent(b.id);
    setFavTick((t) => t + 1);
    selectCityBuilding(b.id);
    geoSelectionBridge.setFrom2d(`city_building_${b.id}`);
    void telemetry.userActivity(`city_select:${b.id}`);
    graphicsRef.current.triggerBuildingEffect(b.id, "selection");
    graphicsRef.current.focusBuildingAnimated(b);
  }, []);

  const handleOdessaSelectBuilding = useCallback(
    (id: string | null) => {
      if (!id) return;
      const b = getBuilding(id as CityBuildingId);
      if (b) selectBuilding(b);
    },
    [selectBuilding],
  );

  const handleOdessaOpenRoute = useCallback(
    (route: string) => {
      navigate(withEmbed(route, embed));
    },
    [navigate, embed],
  );

  const returnHome = useCallback(() => {
    if (plaza) selectBuilding(plaza);
    else navigate(withEmbed("/dashboard", embed));
  }, [plaza, selectBuilding, navigate, embed]);

  const openBuilding = useCallback(
    async (b: CityBuilding) => {
      setFocusId(b.id);
      setCityFocus(b.id);
      cityNavigation.pushHistory(b.id);
      setFavTick((t) => t + 1);
      selectCityBuilding(b.id);
      void telemetry.userActivity(`city_enter:${b.id}`);
      enterpriseEventBus.openCityBuilding(b.id, b.route);
      graphicsRef.current.triggerBuildingEffect(b.id, "selection");
      if (b.id === "plaza" || b.route === "/enterprise-city" || b.route === "/city") {
        graphicsRef.current.focusBuildingAnimated(b);
        return;
      }
      if (b.route.startsWith("/production")) {
        enterpriseEventBus.openProduction(
          new URLSearchParams(b.route.split("?")[1] || "").get("studio") || undefined,
          new URLSearchParams(b.route.split("?")[1] || "").get("tab") || undefined,
        );
      }
      // Portal effect: a brief visual cue at the tile before handing off to the real route. Skips
      // itself (resolves immediately) under reduced motion, a hidden tab, or Low quality — see
      // `useCityGraphicsRuntime.playPortalEffect`.
      await graphicsRef.current.playPortalEffect(b.id);
      navigate(withEmbed(b.route, embed));
    },
    [embed, navigate],
  );

  const panTo = useCallback((b: CityBuilding) => {
    setFocusId(b.id);
    graphicsRef.current.triggerBuildingEffect(b.id, "selection");
    graphicsRef.current.focusBuildingAnimated(b);
  }, []);

  const jumpDistrict = useCallback(
    (id: CityDistrictId) => {
      graphicsRef.current.triggerDistrictEffect(id, "district_activation");
      const target = primaryBuildingForDistrict(id);
      if (target) panTo(target);
    },
    [panTo],
  );

  /** Sprint 30.6 — district open navigates into the real module. */
  const openDistrict = useCallback(
    (id: CityDistrictId) => {
      graphicsRef.current.triggerDistrictEffect(id, "district_activation");
      const target = primaryBuildingForDistrict(id);
      if (target) void openBuilding(target);
    },
    [openBuilding],
  );

  function showLayer(_b: CityBuilding, st: CityLiveStatus): boolean {
    if (overlay === "all") return true;
    if (overlay === "health") return resolveVisualState(st) === "critical" || resolveVisualState(st) === "attention";
    if (overlay === "activity") return st.tone === "busy" || st.tone === "active" || st.tasks > 0;
    if (overlay === "ai") return st.aiActive;
    return true;
  }

  const isBuildingDimmed = useCallback(
    // `showLayer` reads `overlay` from the enclosing closure — listed explicitly below since
    // `showLayer` itself isn't memoized.
    (b: CityBuilding, st: CityLiveStatus) =>
      !showLayer(b, st) ||
      (filtered.length < CITY_BUILDINGS.length && !filtered.some((f) => f.id === b.id)) ||
      (pathSet.size > 0 && !pathSet.has(b.id) && focusId !== b.id),
    [overlay, filtered, pathSet, focusId],
  );

  const visibleBuildingsCount = useMemo(() => {
    let count = 0;
    for (const b of CITY_BUILDINGS) {
      const st = statusById[b.id];
      if (st && !isBuildingDimmed(b, st)) count += 1;
    }
    return count;
  }, [statusById, isBuildingDimmed]);

  function onMapPointerDown(e: ReactMouseEvent) {
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest(".ec-building")) return;
    graphicsRef.current.cancelActiveAnimation();
    const live = graphicsRef.current.getLiveViewport();
    drag.current = { sx: e.clientX, sy: e.clientY, vx: live.x, vy: live.y };
    function onMove(ev: MouseEvent) {
      if (!drag.current || !planeRef.current) return;
      const rect = planeRef.current.getBoundingClientRect();
      const dxPct = ((ev.clientX - drag.current.sx) / rect.width) * 100;
      const dyPct = ((ev.clientY - drag.current.sy) / rect.height) * 100;
      setViewport(
        applyPanDelta(
          { x: drag.current.vx, y: drag.current.vy, zoom: live.zoom },
          dxPct,
          dyPct,
        ),
      );
    }
    function onUp() {
      drag.current = null;
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  useEffect(() => {
    const el = planeRef.current;
    if (!el) return;
    function onWheel(e: WheelEvent) {
      e.preventDefault();
      const delta = e.deltaY > 0 ? -0.08 : 0.08;
      const g = graphicsRef.current;
      g.animateViewportTo(zoomBy(g.getLiveViewport(), delta), { durationMs: 120 });
    }
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  return (
    <WorkspaceLayout>
      <div className="enterprise-city edm-page-soft" ref={cityRootRef} data-tab-hidden="false">
        <header className="ec-header ews-glass">
          <div className="min-w-0">
            <p className="eds-type-caption uppercase tracking-[0.16em] text-[var(--eds-text-muted)]">
              Город предприятия · Beta · Core {CITY_EXPERIENCE_CORE}
            </p>
            <h1 className="text-2xl font-semibold tracking-tight lg:text-3xl">Интерактивный город</h1>
            <nav className="ec-breadcrumbs" aria-label="City breadcrumbs">
              {crumbs.map((c, i) => (
                <span key={`${c.label}_${i}`}>
                  {i > 0 ? <span className="ec-crumb-sep">/</span> : null}
                  {c.id?.startsWith("district:") ? (
                    <button
                      type="button"
                      className="ec-crumb"
                      onClick={() => jumpDistrict(c.id!.replace("district:", "") as CityDistrictId)}
                    >
                      {c.label}
                    </button>
                  ) : (
                    <span className="ec-crumb">{c.label}</span>
                  )}
                </span>
              ))}
            </nav>
          </div>
          <div className="ec-glance edm-stagger" aria-label="City glance">
            <GlanceChip label="OK" value={glance.ok} tone="success" />
            <GlanceChip label="Увага" value={glance.attention} tone="warning" />
            <GlanceChip label="Крит." value={glance.critical} tone="danger" />
            <GlanceChip label="В роботі" value={glance.running} tone="info" />
            <GlanceChip label="AI" value={glance.ai} tone="default" />
            <Badge tone={mcLinked ? "success" : "warning"}>MC {mcLinked ? "live" : "check"}</Badge>
            {unread ? <Badge tone="warning">{unread}</Badge> : null}
            <EnterpriseRuntimeMonitorCompact />
            <Link to="/desktop" className="eds-type-helper text-[var(--eds-primary)]">
              Desktop OS
            </Link>
          </div>
        </header>

        <nav className="ec-exec-nav" aria-label="Навигация города">
          <Button size="sm" variant="primary" toolbar onClick={returnHome}>
            Домой
          </Button>
          <Link
            to={withDecisionQuery("/dashboard?mode=executive", { from: "/enterprise-city", step: "decide" })}
            onClick={() => rememberNavDecision("/enterprise-city", "/dashboard", "City → Dashboard decision", "decide")}
          >
            <Button size="sm" variant="secondary" toolbar>
              Главная
            </Button>
          </Link>
          <Link
            to={withDecisionQuery("/platform-builder/concierge", { from: "/enterprise-city", step: "recommend" })}
            onClick={() => rememberNavDecision("/enterprise-city", "/platform-builder/concierge", "City → Advisor", "recommend")}
          >
            <Button size="sm" variant="secondary" toolbar>
              AI-советник
            </Button>
          </Link>
          {plaza ? (
            <Button size="sm" variant="secondary" toolbar onClick={() => selectBuilding(plaza)}>
              Площадь
            </Button>
          ) : null}
          <Button size="sm" variant="ghost" toolbar onClick={() => void refreshMc()}>
            Обновить
          </Button>
        </nav>

        <div className="ec-quick-jump" aria-label="Районы города">
          {CITY_DISTRICTS.map((d) => (
            <button key={d.id} type="button" className="ec-jump-chip" onClick={() => openDistrict(d.id)}>
              {d.labelRu}
            </button>
          ))}
        </div>

        <div className="ec-toolbar">
          <div className="ec-search">
            <Input
              placeholder="Search · jump · district · building"
              aria-label="City search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  const hit =
                    filtered[0] ||
                    (globalHits[0] ? CITY_BUILDINGS.find((b) => b.route === globalHits[0]!.path) : undefined);
                  if (hit) openBuilding(hit);
                  else if (globalHits[0]) navigate(withEmbed(globalHits[0].path, embed));
                }
              }}
            />
            {q.trim() ? (
              <Card title="Results" className="ec-search-panel">
                <ul className="space-y-1 eds-type-small">
                  {filtered.map((b) => (
                    <li key={b.id}>
                      <button type="button" className="ec-search-hit" onClick={() => selectBuilding(b)}>
                        <span className="ec-search-id">
                          <span className={`ec-sil-mini ${buildingIdentity(b.id).silhouette}`} aria-hidden />
                          {b.label}
                        </span>
                        <Badge tone={badgeToneForState(resolveVisualState(statusById[b.id]!))}>
                          {stateLabelRu(statusById[b.id]!)}
                        </Badge>
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
                          navigate(withEmbed(h.path, embed));
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
          <div className="ec-layer-toggles" role="group" aria-label="Executive overlays">
            <Button
              size="sm"
              variant={cityViewMode === "2d" ? "primary" : "ghost"}
              toolbar
              aria-pressed={cityViewMode === "2d"}
              onClick={() => {
                setCityViewMode("2d");
                writeViewMode("2d");
              }}
            >
              2D
            </Button>
            <Button
              size="sm"
              variant={cityViewMode === "3d" ? "primary" : "ghost"}
              toolbar
              aria-pressed={cityViewMode === "3d"}
              onClick={() => {
                setCityViewMode("3d");
                writeViewMode("3d");
              }}
            >
              3D Одесса
            </Button>
            {bridgeGeo ? (
              <Button
                size="sm"
                variant="ghost"
                toolbar
                data-testid="odessa-show-in-3d"
                onClick={() => {
                  geoSelectionBridge.requestShowIn3d(bridgeGeo);
                  setCityViewMode("3d");
                  writeViewMode("3d");
                }}
              >
                Показать в 3D
              </Button>
            ) : null}
            {cityViewMode === "3d" ? (
              <Odessa3DQualitySelect
                value={qualityProfile}
                onChange={(v) => {
                  setQualityProfile(v);
                  writeQualityProfile(v);
                }}
              />
            ) : null}
            {cityViewMode === "2d"
              ? (
                  [
                    ["all", "All"],
                    ["health", "Health"],
                    ["activity", "Activity"],
                    ["ai", "AI"],
                  ] as const
                ).map(([id, label]) => (
                  <Button
                    key={id}
                    size="sm"
                    variant={overlay === id ? "primary" : "ghost"}
                    toolbar
                    onClick={() => setOverlay(id)}
                  >
                    {label}
                  </Button>
                ))
              : null}
            {cityViewMode === "2d" ? (
              <>
                <Button size="sm" variant="ghost" toolbar onClick={() => graphics.resetCameraAnimated()}>
                  Reset
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  toolbar
                  onClick={() => graphics.animateViewportTo(zoomBy(graphics.getLiveViewport(), 0.1), { durationMs: 160 })}
                >
                  +
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  toolbar
                  onClick={() => graphics.animateViewportTo(zoomBy(graphics.getLiveViewport(), -0.1), { durationMs: 160 })}
                >
                  −
                </Button>
              </>
            ) : null}
            <Button
              size="sm"
              variant={showDevOverlay ? "primary" : "ghost"}
              toolbar
              onClick={() => setShowDevOverlay((v) => !v)}
              aria-pressed={showDevOverlay}
            >
              Debug
            </Button>
          </div>
        </div>

        <div className="ec-legend" aria-label="Живой статус">
          {(Object.keys(HEALTH_LABEL_RU) as BuildingHealth[]).map((k) => (
            <span key={k} className={`ec-legend-item ec-live-${k}`}>
              <i aria-hidden />
              {HEALTH_LABEL_RU[k]}
              <span className="ec-legend-count">{healthCounts[k]}</span>
            </span>
          ))}
        </div>

        {ownerView ? (
          <Card
            title="Owner Mode · God Mode"
            className="ec-owner-panel edm-page-soft"
            status={<Badge tone="success">Owner</Badge>}
            data-testid="city-owner-god-mode"
          >
            <div className="ec-owner-grid">
              <div>
                <p className="eds-type-caption">Здоровье платформы</p>
                <p className="eds-type-small">
                  OK {glance.ok} · Увага {glance.attention} · Крит. {glance.critical} · AI {glance.ai}
                </p>
              </div>
              <div>
                <p className="eds-type-caption">Активные пользователи</p>
                <p className="font-semibold">{platformActiveUsers}</p>
              </div>
              <div>
                <p className="eds-type-caption">Runtime</p>
                <p className="eds-type-small">
                  {runtimeSnap.status} · {runtimeSnap.healthItems.length} checks · {runtimeSnap.jobs.length} jobs
                </p>
                <EnterpriseRuntimeMonitorCompact />
              </div>
            </div>
            <div className="ec-god-metrics mt-3" aria-label="God Mode метрики" data-testid="city-god-metrics">
              {deriveGodModeMetrics()
                .slice(0, 14)
                .map((m) => (
                  <Link key={m.id} to={m.route} className="ec-god-metric" title={m.title}>
                    <span className="eds-type-caption">{m.title}</span>
                    <Badge tone={m.tone || "default"}>{m.value}</Badge>
                  </Link>
                ))}
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <Link className="text-[var(--eds-primary)] eds-type-small" to="/platform-builder/god-mode">
                Control Center God Mode →
              </Link>
              <Link className="text-[var(--eds-primary)] eds-type-small" to="/health">
                Здоровье платформы →
              </Link>
            </div>
            <div className="ec-chip-row mt-2" aria-label="Прыжок по зданиям">
              {CITY_BUILDINGS.slice(0, 24).map((b) => (
                <button
                  key={b.id}
                  type="button"
                  className="ec-jump-chip"
                  onClick={() => selectBuilding(b)}
                  title={b.label}
                >
                  {b.short}
                </button>
              ))}
            </div>
            <div className="ec-chip-row mt-2" aria-label="Все районы">
              {CITY_DISTRICTS.map((d) => (
                <button key={d.id} type="button" className="ec-jump-chip" onClick={() => jumpDistrict(d.id)}>
                  {d.labelRu}
                </button>
              ))}
            </div>
          </Card>
        ) : null}

        {bridgeGeo ? (
          <div className="mb-2 rounded-md border border-[var(--eds-border)] px-3 py-2 text-sm" data-testid="odessa-2d-geo-marker">
            <p className="opacity-70">3D → 2D маркер (WGS84, не адрес)</p>
            <p className="font-mono text-xs">
              {bridgeGeo.lat.toFixed(6)}, {bridgeGeo.lon.toFixed(6)}
            </p>
          </div>
        ) : null}
        <div className="ec-stage">
          {cityViewMode === "3d" ? (
            <Odessa3DView
              qualityProfile={qualityProfile}
              showDev={showDevOverlay}
              onOpenRoute={handleOdessaOpenRoute}
              onSelectBuildingId={handleOdessaSelectBuilding}
            />
          ) : (
          <div
            className="ec-map-shell"
            ref={planeRef}
            onMouseDown={onMapPointerDown}
            role="presentation"
            title="Drag to pan · wheel to zoom"
          >
            <div
              className="ec-plane"
              style={{
                transform: `translate(${viewport.x}%, ${viewport.y}%) scale(${viewport.zoom})`,
              }}
            >
              <div className="ec-grid" aria-hidden />
              <div className="ec-plaza-ring" aria-hidden />
              {CITY_DISTRICTS.map((d) => (
                <button
                  key={d.id}
                  type="button"
                  className={`ec-district-label ${d.css}${graphics.districtEffects[d.id] ? " is-activated" : ""}`}
                  style={{ left: `${d.x}%`, top: `${d.y}%` }}
                  onClick={() => openDistrict(d.id)}
                >
                  {d.labelRu}
                </button>
              ))}
              <svg className="ec-links" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
                {links.map((l) => {
                  const a = CITY_BUILDINGS.find((b) => b.id === l.from);
                  const b = CITY_BUILDINGS.find((x) => x.id === l.to);
                  if (!a || !b) return null;
                  // Roads: the "flowing" treatment is confined to links touching the focused
                  // building — never a whole-map ambient loop — and gated by the effects layer,
                  // graphics quality, and reduced motion, same as every other transient effect.
                  const touchesFocus = !!focusId && (l.from === focusId || l.to === focusId);
                  const flowing =
                    touchesFocus &&
                    !graphics.reducedMotion &&
                    graphics.frame.layers.isEnabled("effects") &&
                    graphics.settings.effectQuality !== "low";
                  return (
                    <line
                      key={`${l.from}_${l.to}`}
                      className={`ec-link-line${flowing ? " is-flowing" : ""}`}
                      x1={a.x + a.w / 2}
                      y1={a.y + a.h / 2}
                      x2={b.x + b.w / 2}
                      y2={b.y + b.h / 2}
                    />
                  );
                })}
              </svg>
              {cityPath.length >= 2 ? (
                <svg className="ec-wf-route" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
                  <polyline
                    fill="none"
                    stroke="var(--eds-primary)"
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
                </svg>
              ) : null}
              {CITY_BUILDINGS.map((b) => {
                const st = statusById[b.id];
                if (!st) return null;
                return (
                  <CityBuildingTile
                    key={b.id}
                    building={b}
                    status={st}
                    focused={focusId === b.id || pathSet.has(b.id)}
                    hovered={hoverId === b.id}
                    dimmed={isBuildingDimmed(b, st)}
                    effect={graphics.buildingEffects[b.id]}
                    onSelect={() => selectBuilding(b)}
                    onOpen={() => openBuilding(b)}
                    onHover={() => {
                      setHoverId(b.id);
                      graphics.triggerBuildingEffect(b.id, "hover");
                    }}
                    onHoverEnd={() => setHoverId((cur) => (cur === b.id ? null : cur))}
                  />
                );
              })}
            </div>
          </div>
          )}

          <aside className="ec-side">
            <CityMinimap
              focusId={focusId}
              statusById={statusById}
              rect={miniRect}
              onSelect={(b) => selectBuilding(b)}
            />

            <Card title="Недавние" className="ec-nav-card">
              <div className="ec-chip-row">
                {recentIds.map((id) => {
                  const b = CITY_BUILDINGS.find((x) => x.id === id);
                  if (!b) return null;
                  return (
                    <button key={id} type="button" className="ec-jump-chip" onClick={() => selectBuilding(b)}>
                      {b.short}
                    </button>
                  );
                })}
                {!recentIds.length ? <span className="eds-type-helper">Нет недавних</span> : null}
              </div>
            </Card>

            <Card title="Избранное" className="ec-nav-card">
              <div className="ec-chip-row">
                {favoriteIds.map((id) => {
                  const b = CITY_BUILDINGS.find((x) => x.id === id);
                  if (!b) return null;
                  return (
                    <button key={id} type="button" className="ec-jump-chip" onClick={() => selectBuilding(b)}>
                      ★ {b.short}
                    </button>
                  );
                })}
                {!favoriteIds.length ? <span className="eds-type-helper">Добавьте ★ на здании</span> : null}
              </div>
            </Card>

            <Card title="История" className="ec-nav-card">
              <ul className="space-y-1 eds-type-small">
                {historyIds.map((id) => {
                  const b = CITY_BUILDINGS.find((x) => x.id === id);
                  if (!b) return null;
                  return (
                    <li key={id}>
                      <button type="button" className="hover:underline" onClick={() => selectBuilding(b)}>
                        {b.label}
                      </button>
                    </li>
                  );
                })}
                {!historyIds.length ? <li className="eds-type-helper">Пусто</li> : null}
              </ul>
            </Card>

            <Card
              title="Здание"
              className="ec-inspector"
              status={
                focused && focusedOps ? (
                  <Badge
                    tone={
                      focusedOps.health === "critical"
                        ? "danger"
                        : focusedOps.health === "warning"
                          ? "warning"
                          : focusedOps.health === "maintenance"
                            ? "default"
                            : "success"
                    }
                  >
                    {HEALTH_LABEL_RU[focusedOps.health]}
                  </Badge>
                ) : null
              }
            >
              {focused && focusedStatus && focusedOps ? (
                <div className="ec-inspector-body">
                  <div className="ec-inspector-id">
                    <span className={`ec-sil ${buildingIdentity(focused.id).silhouette}`} aria-hidden />
                    <div>
                      <p className="font-semibold">{focused.label}</p>
                      <p className="eds-type-helper">{focusedOps.description}</p>
                    </div>
                  </div>
                  <ul className="ec-inspector-meta eds-type-small">
                    <li>
                      Ответственный: <strong>{focusedOps.owner}</strong>
                    </li>
                    <li>
                      Статус: <strong>{stateLabelRu(focusedStatus)}</strong>
                    </li>
                    <li>
                      Здоровье: <strong>{HEALTH_LABEL_RU[focusedOps.health]}</strong>
                    </li>
                    <li>
                      Активные пользователи: <strong>{focusedOps.activeUsers}</strong>
                    </li>
                    <li>
                      Район: <strong>{getDistrict(focused.district)?.labelRu || focused.district}</strong>
                    </li>
                    <li>
                      Недавняя активность: <strong>{focusedStatus.processLabel}</strong>
                    </li>
                    <li>
                      AI: <strong>{focused.aiAssistant || "City Concierge"}</strong>
                    </li>
                  </ul>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      onClick={() => {
                        if (focused.id === "casino") {
                          navigate(withEmbed("/casino", embed));
                          return;
                        }
                        openBuilding(focused);
                      }}
                    >
                      {focused.id === "casino" ? "Войти в казино" : "Открыть модуль"}
                    </Button>
                    {focusedOps.quickActions
                      .filter((a) => a.id !== "open")
                      .slice(0, 3)
                      .map((a) => (
                        <Button
                          key={a.id}
                          size="sm"
                          variant="secondary"
                          onClick={() => navigate(withEmbed(a.route, embed))}
                        >
                          {a.label}
                        </Button>
                      ))}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        cityNavigation.toggleFavorite(focused.id);
                        setFavTick((t) => t + 1);
                      }}
                    >
                      {cityNavigation.isFavorite(focused.id) ? "Убрать ★" : "В избранное"}
                    </Button>
                  </div>
                  {advisor ? (
                    <div className="ai-advisor-rec ec-inspector-advice">
                      <p className="eds-type-caption">{advisor.assistant}</p>
                      <p className="ai-advisor-obs">{advisor.observation}</p>
                      <p className="ai-advisor-why">{advisor.why}</p>
                      <p className="ai-advisor-impact">Impact: {advisor.impact}</p>
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="eds-type-helper">Выберите здание — клик для выбора, двойной клик для входа.</p>
              )}
            </Card>

            <Card title="Advisor · City">
              <ul className="space-y-2">
                {cityAdvice.map((s) => (
                  <li key={s.id}>
                    <button
                      type="button"
                      className="ec-advice-hit"
                      onClick={() => {
                        void telemetry.userActivity(`city_advice:${s.id}`);
                        navigate(withEmbed(s.route, embed));
                      }}
                    >
                      <span className="font-medium eds-type-small">{s.action}</span>
                      <span className="block eds-type-helper">{s.observation}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          </aside>
        </div>
      </div>
      {showDevOverlay ? (
        <CityDevOverlay
          perf={graphics.perf}
          objects={Object.values(graphics.frame.stats).reduce((sum, n) => sum + n, 0)}
          visibleBuildings={visibleBuildingsCount}
          animationQueueLength={graphics.animationQueueLength}
          settings={graphics.settings}
          onQualityChange={(quality) => graphics.updateSettings(defaultGraphicsSettings(quality))}
          onClose={() => setShowDevOverlay(false)}
        />
      ) : null}
    </WorkspaceLayout>
  );
}

function GlanceChip({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "warning" | "danger" | "info" | "default";
}) {
  return (
    <span className="ec-glance-chip">
      <Badge tone={tone}>{value}</Badge>
      <span className="eds-type-caption">{label}</span>
    </span>
  );
}

function CityBuildingTile({
  building,
  status,
  focused,
  hovered,
  dimmed,
  effect,
  onSelect,
  onOpen,
  onHover,
  onHoverEnd,
}: {
  building: CityBuilding;
  status: CityLiveStatus;
  focused: boolean;
  hovered: boolean;
  dimmed: boolean;
  effect?: ResolvedEffect;
  onSelect: () => void;
  onOpen: () => void;
  onHover: () => void;
  onHoverEnd: () => void;
}) {
  const visual = resolveVisualState(status);
  const identity = buildingIdentity(building.id);
  const plaza = building.kind === "plaza";
  const effectClass = effect ? ` ${effect.className}` : "";
  const ops = buildingOps(building.id, building.route);
  const health = healthFromLiveTone(status.tone, status.notifications, status.tasks);
  return (
    <button
      type="button"
      className={`ec-building ${identity.districtClass} ${CITY_STATE_LABELS[visual].css}${focused ? " is-focused" : ""}${hovered ? " is-hovered" : ""}${dimmed ? " is-dimmed" : ""}${status.aiActive ? " has-ai" : ""}${plaza ? " is-plaza" : ""}${health === "online" ? " is-online" : ""}${effectClass}`}
      style={{
        left: `${building.x}%`,
        top: `${building.y}%`,
        width: `${building.w}%`,
        height: `${building.h}%`,
      }}
      onClick={onSelect}
      onDoubleClick={onOpen}
      onMouseEnter={onHover}
      onMouseLeave={onHoverEnd}
      onFocus={onHover}
      aria-label={`${building.label} — ${HEALTH_LABEL_RU[health]}`}
      title={`${building.label}\n${HEALTH_LABEL_RU[health]} · ${ops.owner}\nUsers: ${ops.activeUsers}\n${ops.description}`}
    >
      <span className={`ec-online-dot ec-health-${health}`} title={HEALTH_LABEL_RU[health]} aria-hidden />
      <span className={`ec-sil ${identity.silhouette}`} aria-hidden />
      <span className="ec-building-label">{building.short}</span>
      <span className="ec-building-state">{HEALTH_LABEL_RU[health]}</span>
      <span className="ec-building-meta" aria-hidden>
        {ops.activeUsers}
      </span>
      {status.notifications > 0 ? <span className="ec-badge">{status.notifications}</span> : null}
      {status.aiActive ? <span className="ec-ai-dot" title="AI активность" /> : null}
      {status.tasks > 0 ? <span className="ec-tasks">{status.tasks}</span> : null}
    </button>
  );
}

function CityMinimap({
  focusId,
  statusById,
  rect,
  onSelect,
}: {
  focusId: CityBuildingId | null;
  statusById: Record<CityBuildingId, CityLiveStatus>;
  rect: { left: number; top: number; width: number; height: number };
  onSelect: (b: CityBuilding) => void;
}) {
  return (
    <Card title="Мини-карта">
      <div className="ec-minimap" role="img" aria-label="Мини-карта города">
        <div
          className="ec-mini-viewport"
          style={{
            left: `${rect.left}%`,
            top: `${rect.top}%`,
            width: `${rect.width}%`,
            height: `${rect.height}%`,
          }}
          aria-hidden
        />
        {CITY_BUILDINGS.map((b) => (
          <button
            key={b.id}
            type="button"
            className={`ec-mini-dot ${CITY_STATE_LABELS[resolveVisualState(statusById[b.id]!)].css}${focusId === b.id ? " is-focused" : ""}`}
            style={{ left: `${b.x + b.w / 2}%`, top: `${b.y + b.h / 2}%` }}
            onClick={() => onSelect(b)}
            aria-label={`Go to ${b.label}`}
            title={`${b.label} · ${stateLabelRu(statusById[b.id]!)}`}
          />
        ))}
      </div>
    </Card>
  );
}
