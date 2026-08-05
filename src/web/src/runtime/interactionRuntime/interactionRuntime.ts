/**
 * Enterprise Interaction Runtime — Sprint 29.6.
 * Interaction layer between users, AI, and living Enterprise City.
 */

import { commandRuntime } from "@/runtime/commandRuntime";
import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import { spatialRuntime } from "@/runtime/spatialRuntime";
import { lifeEngine } from "@/runtime/lifeEngine";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID } from "@/runtime/businessNetwork";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { automationEngine } from "@/runtime/automation";
import {
  INTERACTION_RUNTIME_VERSION,
  type InteractionActionId,
  type InteractionObjectKind,
  type InteractionTarget,
  type SelectionMode,
} from "./interactionTypes";
import { interactionEvents, publishInteractionEvent } from "./interactionEvents";
import { interactionPermissions } from "./interactionPermissions";
import { interactionRegistry } from "./interactionRegistry";
import { interactionSessionStore, interactionHistory } from "./interactionSession";
import { selectionEngine } from "./selectionEngine";
import { navigationEngine } from "./navigationEngine";
import { interactionCache } from "./interactionCache";
import { executeContextAction, contextActionsForTarget } from "./contextActions";

let booted = false;

function registerCommands() {
  commandRuntime.register({
    id: "interaction_open",
    action: "open_interaction_runtime",
    label: "Open Interaction Runtime",
    kind: "navigate",
    keywords: ["interaction", "selection", "context action", "city interact"],
    route: "/interactions",
    permission: "*",
  });
  commandRuntime.register({
    id: "interaction_select",
    action: "select_city_object",
    label: "Select City Object",
    kind: "system",
    keywords: ["select", "building", "citizen"],
    permission: "*",
    handler: async (_ctx, args) => {
      const kind = String(args.kind || "building") as InteractionObjectKind;
      const id = String(args.id || "hub");
      const t = interactionRuntime.select(kind, id);
      return { ok: !!t, message: t?.label || id, error: t ? undefined : "not_found" };
    },
  });
  commandRuntime.register({
    id: "interaction_action",
    action: "execute_context_action",
    label: "Execute Context Action",
    kind: "system",
    keywords: ["action", "open", "meeting", "workflow"],
    permission: "*",
    handler: async (_ctx, args) => {
      const actionId = String(args.actionId || "open_building") as InteractionActionId;
      const res = interactionRuntime.execute(actionId, undefined, args as Record<string, unknown>);
      return { ok: res.ok, message: res.message, error: res.error, route: res.route };
    },
  });
}

