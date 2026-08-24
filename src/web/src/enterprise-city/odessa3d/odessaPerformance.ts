/**
 * Odessa 3D runtime performance — demand render loop, adaptive DPR, visibility hysteresis.
 */

import * as THREE from "three";
import type { RuntimePerfMode } from "./runtimePerfState";

export const HUD_THROTTLE_MS = 400;
export const STREAM_TICK_MS = 500;
export const UNLOAD_DISTANCE_MULTIPLIER = 1.4;
export const VISIBILITY_UNLOAD_MULTIPLIER = 1.35;

export type OdessaPerfSnapshot = {
  fps: number;
  frameMs: number;
  drawCalls: number;
  triangles: number;
  points: number;
  lines: number;
  visibleObjects: number;
  loadedGlbs: number;
  cameraDistance: number;
  pixelRatio: number;
  adaptiveTier: string;
  continuousRender: boolean;
};

export type FrameTickResult = {
  fps: number;
  frameMs: number;
};

export class FrameMetricsTracker {
  private samples: number[] = [];
  private lastTime = 0;

  reset(now = performance.now()) {
    this.samples = [];
    this.lastTime = now;
  }

  tick(now = performance.now()): FrameTickResult {
    if (this.lastTime <= 0) {
      this.lastTime = now;
      return { fps: 0, frameMs: 0 };
    }
    const dt = Math.max(0.001, now - this.lastTime);
    this.lastTime = now;
    this.samples.push(dt);
    if (this.samples.length > 90) this.samples.shift();
    const avgMs = this.samples.reduce((a, b) => a + b, 0) / this.samples.length;
    return { fps: 1000 / avgMs, frameMs: avgMs };
  }
}

/** AUTO / MEDIUM steps. Never apply devicePixelRatio above HARD_PIXEL_RATIO_CAP. */
export const DPR_STEPS = [1, 1.25] as const;
export const DPR_STEPS_LOW = [0.85, 1] as const;
export const HARD_PIXEL_RATIO_CAP = 1.5;
export const AUTO_START_PIXEL_RATIO = 1.25;
export const FPS_GUARD_POOR_FPS = 26;
export const FPS_GUARD_RECOVER_FPS = 40;
export const FPS_GUARD_POOR_MS = 3000;
export const FPS_GUARD_RECOVER_MS = 8000;
/** After the camera rests, restore preferred DPR without waiting the 8s recover window. */
export const QUALITY_IDLE_BOOST_MS = 650;

function stepsForProfile(profile: "auto" | "low" | "medium" | "high", cap: number): number[] {
  const hard = Math.min(cap, HARD_PIXEL_RATIO_CAP);
  if (profile === "low" || hard <= 1) return [...DPR_STEPS_LOW].map((s) => Math.min(s, hard));
  if (hard <= 1.25) return [...DPR_STEPS].map((s) => Math.min(s, hard));
  return [1.25, 1.5].filter((s) => s <= hard);
}

export class AdaptivePixelRatioController {
  private stepIndex: number;
  private poorSince = 0;
  private goodSince = 0;
  private idleSince = 0;
  private tierLabel = "stable";
  private readonly steps: number[];

  constructor(
    private readonly profile: "auto" | "low" | "medium" | "high",
    private readonly cap: number,
  ) {
    this.steps = stepsForProfile(profile, cap);
    const preferred = Math.min(
      profile === "auto" ? AUTO_START_PIXEL_RATIO : this.steps[this.steps.length - 1] ?? 1,
      cap,
      HARD_PIXEL_RATIO_CAP,
    );
    let idx = this.steps.findIndex((s) => s >= preferred - 0.001);
    if (idx < 0) idx = this.steps.length - 1;
    this.stepIndex = Math.max(0, idx);
  }

  getTierLabel() {
    return this.profile === "auto" ? this.tierLabel : this.profile;
  }

  currentRatio(devicePixelRatio = 1): number {
    const hard = Math.min(this.cap, HARD_PIXEL_RATIO_CAP);
    if (this.profile !== "auto") {
      return Math.min(devicePixelRatio, hard);
    }
    const step = this.steps[this.stepIndex] ?? AUTO_START_PIXEL_RATIO;
    return Math.min(devicePixelRatio, step, hard);
  }

