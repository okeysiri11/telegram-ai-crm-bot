/**
 * Tile streaming — progressive load with camera priority + heavy-chunk hysteresis.
 */

import * as THREE from "three";
import type { GeoTransform } from "./geoTransform";
import type { OdessaManifest, OdessaManifestTile } from "./types";
import type { ProgressiveAssetLoader } from "./assetLoader";
import { scoreLodPriority, isSeaOrCoastProtected, lodThresholdsFor } from "./lod";

export type TileStreamState = {
  tileId: string;
  distanceM: number;
  inFrustum: boolean;
  active: boolean;
  layerId: string;
  sizeMb: number;
  score: number;
};

export type TileStreamSettings = {
  maxActiveTiles: number;
  loadDistanceM: number;
  unloadDistanceM: number;
  heavyLoadDistanceM: number;
  heavyUnloadDistanceM: number;
  targetX?: number;
  targetZ?: number;
  cityDiagonalM?: number;
  profile?: "auto" | "low" | "medium" | "high";
  lodBias?: number;
};

export class TileStreamingController {
  private activeTiles = new Set<string>();
  private heavyLoaded = new Set<string>();
  private manifest: OdessaManifest;
  private geo: GeoTransform;
  private loader: ProgressiveAssetLoader;
  private useSceneSpace: boolean;
  /** Non-heavy REAL GLB tiles stay mounted once loaded. */
  readonly retainLoadedTiles = true;
  private readonly essentialLayers = new Set(["city"]);
  private tileCenters = new Map<string, THREE.Vector3>();

  constructor(manifest: OdessaManifest, geo: GeoTransform, loader: ProgressiveAssetLoader) {
    this.manifest = manifest;
    this.geo = geo;
    this.loader = loader;
    this.useSceneSpace = manifest.tiles.some((t) => !!t.centerScene);
  }

  tileById(id: string): OdessaManifestTile | undefined {
    return this.manifest.tiles.find((t) => t.id === id);
  }

  private tileLayer(tile: OdessaManifestTile): string {
    return tile.assets[0]?.layer || "city";
  }

  private tileSizeMb(tile: OdessaManifestTile): number {
    return tile.assets.reduce((s, a) => s + (a.sizeMb ?? 0), 0);
  }

  private tileCenter(tile: OdessaManifestTile): THREE.Vector3 {
    const cached = this.tileCenters.get(tile.id);
    if (cached) return cached;
    let center: THREE.Vector3;
    if (tile.centerScene) {
      center = new THREE.Vector3(tile.centerScene.x, 0, tile.centerScene.z);
    } else {
      const geoPt = this.geo.geoToScene(tile.center.lat, tile.center.lng);
      center = new THREE.Vector3(geoPt.x, geoPt.y, geoPt.z);
    }
    this.tileCenters.set(tile.id, center);
    return center;
  }

  private tileDistance(camera: THREE.Camera, tile: OdessaManifestTile): number {
    const center = this.tileCenter(tile);
    if (this.useSceneSpace || tile.centerScene) {
      const dx = camera.position.x - center.x;
      const dz = camera.position.z - center.z;
      return Math.hypot(dx, dz);
    }
    const camGeo = this.geo.sceneToGeo(camera.position.x, camera.position.y, camera.position.z);
    return this.geo.distanceMeters(camGeo, tile.center);
  }

  private cameraForwardDot(camera: THREE.Camera, tile: OdessaManifestTile): number {
    const center = this.tileCenter(tile);
    const toTile = new THREE.Vector3().subVectors(center, camera.position);
    toTile.y = 0;
    if (toTile.lengthSq() < 1) return 1;
    toTile.normalize();
    const forward = new THREE.Vector3();
    camera.getWorldDirection(forward);
    forward.y = 0;
    forward.normalize();
    return forward.dot(toTile);
  }

  evaluate(camera: THREE.Camera, settings?: Pick<TileStreamSettings, "targetX" | "targetZ" | "cityDiagonalM" | "profile" | "lodBias">): TileStreamState[] {
    const frustum = new THREE.Frustum();
    const matrix = new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustum.setFromProjectionMatrix(matrix);
    const priority = new Set(this.manifest.priorityTiles || []);
    const targetX = settings?.targetX ?? camera.position.x;
    const targetZ = settings?.targetZ ?? camera.position.z;
    const thresholds = lodThresholdsFor(settings?.profile ?? "medium", settings?.cityDiagonalM, settings?.lodBias);

    return this.manifest.tiles.map((tile) => {
      const center = this.tileCenter(tile);
      const sphere = new THREE.Sphere(center, tile.radiusM ?? 600);
      const distanceM = this.tileDistance(camera, tile);
      const inFrustum = frustum.intersectsSphere(sphere);
      const layerId = this.tileLayer(tile);
      const sizeMb = this.tileSizeMb(tile);
      const toTarget = Math.hypot(center.x - targetX, center.z - targetZ);
      const score = scoreLodPriority({
        id: tile.id,
        distanceM,
        inFrustum,
        nearTarget: toTarget < thresholds.targetProtectM,
        manifestPriority: priority.has(tile.id),
        seaProtected: isSeaOrCoastProtected(tile.id, layerId),
        screenImportant: false,
        layerId,
        sizeMb,
        cameraForwardDot: this.cameraForwardDot(camera, tile),
      });
      return {
        tileId: tile.id,
        distanceM,
        inFrustum,
        active: this.activeTiles.has(tile.id),
        layerId,
        sizeMb,
        score,
      };
    });
  }

