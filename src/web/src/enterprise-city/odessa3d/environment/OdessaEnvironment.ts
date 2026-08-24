/**
 * Odessa visual environment — sky, sun, ambient, fog, sea tint.
 * Independent of GLB streaming. Create once per 3D mount.
 */

import * as THREE from "three";
import { Sky } from "three/examples/jsm/objects/Sky.js";
import {
  DEFAULT_ENVIRONMENT_PRESET,
  getEnvironmentPreset,
  lightingForQuality,
  type EnvironmentPreset,
  type EnvironmentPresetId,
  type EnvironmentQuality,
  type WaterVisualMode,
} from "./environmentPresets";
import { sunDirectionFromElevationAzimuth, sunPositionOnRadius } from "./sunController";
import { applyFog, createCityFog, fogDensityForCity } from "./atmosphere";
import {
  applyCanonicalSeaAppearance,
  collectCanonicalSeaMeshes,
  updateSeaDistanceResponse,
} from "./waterEnvironment";

export type OdessaEnvironmentOptions = {
  quality?: EnvironmentQuality;
  presetId?: EnvironmentPresetId;
  enableLocalShadows?: boolean;
};

export type OdessaEnvironmentDiagnostics = {
  preset: EnvironmentPresetId;
  sunElevation: number;
  sunAzimuth: number;
  sunIntensity: number;
  hemiIntensity: number;
  fogEnabled: boolean;
  fogDensity: number;
  fogColor: string;
  exposure: number;
  waterMode: WaterVisualMode;
  skyEnabled: boolean;
  environmentQuality: EnvironmentQuality;
};

type SkyMesh = THREE.Mesh & { isSky?: boolean; material: THREE.ShaderMaterial };

export class OdessaEnvironment {
  readonly root = new THREE.Group();
  private mounted = false;
  private scene: THREE.Scene | null = null;
  private renderer: THREE.WebGLRenderer | null = null;
  private quality: EnvironmentQuality;
  private preset: EnvironmentPreset;
  private enableLocalShadows: boolean;
  private sky: SkyMesh | null = null;
  private sun: THREE.DirectionalLight | null = null;
  private hemi: THREE.HemisphereLight | null = null;
  private fog: THREE.FogExp2 | null = null;
  private seaMeshes: THREE.Mesh[] = [];
  private cityDiagonal = 1400;
  private cameraFar = 4000;
  private sunDir = new THREE.Vector3();
  private sunPos = new THREE.Vector3();
  private lastWaterDist = -1;
  private waterMode: WaterVisualMode = "stable";
  private fogEnabled = true;

  constructor(opts: OdessaEnvironmentOptions = {}) {
    this.quality = opts.quality ?? "medium";
    this.preset = getEnvironmentPreset(opts.presetId ?? DEFAULT_ENVIRONMENT_PRESET);
    this.enableLocalShadows = opts.enableLocalShadows === true;
    this.root.name = "odessaEnvironment";
  }

  isMounted() {
    return this.mounted;
  }

  mount(scene: THREE.Scene, renderer: THREE.WebGLRenderer) {
    if (this.mounted) return;
    this.scene = scene;
    this.renderer = renderer;
    this.root.clear();
    scene.add(this.root);
    this.applyColorManagement(renderer);
    this.createLights();
    this.syncSky();
    this.syncFog();
    this.mounted = true;
  }

  dispose() {
    if (this.scene && this.root.parent === this.scene) this.scene.remove(this.root);
    if (this.scene) applyFog(this.scene, null);
    this.disposeSky();
    this.sun = null;
    this.hemi = null;
    this.fog = null;
    this.seaMeshes = [];
    this.root.clear();
    this.scene = null;
    this.renderer = null;
    this.mounted = false;
    this.waterMode = "off";
  }