  getStreamConcurrencyCap(base: number): number {
    if (this.profile !== "auto") return Math.max(1, base);
    const step = this.steps[this.stepIndex] ?? 1;
    if (step <= 0.85) return 1;
    if (this.tierLabel.startsWith("degraded") && step <= 1) return 1;
    return Math.max(1, base);
  }

  private restorePreferred() {
    this.stepIndex = this.steps.length - 1;
    this.tierLabel = `idle:${this.steps[this.stepIndex]}`;
    this.poorSince = 0;
    this.goodSince = 0;
  }

  /**
   * AUTO FPS guard with hysteresis. Never change DPR on the first interaction frame.
   * Step down only after sustained FPS < 26 for ≥ 3s. Step up only when idle
   * (8s healthy FPS, or idle-boost after QUALITY_IDLE_BOOST_MS).
   */
  observe(frameMs: number, now = performance.now(), fps?: number, mode: RuntimePerfMode = "IDLE") {
    if (this.profile !== "auto") return this.currentRatio();
    if (fps === 0) return this.currentRatio();

    const measuredFps = fps ?? (frameMs > 0 ? 1000 / frameMs : 60);
    const interacting = mode === "INTERACTING" || mode === "SETTLING";
    if (mode === "IDLE") {
      this.idleSince = this.idleSince || now;
      if (now - this.idleSince >= QUALITY_IDLE_BOOST_MS && this.stepIndex < this.steps.length - 1) {
        this.restorePreferred();
        return this.currentRatio();
      }
    } else {
      this.idleSince = 0;
    }

    const poor = measuredFps < FPS_GUARD_POOR_FPS;
    const good = measuredFps > FPS_GUARD_RECOVER_FPS;

    if (poor) {
      this.poorSince = this.poorSince || now;
      this.goodSince = 0;
      if (now - this.poorSince >= FPS_GUARD_POOR_MS && this.stepIndex > 0) {
        this.stepIndex -= 1;
        this.poorSince = 0;
        this.tierLabel = `degraded:${this.steps[this.stepIndex]}`;
      }
    } else if (good && !interacting) {
      this.goodSince = this.goodSince || now;
      this.poorSince = 0;
      if (now - this.goodSince >= FPS_GUARD_RECOVER_MS && this.stepIndex < this.steps.length - 1) {
        const next = this.steps[this.stepIndex + 1];
        if (next <= Math.min(this.cap, HARD_PIXEL_RATIO_CAP)) {
          this.stepIndex += 1;
          this.tierLabel = `recovering:${next}`;
        }
        this.goodSince = 0;
      }
    } else {
      this.poorSince = 0;
      this.goodSince = 0;
      if (!this.tierLabel.startsWith("degraded") && !this.tierLabel.startsWith("recovering") && !this.tierLabel.startsWith("idle")) {
        this.tierLabel = "stable";
      }
    }

    return this.currentRatio();
  }
}

export function loadUnloadDistances(loadM: number, multiplier = UNLOAD_DISTANCE_MULTIPLIER) {
  return { loadDistanceM: loadM, unloadDistanceM: loadM * multiplier };
}

/** Hysteresis visibility — stay visible until beyond unload distance. */
export function visibilityWithHysteresis(
  distanceM: number,
  loadDistanceM: number,
  unloadDistanceM: number,
  currentlyVisible: boolean,
): boolean {
  if (currentlyVisible) return distanceM <= unloadDistanceM;
  return distanceM <= loadDistanceM;
}

export type TilePriorityInput = {
  tileId: string;
  distanceM: number;
  inFrustum: boolean;
  manifestPriority: boolean;
  layerId: string;
  sizeMb: number;
  cameraForwardDot: number;
};

