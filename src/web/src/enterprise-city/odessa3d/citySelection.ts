/**
 * Unified selection model for 2D/3D Interactive City.
 */

import type { CityEntity } from "./types";
import { getCityEntity } from "./cityEntityRegistry";

type Listener = (entity: CityEntity | null) => void;

export class CitySelectionService {
  private selectedId: string | null = null;
  private listeners = new Set<Listener>();

  getSelected(): CityEntity | null {
    return this.selectedId ? getCityEntity(this.selectedId) ?? null : null;
  }

  getSelectedId(): string | null {
    return this.selectedId;
  }

  select(entityId: string | null) {
    this.selectedId = entityId;
    for (const fn of this.listeners) fn(this.getSelected());
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }
}

export const citySelection = new CitySelectionService();