  setQuality(quality: EnvironmentQuality) {
    if (this.quality === quality) return;
    this.quality = quality;
    if (!this.mounted) return;
    this.syncLights();
    this.syncSky();
    this.syncFog();
    if (this.renderer) this.applyColorManagement(this.renderer);
  }

  setPreset(id: EnvironmentPresetId) {
    const next = getEnvironmentPreset(id);
    if (next.id === this.preset.id && this.mounted) return;
    this.preset = next;
    if (!this.mounted) return;
    this.applyColorManagement(this.renderer!);
    this.syncLights();
    this.syncSky();
    this.syncFog();
  }

  setCityScale(diagonal: number, cameraFar: number) {
    this.cityDiagonal = Math.max(200, diagonal);
    this.cameraFar = Math.max(400, cameraFar);
    if (!this.mounted) return;
    this.syncFog();
    this.syncSkyScale();
    this.syncSunPlacement();
  }

  /** Cheap per-frame path — water roughness only. No alloc, no traverse, no rebuild. */
  updateFrame(cameraDistanceM: number) {
    if (!this.mounted || this.seaMeshes.length === 0) return;
    if (this.lastWaterDist >= 0 && Math.abs(cameraDistanceM - this.lastWaterDist) < 8) return;
    this.lastWaterDist = cameraDistanceM;
    updateSeaDistanceResponse(this.seaMeshes, cameraDistanceM, this.preset, this.quality);
  }

  syncSeaFromRoots(roots: Iterable<THREE.Object3D>) {
    this.seaMeshes = collectCanonicalSeaMeshes(roots);
    let applied = 0;
    for (const mesh of this.seaMeshes) {
      if (applyCanonicalSeaAppearance(mesh, this.preset, this.lastWaterDist < 0 ? 600 : this.lastWaterDist, this.quality)) {
        applied += 1;
      }
    }
    this.waterMode = applied > 0 ? "sea-override" : this.seaMeshes.length ? "stable" : "stable";
  }

  /** Dev diagnostic only — isolates coastal-haze washout. Does not change the preset. */
  setFogEnabled(on: boolean) {
    if (this.fogEnabled === on) return;
    this.fogEnabled = on;
    if (!this.scene) return;
    if (on) this.syncFog();
    else applyFog(this.scene, null);
  }

  isFogEnabled() {
    return this.fogEnabled;
  }

  setLocalShadows(enabled: boolean) {
    if (this.quality !== "high") return;
    this.enableLocalShadows = enabled;
    if (this.sun) this.sun.castShadow = enabled;
    if (this.renderer) this.renderer.shadowMap.enabled = enabled;
  }

  diagnostics(): OdessaEnvironmentDiagnostics {
    const lit = lightingForQuality(this.preset, this.quality);
    const fogHex = this.fog?.color.getHex() ?? this.preset.fogColor;
    return {
      preset: this.preset.id,
      sunElevation: this.preset.elevationDeg,
      sunAzimuth: this.preset.azimuthDeg,
      sunIntensity: this.sun?.intensity ?? lit.sunIntensity,
      hemiIntensity: this.hemi?.intensity ?? lit.hemiIntensity,
      fogEnabled: this.fogEnabled,
      fogDensity: this.fog?.density ?? 0,
      fogColor: `#${fogHex.toString(16).padStart(6, "0")}`,
      exposure: this.renderer?.toneMappingExposure ?? lit.exposure,
      waterMode: this.waterMode,
      skyEnabled: !!this.sky?.visible,
      environmentQuality: this.quality,
    };
  }

  private applyColorManagement(renderer: THREE.WebGLRenderer) {
    const lit = lightingForQuality(this.preset, this.quality);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = lit.exposure;
    renderer.shadowMap.enabled = this.enableLocalShadows && this.quality === "high";
  }