export function scoreTilePriority(input: TilePriorityInput): number {
  let score = input.distanceM;
  if (input.manifestPriority) score -= 5000;
  if (input.inFrustum) score -= 2000;
  if (input.layerId === "heavy") score += 800;
  score += Math.max(0, input.sizeMb - 8) * 40;
  score -= Math.max(0, input.cameraForwardDot) * 600;
  return score;
}

export function collectRendererStats(renderer: THREE.WebGLRenderer) {
  const render = renderer.info.render;
  const memory = renderer.info.memory;
  return {
    drawCalls: render.calls,
    triangles: render.triangles,
    points: render.points,
    lines: render.lines,
    geometries: memory.geometries,
    textures: memory.textures,
  };
}

export function countVisibleSceneObjects(scene: THREE.Scene): number {
  let n = 0;
  scene.traverseVisible((obj) => {
    n += 1;
  });
  return n;
}

export function applyTexturedMaterialFilters(tex: THREE.Texture, anisotropy: number) {
  const aniso = Math.max(1, anisotropy);
  let changed = false;
  if (tex.magFilter !== THREE.LinearFilter) {
    tex.magFilter = THREE.LinearFilter;
    changed = true;
  }
  if (!tex.generateMipmaps) {
    tex.generateMipmaps = true;
    changed = true;
  }
  if (tex.minFilter !== THREE.LinearMipmapLinearFilter) {
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    changed = true;
  }
  if (tex.anisotropy !== aniso) {
    tex.anisotropy = aniso;
    changed = true;
  }
  if (changed) tex.needsUpdate = true;
}

export function prepareMeshForPerformance(
  mesh: THREE.Mesh,
  opts: { enableShadows: boolean; maxAnisotropy: number },
) {
  mesh.frustumCulled = true;
  mesh.castShadow = opts.enableShadows;
  mesh.receiveShadow = opts.enableShadows;
  if (mesh.geometry && !mesh.geometry.boundingSphere) {
    mesh.geometry.computeBoundingSphere();
  }
  if (mesh.geometry && !mesh.geometry.boundingBox) {
    mesh.geometry.computeBoundingBox();
  }

  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
  for (const mat of materials) {
    if (!mat) continue;
    const std = mat as THREE.MeshStandardMaterial;
    if (std.isMeshStandardMaterial || (mat as THREE.MeshPhongMaterial).isMeshPhongMaterial) {
      let changed = false;
      if (std.transparent && std.opacity >= 0.99) {
        std.transparent = false;
        std.opacity = 1;
        changed = true;
      }
      if (std.side !== THREE.FrontSide) {
        std.side = THREE.FrontSide;
        changed = true;
      }
      if (changed) std.needsUpdate = true;
    }
    const texKeys = ["map", "normalMap", "roughnessMap", "metalnessMap", "aoMap"] as const;
    for (const key of texKeys) {
      const tex = (mat as THREE.MeshStandardMaterial)[key];
      if (tex instanceof THREE.Texture) {
        applyTexturedMaterialFilters(tex, opts.maxAnisotropy);
      }
    }
  }
}

export function cameraMotionKey(camera: THREE.Camera, target: THREE.Vector3): string {
  const p = camera.position;
  return `${p.x.toFixed(2)}:${p.y.toFixed(2)}:${p.z.toFixed(2)}:${target.x.toFixed(2)}:${target.y.toFixed(2)}:${target.z.toFixed(2)}`;
}

export type DemandRenderLoopOptions = {
  onFrame: (now: number) => void;
  shouldContinue: () => boolean;
};

/** Single RAF loop — starts on demand, stops when idle. */
export class DemandRenderLoop {
  private rafId = 0;
  private disposed = false;

  constructor(private opts: DemandRenderLoopOptions) {}

  get isRunning() {
    return this.rafId !== 0;
  }

  requestFrame() {
    if (this.disposed || this.rafId) return;
    this.rafId = requestAnimationFrame(this.tick);
  }

  private tick = (now: number) => {
    this.rafId = 0;
    if (this.disposed) return;
    this.opts.onFrame(now);
    if (!this.disposed && this.opts.shouldContinue()) {
      this.requestFrame();
    }
  };

  dispose() {
    this.disposed = true;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    this.rafId = 0;
  }
}
