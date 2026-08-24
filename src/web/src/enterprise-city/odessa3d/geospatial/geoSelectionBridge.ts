/**
 * Shared 2D/3D geographic selection. Does not rebuild the 2D map.
 * Does not invent WGS84 from the 0–100 city plane.
 */

import type { GeoCoordinate } from "./types";

export type GeoSelectionSource = "2d" | "3d" | null;

export type GeoBridgeIntent = "idle" | "show-2d" | "show-3d";

export type GeoSelectionState = {
  entityId: string | null;
  source: GeoSelectionSource;
  geo: GeoCoordinate | null;
  intent: GeoBridgeIntent;
};

type Listener = (state: GeoSelectionState) => void;

const empty: GeoSelectionState = { entityId: null, source: null, geo: null, intent: "idle" };

class GeoSelectionBridge {
  private state: GeoSelectionState = { ...empty };
  private listeners = new Set<Listener>();

  get(): GeoSelectionState {
    return this.state;
  }

  setFrom3d(entityId: string | null, geo: GeoCoordinate | null) {
    this.state = { entityId, source: entityId || geo ? "3d" : null, geo, intent: "idle" };
    this.emit();
  }

  setFrom2d(entityId: string | null, geo: GeoCoordinate | null = null) {
    this.state = { entityId, source: entityId ? "2d" : null, geo, intent: "idle" };
    this.emit();
  }

  requestShowIn2d(geo: GeoCoordinate | null, entityId: string | null = null) {
    if (!geo) return;
    this.state = { entityId, source: "3d", geo, intent: "show-2d" };
    this.emit();
  }

  requestShowIn3d(geo: GeoCoordinate | null, entityId: string | null = null) {
    if (!geo) return;
    this.state = { entityId, source: "2d", geo, intent: "show-3d" };
    this.emit();
  }

  consumeShow3d(): GeoCoordinate | null {
    if (this.state.intent !== "show-3d" || !this.state.geo) return null;
    const geo = this.state.geo;
    this.state = { ...this.state, intent: "idle" };
    return geo;
  }

  consumeShow2d(): GeoCoordinate | null {
    if (this.state.intent !== "show-2d" || !this.state.geo) return null;
    const geo = this.state.geo;
    this.state = { ...this.state, intent: "idle" };
    return geo;
  }

  clear() {
    this.state = { ...empty };
    this.emit();
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private emit() {
    for (const fn of this.listeners) fn(this.state);
  }
}

export const geoSelectionBridge = new GeoSelectionBridge();
