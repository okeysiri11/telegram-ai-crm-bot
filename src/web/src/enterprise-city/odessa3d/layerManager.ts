/**
 * LayerManager — toggle visibility without reloading base geometry.
 */

import type { OdessaManifestLayer } from "./types";

export class LayerManager {
  private visible = new Map<string, boolean>();
  private layers: OdessaManifestLayer[] = [];

  bootstrap(layers: OdessaManifestLayer[]) {
    this.layers = layers;
    for (const l of layers) {
      if (!this.visible.has(l.id)) {
        this.visible.set(l.id, l.defaultVisible !== false);
      }
    }
  }

  isVisible(layerId: string): boolean {
    return this.visible.get(layerId) ?? true;
  }

  setVisible(layerId: string, on: boolean) {
    this.visible.set(layerId, on);
  }

  toggle(layerId: string): boolean {
    const next = !this.isVisible(layerId);
    this.visible.set(layerId, next);
    return next;
  }

  activeLayerIds(): string[] {
    return [...this.visible.entries()].filter(([, v]) => v).map(([k]) => k);
  }

  list(): { id: string; label: string; visible: boolean; dynamic?: boolean }[] {
    return this.layers.map((l) => ({
      id: l.id,
      label: l.label,
      visible: this.isVisible(l.id),
      dynamic: l.dynamic,
    }));
  }
}