export const interactionRuntime = {
  version: INTERACTION_RUNTIME_VERSION,

  startup() {
    if (booted) return this.stats();
    commandRuntime.startup();
    workflowRuntime.startup();
    automationEngine.startup();
    businessNetworkEngine.startup();
    digitalCitizenEngine.startup();
    lifeEngine.startup();
    assetRuntime.startup();
    spatialRuntime.startup();
    cityVisualizationRuntime.startup();
    interactionCache.clear();
    selectionEngine.clear();
    navigationEngine.clear();
    interactionHistory.clear();
    interactionSessionStore.clear();
    interactionEvents.clear();
    this.beginSession({ actorCitizenId: EDC_CITIZEN_OWNER, surface: "city" });
    navigationEngine.catalog();
    registerCommands();
    booted = true;
    enterpriseEventBus.publish({
      type: "runtime_update",
      source: "system",
      payload: { stream: "interaction_runtime", ready: true, version: INTERACTION_RUNTIME_VERSION },
    });
    return this.stats();
  },

  isReady() {
    return booted;
  },

  beginSession(input?: {
    actorCitizenId?: string;
    surface?: "city" | "desktop" | "command_center" | "mobile" | "twin_2d" | "twin_3d" | "api";
  }) {
    const session = interactionSessionStore.start({
      actorCitizenId: input?.actorCitizenId || EDC_CITIZEN_OWNER,
      surface: input?.surface || "city",
    });
    interactionSessionStore.patchContext({
      actorCompanyId: EBN_HOME_PROFILE_ID,
      path: "/enterprise-city",
    });
    interactionCache.putContext(session.context);
    publishInteractionEvent("ContextChanged", { sessionId: session.id, surface: session.surface });
    return session;
  },

  endSession(sessionId?: string) {
    return interactionSessionStore.end(sessionId);
  },

  session() {
    if (!booted) this.startup();
    return interactionSessionStore.active();
  },

  sessions() {
    if (!booted) this.startup();
    return interactionSessionStore.list();
  },

  context() {
    if (!booted) this.startup();
    return interactionSessionStore.active()?.context || interactionCache.getContext();
  },

  setContext(patch: Parameters<typeof interactionSessionStore.patchContext>[0]) {
    if (!booted) this.startup();
    const ctx = interactionSessionStore.patchContext(patch);
    if (ctx) {
      interactionCache.putContext(ctx);
      publishInteractionEvent("ContextChanged", {
        path: ctx.path,
        focusId: ctx.focus?.id,
        selectionCount: ctx.selectionIds.length,
      });
    }
    return ctx;
  },

  catalog() {
    if (!booted) this.startup();
    return navigationEngine.catalog();
  },

  /** Selection */
  selection() {
    if (!booted) this.startup();
    return selectionEngine.get();
  },

  setSelectionMode(mode: SelectionMode) {
    if (!booted) this.startup();
    const sel = selectionEngine.setMode(mode);
    interactionCache.putSelection(sel);
    return sel;
  },

  select(kind: InteractionObjectKind, id: string) {
    if (!booted) this.startup();
    const target = navigationEngine.find(kind, id);
    if (!target) return null;
    const sel = selectionEngine.select(target);
    interactionCache.putSelection(sel);
    interactionSessionStore.setFocus(target);
    interactionSessionStore.patchContext({ selectionIds: [target.id] });
    publishInteractionEvent("ObjectSelected", { kind, id, label: target.label });
    interactionHistory.recordEvent("ObjectSelected", { target, result: "ok" });
    return target;
  },

  toggleSelect(kind: InteractionObjectKind, id: string) {
    if (!booted) this.startup();
    const target = navigationEngine.find(kind, id);
    if (!target) return null;
    const sel = selectionEngine.toggle(target);
    interactionCache.putSelection(sel);
    interactionSessionStore.patchContext({
      focus: sel.primary,
      selectionIds: sel.targets.map((t) => t.id),
    });
    publishInteractionEvent("ObjectSelected", { kind, id, multi: true });
    return sel;
  },

  selectArea(area: { minX: number; minY: number; maxX: number; maxY: number }) {
    if (!booted) this.startup();
    const sel = selectionEngine.selectArea(this.catalog(), area);
    interactionCache.putSelection(sel);
    interactionSessionStore.patchContext({
      focus: sel.primary,
      selectionIds: sel.targets.map((t) => t.id),
    });
    return sel;
  },

  selectHierarchy(kind: InteractionObjectKind, id: string) {
    if (!booted) this.startup();
    const root = navigationEngine.find(kind, id);
    if (!root) return null;
    const sel = selectionEngine.selectHierarchy(root, this.catalog());
    interactionCache.putSelection(sel);
    interactionSessionStore.patchContext({
      focus: sel.primary,
      selectionIds: sel.targets.map((t) => t.id),
    });
    return sel;
  },

  clearSelection() {
    if (!booted) this.startup();
    const sel = selectionEngine.clearSelection();
    interactionCache.putSelection(sel);
    interactionSessionStore.patchContext({ focus: undefined, selectionIds: [] });
    return sel;
  },

  /** Search & navigation */
  search(query: string, limit?: number) {
    if (!booted) this.startup();
    return navigationEngine.globalSearch(query, limit);
  },

  contextSearch(query: string, kind?: InteractionObjectKind, limit?: number) {
    if (!booted) this.startup();
    return navigationEngine.contextSearch(query, kind, limit);
  },

  nearby(buildingId: string, limit?: number) {
    if (!booted) this.startup();
    return navigationEngine.nearby(buildingId, limit);
  },

  businessDiscovery(query?: string, limit?: number) {
    if (!booted) this.startup();
    return navigationEngine.businessDiscovery(query, limit);
  },

  navigationHistory(limit?: number) {
    if (!booted) this.startup();
    return navigationEngine.history(limit);
  },

  quickJump(kind: InteractionObjectKind, id: string) {
    if (!booted) this.startup();
    const jump = navigationEngine.quickJump(kind, id);
    if (jump) {
      this.select(kind, id);
      this.setContext({ path: jump.path, focus: jump.target });
    }
    return jump;
  },

  /** Context actions */
  actionsFor(target: InteractionTarget) {
    if (!booted) this.startup();
    return contextActionsForTarget(target);
  },

  actionsForSelection() {
    if (!booted) this.startup();
    const primary = selectionEngine.get().primary;
    return primary ? contextActionsForTarget(primary) : interactionRegistry.actions();
  },

  execute(actionId: InteractionActionId, target?: InteractionTarget, args: Record<string, unknown> = {}) {
    if (!booted) this.startup();
    const resolved =
      target ||
      selectionEngine.get().primary ||
      (args.kind && args.id
        ? navigationEngine.find(String(args.kind) as InteractionObjectKind, String(args.id))
        : undefined);
    return executeContextAction(actionId, resolved || undefined, args);
  },

  open(kind: InteractionObjectKind, id: string) {
    if (!booted) this.startup();
    const target = this.select(kind, id);
    if (!target) return { ok: false, actionId: "navigate" as const, error: "not_found" };
    const actionMap: Partial<Record<InteractionObjectKind, InteractionActionId>> = {
      building: "open_building",
      company: "open_company",
      citizen: "open_citizen",
      asset: "open_asset",
      vehicle: "open_vehicle",
      district: "open_district",
      project: "open_project",
      meeting: "open_meeting",
      ai_agent: "launch_ai",
    };
    return this.execute(actionMap[kind] || "navigate", target);
  },

  history(limit?: number) {
    if (!booted) this.startup();
    return interactionHistory.list(limit);
  },

  registry: interactionRegistry,
  permissions: interactionPermissions,
  events: interactionEvents,
  cache: interactionCache,

  stats() {
    if (!booted) this.startup();
    const sel = selectionEngine.get();
    return {
      version: INTERACTION_RUNTIME_VERSION,
      sessions: interactionSessionStore.list().length,
      activeSession: interactionSessionStore.active()?.id || null,
      catalog: navigationEngine.catalog().length,
      selection: sel.targets.length,
      selectionMode: sel.mode,
      history: interactionHistory.list(200).length,
      navHistory: navigationEngine.history(40).length,
      actions: interactionRegistry.actions().length,
      cache: interactionCache.stats(),
      events: interactionEvents.list(200).length,
    };
  },

  inspectorSnapshot() {
    if (!booted) this.startup();
    return {
      version: INTERACTION_RUNTIME_VERSION,
      session: this.session(),
      context: this.context(),
      selection: this.selection(),
      actions: this.actionsForSelection(),
      searchSample: this.search("hub", 5),
      nearbySample: this.nearby("hub", 5),
      history: this.history(20),
      navHistory: this.navigationHistory(10),
      stats: this.stats(),
      events: interactionEvents.list(25),
    };
  },

  __resetForTests() {
    interactionCache.clear();
    selectionEngine.clear();
    navigationEngine.clear();
    interactionHistory.clear();
    interactionSessionStore.clear();
    interactionEvents.clear();
    booted = false;
  },
};
