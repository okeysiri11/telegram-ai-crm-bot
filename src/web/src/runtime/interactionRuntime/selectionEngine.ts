/**
 * Selection engine — single · multi · area · hierarchy — Sprint 29.6.
 */

import type { InteractionTarget, SelectionMode, SelectionState } from "./interactionTypes";
import { publishInteractionEvent } from "./interactionEvents";

function now() {
  return new Date().toISOString();
}

let state: SelectionState = {
  mode: "single",
  targets: [],
  revision: 0,
  updatedAt: now(),
};

function bump(partial: Partial<SelectionState>): SelectionState {
  state = {
    ...state,
    ...partial,
    targets: partial.targets ?? state.targets,
    revision: state.revision + 1,
    updatedAt: now(),
  };
  publishInteractionEvent("SelectionChanged", {
    mode: state.mode,
    count: state.targets.length,
    primaryId: state.primary?.id,
    revision: state.revision,
  });
  return { ...state, targets: [...state.targets] };
}

export const selectionEngine = {
  clear() {
    state = { mode: "single", targets: [], revision: 0, updatedAt: now() };
  },

  get(): SelectionState {
    return { ...state, targets: [...state.targets] };
  },

  setMode(mode: SelectionMode) {
    return bump({ mode });
  },

  /** Single selection (replaces) */
  select(target: InteractionTarget) {
    return bump({
      mode: "single",
      primary: target,
      targets: [target],
      area: undefined,
      hierarchyRootId: undefined,
    });
  },

  /** Multi — toggle membership */
  toggle(target: InteractionTarget) {
    const exists = state.targets.some((t) => t.kind === target.kind && t.id === target.id);
    const targets = exists
      ? state.targets.filter((t) => !(t.kind === target.kind && t.id === target.id))
      : [...state.targets, target];
    return bump({
      mode: "multi",
      primary: targets[0],
      targets,
    });
  },

  multi(targets: InteractionTarget[]) {
    return bump({
      mode: "multi",
      primary: targets[0],
      targets: [...targets],
    });
  },

  /** Area selection — filter candidates by plane bounds (x/y on meta) */
  selectArea(
    candidates: InteractionTarget[],
    area: { minX: number; minY: number; maxX: number; maxY: number },
  ) {
    const hit = candidates.filter((t) => {
      const x = Number(t.meta?.x);
      const y = Number(t.meta?.y);
      if (Number.isNaN(x) || Number.isNaN(y)) return false;
      return x >= area.minX && x <= area.maxX && y >= area.minY && y <= area.maxY;
    });
    return bump({
      mode: "area",
      area,
      primary: hit[0],
      targets: hit,
    });
  },

  /** Hierarchy — select root + descendants (by buildingId/districtId/parent in meta) */
  selectHierarchy(root: InteractionTarget, candidates: InteractionTarget[]) {
    const rootId = root.id;
    const related = candidates.filter((t) => {
      if (t.id === rootId && t.kind === root.kind) return true;
      if (root.kind === "district") {
        return t.districtId === root.id || t.districtId === root.districtId;
      }
      if (root.kind === "building") {
        return t.buildingId === root.id || t.id === root.id;
      }
      if (root.kind === "company") {
        return t.companyId === root.id || t.id === root.id;
      }
      return t.meta?.parentId === rootId;
    });
    return bump({
      mode: "hierarchy",
      hierarchyRootId: rootId,
      primary: root,
      targets: related.length ? related : [root],
    });
  },

  clearSelection() {
    return bump({
      primary: undefined,
      targets: [],
      area: undefined,
      hierarchyRootId: undefined,
    });
  },
};