  private createLights() {
    if (this.sun || this.hemi) return;
    const lit = lightingForQuality(this.preset, this.quality);
    this.hemi = new THREE.HemisphereLight(this.preset.hemiSky, this.preset.hemiGround, lit.hemiIntensity);
    this.hemi.name = "odessaHemi";
    this.sun = new THREE.DirectionalLight(this.preset.sunColor, lit.sunIntensity);
    this.sun.name = "odessaSun";
    this.sun.castShadow = this.enableLocalShadows && this.quality === "high";
    this.root.add(this.hemi);
    this.root.add(this.sun);
    this.syncSunPlacement();
  }

  private syncLights() {
    if (!this.hemi || !this.sun) {
      this.createLights();
      return;
    }
    const lit = lightingForQuality(this.preset, this.quality);
    this.hemi.color.setHex(this.preset.hemiSky);
    this.hemi.groundColor.setHex(this.preset.hemiGround);
    this.hemi.intensity = lit.hemiIntensity;
    this.sun.color.setHex(this.preset.sunColor);
    this.sun.intensity = lit.sunIntensity;
    this.syncSunPlacement();
  }

  private syncSunPlacement() {
    sunDirectionFromElevationAzimuth(this.preset.elevationDeg, this.preset.azimuthDeg, this.sunDir);
    const radius = Math.min(this.cameraFar * 0.35, Math.max(420, this.cityDiagonal * 0.85));
    sunPositionOnRadius(this.sunDir, radius, this.sunPos);
    if (this.sun) this.sun.position.copy(this.sunPos);
    if (this.sky) {
      const uniforms = this.sky.material.uniforms;
      uniforms.sunPosition.value.copy(this.sunDir);
    }
  }

  private syncSky() {
    const wantSky = this.quality !== "low" && this.preset.elevationDeg > 0;
    if (!wantSky) {
      if (this.sky) this.sky.visible = false;
      if (this.scene) this.scene.background = new THREE.Color(this.preset.backgroundColor);
      return;
    }
    if (!this.sky) {
      const sky = new Sky() as SkyMesh;
      sky.name = "odessaSky";
      sky.frustumCulled = false;
      this.sky = sky;
      this.root.add(sky);
    }
    this.sky.visible = true;
    const u = this.sky.material.uniforms;
    u.turbidity.value = this.preset.turbidity;
    u.rayleigh.value = this.preset.rayleigh;
    u.mieCoefficient.value = this.preset.mieCoefficient;
    u.mieDirectionalG.value = this.preset.mieDirectionalG;
    this.syncSkyScale();
    this.syncSunPlacement();
    if (this.scene) this.scene.background = new THREE.Color(this.preset.backgroundColor);
  }

  private syncSkyScale() {
    if (!this.sky) return;
    const scale = Math.max(800, this.cameraFar * 0.45);
    this.sky.scale.setScalar(Math.max(600, scale));
  }

  private disposeSky() {
    if (!this.sky) return;
    this.sky.removeFromParent();
    this.sky.geometry.dispose();
    this.sky.material.dispose();
    this.sky = null;
  }

  private syncFog() {
    if (!this.scene) return;
    const density = fogDensityForCity(this.cityDiagonal, this.quality, this.preset.haze);
    if (this.fog) {
      this.fog.color.setHex(this.preset.fogColor);
      this.fog.density = density;
    } else {
      this.fog = createCityFog(this.preset.fogColor, density);
    }
    applyFog(this.scene, this.fogEnabled ? this.fog : null);
  }
}

export function countEnvironmentLights(root: THREE.Object3D): { sun: number; hemi: number; sky: number } {
  let sun = 0;
  let hemi = 0;
  let sky = 0;
  root.traverse((obj) => {
    if ((obj as THREE.DirectionalLight).isDirectionalLight && obj.name === "odessaSun") sun += 1;
    if ((obj as THREE.HemisphereLight).isHemisphereLight && obj.name === "odessaHemi") hemi += 1;
    if (obj.name === "odessaSky") sky += 1;
  });
  return { sun, hemi, sky };
}
