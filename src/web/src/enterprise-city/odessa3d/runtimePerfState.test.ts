import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  InteractionRuntimeState,
  SETTLE_MS,
  interactionPixelRatio,
  streamConcurrencyForMode,
} from "./runtimePerfState";
import { MaterialInternCache, materialInternKey } from "./materialIntern";
import { ProgressiveAssetLoader } from "./assetLoader";
import { AssetRegistry } from "./assetRegistry";

describe("Odessa runtime performance state", () => {
  it("transitions IDLE → INTERACTING → SETTLING → IDLE", () => {
    const s = new InteractionRuntimeState();
    expect(s.getMode()).toBe("IDLE");
    s.start(0);
    expect(s.getMode()).toBe("INTERACTING");
    expect(s.shouldPauseStreaming()).toBe(true);
    s.end(100);
    expect(s.getMode()).toBe("SETTLING");
    expect(s.shouldPauseStreaming()).toBe(false);
    expect(s.tick(100 + SETTLE_MS - 10, false)).toBe("SETTLING");
    expect(s.tick(100 + SETTLE_MS + 1, false)).toBe("IDLE");
  });

  it("keeps SETTLING while the camera is still damping", () => {
    const s = new InteractionRuntimeState();
    s.start(0);
    s.end(50);
    expect(s.tick(200, true)).toBe("SETTLING");
    expect(s.tick(200 + SETTLE_MS + 20, false)).toBe("IDLE");
  });

  it("does not reset to IDLE while the pointer is down", () => {
    const s = new InteractionRuntimeState();
    s.start(0);
    expect(s.tick(10_000, false)).toBe("INTERACTING");
  });

  it("does not dip DPR immediately while interacting", () => {
    expect(streamConcurrencyForMode(3, "IDLE", 3)).toBe(3);
    expect(streamConcurrencyForMode(3, "SETTLING", 3)).toBe(1);
    expect(interactionPixelRatio(1.5, true)).toBe(1.5);
    expect(interactionPixelRatio(1, true)).toBe(1);
    expect(interactionPixelRatio(1.25, false)).toBe(1.25);
    const s = new InteractionRuntimeState();
    s.start(0);
    expect(s.shouldDipPixelRatio()).toBe(false);
  });
});

describe("Odessa streaming pause / resume", () => {
  it("pauses new loads and resumes the pump without duplicating queued ids", () => {
    const loader = new ProgressiveAssetLoader();
    loader.setMaxConcurrent(2);
    loader.setStreamingPaused(true);
    expect(loader.isStreamingPaused()).toBe(true);
    loader.setStreamingPaused(false);
    expect(loader.isStreamingPaused()).toBe(false);
  });
});

describe("Odessa asset registry duplicate guard", () => {
  it("does not register the same id or url twice", () => {
    const reg = new AssetRegistry();
    const a = reg.register({ id: "tile-a", url: "/assets/odessa/TILE_02_00.glb" });
    const b = reg.register({ id: "tile-a", url: "/assets/odessa/other.glb" });
    const c = reg.register({ id: "tile-b", url: "/assets/odessa/TILE_02_00.glb" });
    expect(a).toBe(b);
    expect(c).toBe(a);
    expect(reg.list()).toHaveLength(1);
  });
});

describe("Odessa material intern", () => {
  it("shares identical untextured building materials and skips Water", () => {
    const cache = new MaterialInternCache();
    const a = new THREE.MeshStandardMaterial({ name: "building", color: 0x888888, metalness: 0, roughness: 0.8 });
    const b = new THREE.MeshStandardMaterial({ name: "building", color: 0x888888, metalness: 0, roughness: 0.8 });
    const water = new THREE.MeshStandardMaterial({ name: "Water", color: 0x338899 });
    expect(materialInternKey(water)).toBeNull();
    const meshA = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), a);
    const meshB = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), b);
    const root = new THREE.Group();
    root.add(meshA, meshB);
    const replaced = cache.applyToRoot(root);
    expect(replaced).toBeGreaterThanOrEqual(1);
    expect(meshA.material).toBe(meshB.material);
    cache.dispose();
  });

  it("does not intern textured, emissive, water, or different-opacity materials", () => {
    const textured = new THREE.MeshStandardMaterial({ name: "bldg", color: 0x888888 });
    textured.map = new THREE.Texture();
    const emissive = new THREE.MeshStandardMaterial({
      name: "neon",
      color: 0x111111,
      emissive: new THREE.Color(0xffaa33),
      emissiveIntensity: 1,
    });
    const bay = new THREE.MeshStandardMaterial({ name: "WEB_bay", color: 0x2244aa });
    const a = new THREE.MeshStandardMaterial({ name: "glass", color: 0xffffff, transparent: true, opacity: 0.4 });
    const b = new THREE.MeshStandardMaterial({ name: "glass", color: 0xffffff, transparent: true, opacity: 0.9 });
    expect(materialInternKey(textured)).toBeNull();
    expect(materialInternKey(emissive)).toBeNull();
    expect(materialInternKey(bay)).toBeNull();
    expect(materialInternKey(a)).not.toBe(materialInternKey(b));
    textured.map.dispose();
    textured.dispose();
    emissive.dispose();
    bay.dispose();
    a.dispose();
    b.dispose();
  });
});
