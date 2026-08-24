/**
 * Odessa 3D interaction layer — picking, highlight, enterprise binding.
 */

export type {
  EntityBindingResult,
  InteractionDiagnostics,
  InteractionSnapshot,
  PickBindingStatus,
  PickableBounds,
  PickableEntity,
  SceneGraphAudit,
} from "./types";
export { makePickId, sanitizePickToken } from "./pickIds";
export { PickRegistry } from "./pickRegistry";
export { bindPickableEntity, bindPickableFromLookup, collectExactBuildingIds, bindingCounts } from "./entityBinding";
export { MANUAL_ODESSA_ENTITY_MAP } from "./manualEntityMap";
export { HighlightController, HOVER_HIGHLIGHT_HEX, SELECT_HIGHLIGHT_HEX, HOVER_EMISSIVE, SELECT_EMISSIVE } from "./highlightController";
export { isInteractivePickMesh, EXCLUDED_PICK_NAME_RE, MAX_INTERACTIVE_FOOTPRINT_M } from "./pickFilter";
export { isFavorite, toggleFavorite, listFavorites } from "./favorites";
export { objectPanelFacts, NO_DATA } from "./objectPanelFacts";
export {
  CLICK_DRAG_THRESHOLD_PX,
  exceedsDragThreshold,
  isClickGesture,
  pointerDeltaPx,
} from "./pointerGesture";
export {
  BROADPHASE_MESH_THRESHOLD,
  HOVER_RAYCAST_INTERVAL_MS,
  HOVER_RAYCAST_MAX_PER_SEC,
  createRaycastMeter,
  pointerToNdc,
  recordRaycast,
} from "./pickRaycast";
export { auditSceneGraph, emptySceneGraphAudit } from "./sceneAudit";
