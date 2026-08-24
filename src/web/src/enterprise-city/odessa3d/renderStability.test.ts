import { describe, expect, it } from "vitest";
import * as THREE from "three";
import {
  DEFAULT_RENDER_ISOLATION,
  applyMaterialTextureColorSpaces,
  applyNeutralMaterialDiagnostic,
  collectLightingColorAudit,
  collectRenderStabilityStats,
  countNamedObject,
  createNeutralDiagnosticMaterial,
  fogMixAtDepth,
  hideWaterLikeMeshes,
  safariStableRendererOptions,
  setSubtreeIsolatedHidden,
  toneMappingName,
} from "./renderStability";

describe("Odessa render stability", () => {
  it("mounts a named city root only once in the scene graph", () => {
    const scene = new THREE.Scene();
    const root = new THREE.Group();
    root.name = "odessaCityRoot";
    if (!root.parent) scene.add(root);
    if (!root.parent) scene.add(root);
    expect(countNamedObject(scene, "odessaCityRoot")).toBe(1);
  });

  it("applies color-space normalization once per material (idempotent)", () => {
    const map = new THREE.Texture();
    const normal = new THREE.Texture();
    const mat = new THREE.MeshStandardMaterial({ map, normalMap: normal });
    expect(applyMaterialTextureColorSpaces(mat)).toBe(true);
    expect(map.colorSpace).toBe(THREE.SRGBColorSpace);
    expect(normal.colorSpace).toBe(THREE.LinearSRGBColorSpace);
    expect(applyMaterialTextureColorSpaces(mat)).toBe(false);
    expect(applyMaterialTextureColorSpaces(mat)).toBe(false);
  });

  it("computes isolation stats including a single city root", () => {
    const scene = new THREE.Scene();
    const cityRoot = new THREE.Group();
    cityRoot.name = "odessaCityRoot";
    scene.add(cityRoot);
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial({ transparent: true, depthWrite: false }));
    cityRoot.add(mesh);
    const camera = new THREE.PerspectiveCamera(50, 1, 1.5, 3300);
    const stats = collectRenderStabilityStats({
      scene,
      cityRoot,
      camera,
      renderer: null,
    });
    expect(stats.cityRootInstances).toBe(1);
    expect(stats.meshCount).toBe(1);
    expect(stats.visibleMeshes).toBe(1);
    expect(stats.transparentMaterials).toBe(1);
    expect(stats.depthWriteFalseCount).toBe(1);
    expect(stats.cameraNear).toBe(1.5);
    expect(stats.cameraFar).toBe(3300);
    expect(stats.farNearRatio).toBeCloseTo(3300 / 1.5, 5);
  });

  it("Safari-stable renderer skips stencil and logarithmic depth", () => {
    const opts = safariStableRendererOptions(true);
    expect(opts.antialias).toBe(true);
    expect(opts.stencil).toBe(false);
    expect(opts.depth).toBe(true);
    expect(opts.logarithmicDepthBuffer).toBe(false);
  });

  it("isolation can hide water and restore original visibility without destroying materials", () => {
    const root = new THREE.Group();
    const water = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), new THREE.MeshStandardMaterial({ color: 0x2244aa }));
    water.name = "WEB_water";
    water.visible = true;
    root.add(water);
    hideWaterLikeMeshes(root, true, (m) => /water/i.test(m.name));
    expect(water.visible).toBe(false);
    hideWaterLikeMeshes(root, false, (m) => /water/i.test(m.name));
    expect(water.visible).toBe(true);

    const overlay = new THREE.Group();
    overlay.visible = true;
    setSubtreeIsolatedHidden(overlay, true);
    expect(overlay.visible).toBe(false);
    setSubtreeIsolatedHidden(overlay, false);
    expect(overlay.visible).toBe(true);

    const shared = createNeutralDiagnosticMaterial();
    const original = water.material;
    applyNeutralMaterialDiagnostic(root, true, shared);
    expect(water.material).toBe(shared);
    applyNeutralMaterialDiagnostic(root, false, shared);
    expect(water.material).toBe(original);
    shared.dispose();
    expect(DEFAULT_RENDER_ISOLATION.baseModelOnly).toBe(false);
  });

  it("lighting/color audit flags emissive, metal-without-map, and sRGB data maps", () => {
    const root = new THREE.Group();

    const clean = new THREE.MeshStandardMaterial({ map: new THREE.Texture() });
    applyMaterialTextureColorSpaces(clean);
    root.add(new THREE.Mesh(new THREE.BoxGeometry(), clean));

    const emissive = new THREE.MeshStandardMaterial({ emissive: 0xffffff, emissiveIntensity: 1 });
    root.add(new THREE.Mesh(new THREE.BoxGeometry(), emissive));

    const metal = new THREE.MeshStandardMaterial({ map: new THREE.Texture(), metalness: 1 });
    const vertexColored = new THREE.Mesh(new THREE.BoxGeometry(), metal);
    vertexColored.geometry.setAttribute(
      "color",
      new THREE.BufferAttribute(new Float32Array(vertexColored.geometry.attributes.position.count * 3), 3),
    );
    root.add(vertexColored);

    const badRoughness = new THREE.MeshStandardMaterial({ roughnessMap: new THREE.Texture() });
    badRoughness.roughnessMap!.colorSpace = THREE.SRGBColorSpace;
    root.add(new THREE.Mesh(new THREE.BoxGeometry(), badRoughness));

    const audit = collectLightingColorAudit(root);
    expect(audit.emissiveActiveMaterials).toBe(1);
    expect(audit.metalTexturedMaterials).toBe(1);
    expect(audit.srgbDataMapViolations).toBe(1);
    expect(audit.vertexColorMeshes).toBe(1);
    expect(audit.transparentTexturedMaterials).toBe(0);

    /* After the STEP 29.2 color-space pass, data maps must never register as violations. */
    applyMaterialTextureColorSpaces(badRoughness);
    expect(collectLightingColorAudit(root).srgbDataMapViolations).toBe(0);
  });

  it("fog mix estimate matches FogExp2 and tone mapping names resolve", () => {
    expect(fogMixAtDepth(0, 1000)).toBe(0);
    expect(fogMixAtDepth(0.000774, 200)).toBeCloseTo(0.0237, 3);
    expect(fogMixAtDepth(0.000774, 1600)).toBeGreaterThan(0.7);
    expect(fogMixAtDepth(0.000774, 2600)).toBeGreaterThan(0.95);
    expect(toneMappingName(THREE.ACESFilmicToneMapping)).toBe("ACESFilmicToneMapping");
    expect(toneMappingName(THREE.NoToneMapping)).toBe("NoToneMapping");
  });
});
