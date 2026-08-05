/**
 * Enterprise Interaction Runtime types — Sprint 29.6.
 * Runtime-driven interaction layer for Web/Desktop/Mobile/2D/3D clients.
 */

export const INTERACTION_RUNTIME_VERSION = "29.6";
export const INTERACTION_PERSIST_KEY = "ews_interaction_runtime_v1";
export const INTERACTION_API_PREFIX = "/api/enterprise-interaction/v1";

export type InteractionObjectKind =
  | "building"
  | "company"
  | "citizen"
  | "asset"
  | "project"
  | "vehicle"
  | "ai_agent"
  | "district"
  | "meeting";

export type InteractionActionId =
  | "open_company"
  | "open_citizen"
  | "open_asset"
  | "open_building"
  | "start_workflow"
  | "assign_task"
  | "invite_partner"
  | "launch_ai"
  | "create_meeting"
  | "navigate"
  | "open_district"
  | "open_project"
  | "open_meeting"
  | "open_vehicle";

export type InteractionEventName =
  | "ObjectSelected"
  | "ObjectOpened"
  | "ActionExecuted"
  | "WorkflowStarted"
  | "NavigationChanged"
  | "ContextChanged"
  | "SelectionChanged";

export type SelectionMode = "single" | "multi" | "area" | "hierarchy";

export type InteractionTarget = {
  kind: InteractionObjectKind;
  id: string;
  label: string;
  buildingId?: string;
  districtId?: string;
  companyId?: string;
  route?: string;
  meta?: Record<string, unknown>;
};

export type ContextActionDef = {
  id: InteractionActionId;
  label: string;
  /** Object kinds this action applies to (empty = always contextual) */
  targetKinds: InteractionObjectKind[];
  permission: string;
  keywords: string[];
};

export type InteractionContext = {
  actorCitizenId?: string;
  actorCompanyId?: string;
  surface: "city" | "desktop" | "command_center" | "mobile" | "twin_2d" | "twin_3d" | "api";
  focus?: InteractionTarget;
  selectionIds: string[];
  path: string;
  vars: Record<string, unknown>;
  updatedAt: string;
};

export type InteractionSession = {
  id: string;
  actorCitizenId?: string;
  surface: InteractionContext["surface"];
  startedAt: string;
  endedAt?: string;
  active: boolean;
  context: InteractionContext;
  selectionMode: SelectionMode;
};

export type InteractionHistoryEntry = {
  id: string;
  at: string;
  sessionId?: string;
  event: InteractionEventName | "action" | "search" | "navigate";
  actionId?: InteractionActionId;
  target?: InteractionTarget;
  result?: "ok" | "denied" | "error";
  message?: string;
  payload?: Record<string, unknown>;
};

export type SelectionState = {
  mode: SelectionMode;
  primary?: InteractionTarget;
  targets: InteractionTarget[];
  area?: { minX: number; minY: number; maxX: number; maxY: number };
  hierarchyRootId?: string;
  revision: number;
  updatedAt: string;
};

export type NavigationEntry = {
  id: string;
  at: string;
  path: string;
  target?: InteractionTarget;
  label: string;
};

export type SearchHit = {
  target: InteractionTarget;
  score: number;
  source: "global" | "context" | "nearby" | "business";
};

export type ActionResult = {
  ok: boolean;
  actionId: InteractionActionId;
  message?: string;
  error?: string;
  route?: string;
  data?: Record<string, unknown>;
};