  schedule(camera: THREE.Camera, settings: TileStreamSettings, opts?: { pauseNewActivations?: boolean; pauseUnload?: boolean }) {
    const states = this.evaluate(camera, settings);
    if (opts?.pauseNewActivations) {
      if (!opts.pauseUnload) this.maybeUnloadHeavy(camera, settings);
      return [...this.activeTiles];
    }
    const priority = new Set(this.manifest.priorityTiles || []);
    const sorted = [...states].sort((a, b) => a.score - b.score);

    for (const st of sorted) {
      if (this.activeTiles.has(st.tileId)) continue;
      const isHeavy = st.layerId === "heavy";
      const loadDist = isHeavy ? settings.heavyLoadDistanceM : settings.loadDistanceM;
      const near =
        st.inFrustum ||
        st.distanceM < loadDist ||
        priority.has(st.tileId) ||
        (!isHeavy && st.distanceM < settings.unloadDistanceM * 0.55);
      if (near && this.activeTiles.size < settings.maxActiveTiles) {
        this.activateTile(st.tileId, priority.has(st.tileId));
      }
    }

    let batch = 0;
    if (this.loader.allowsPrefetch()) {
      for (const st of sorted) {
        if (this.activeTiles.has(st.tileId)) continue;
        if (st.layerId === "heavy" && st.distanceM > settings.heavyLoadDistanceM) continue;
        this.activateTile(st.tileId, false, { prefetch: true });
        batch += 1;
        if (batch >= 2) break;
      }
    }

    if (!opts?.pauseUnload) this.maybeUnloadHeavy(camera, settings);

    return [...this.activeTiles];
  }

  private maybeUnloadHeavy(camera: THREE.Camera, settings: TileStreamSettings) {
    const targetX = settings.targetX ?? camera.position.x;
    const targetZ = settings.targetZ ?? camera.position.z;
    const thresholds = lodThresholdsFor(settings.profile ?? "medium", settings.cityDiagonalM, settings.lodBias);
    for (const tileId of [...this.heavyLoaded]) {
      const tile = this.tileById(tileId);
      if (!tile) continue;
      if (isSeaOrCoastProtected(tileId, this.tileLayer(tile))) continue;
      const center = this.tileCenter(tile);
      const toTarget = Math.hypot(center.x - targetX, center.z - targetZ);
      if (toTarget < thresholds.targetProtectM) continue;
      const dist = this.tileDistance(camera, tile);
      if (dist <= settings.heavyUnloadDistanceM) continue;
      if (dist <= thresholds.farM) continue;
      for (const asset of tile.assets) {
        this.loader.unloadAsset(asset.id, { disposeSceneGraph: false });
      }
      this.heavyLoaded.delete(tileId);
      this.activeTiles.delete(tileId);
    }
  }

  bootstrapPriorityTiles() {
    for (const id of this.manifest.priorityTiles || []) {
      this.activateTile(id, true);
    }
    if (!this.manifest.priorityTiles?.length && this.manifest.tiles[0]) {
      this.activateTile(this.manifest.tiles[0].id, true);
    }
  }

  private activateTile(tileId: string, front: boolean, opts?: { prefetch?: boolean }) {
    const tile = this.tileById(tileId);
    if (!tile || this.activeTiles.has(tileId)) return;
    this.activeTiles.add(tileId);
    const layerId = this.tileLayer(tile);
    if (layerId === "heavy") this.heavyLoaded.add(tileId);
    const ids = tile.assets
      .slice()
      .sort((a, b) => (a.priority ?? 9) - (b.priority ?? 9))
      .map((a) => a.id);
    for (const id of ids) {
      this.loader.enqueue(id, front, opts?.prefetch ? { prefetch: true } : undefined);
    }
  }

  releaseTileIfUnloaded(tileId: string): boolean {
    const tile = this.tileById(tileId);
    if (!tile) return false;
    const busy = tile.assets.some((a) => {
      const row = this.loader.registry.get(a.id);
      if (!row) return false;
      return row.status === "loaded" || row.status === "loading" || row.lifecycle === "waiting_parse" || row.lifecycle === "parsing";
    });
    if (busy) return false;
    this.activeTiles.delete(tileId);
    this.heavyLoaded.delete(tileId);
    return true;
  }

  shouldRetainTile(tileId: string): boolean {
    const tile = this.tileById(tileId);
    if (!tile) return true;
    const layerId = this.tileLayer(tile);
    return this.retainLoadedTiles && this.essentialLayers.has(layerId);
  }

  isHeavyTile(tileId: string): boolean {
    const tile = this.tileById(tileId);
    return tile ? this.tileLayer(tile) === "heavy" : false;
  }

  activeTileIds(): string[] {
    return [...this.activeTiles];
  }

  loadedTileIds(): string[] {
    return this.loader.registry
      .list()
      .filter((a) => a.source === "REAL_GLB" && a.status === "loaded")
      .map((a) => a.tileId || a.id)
      .filter(Boolean) as string[];
  }
}
