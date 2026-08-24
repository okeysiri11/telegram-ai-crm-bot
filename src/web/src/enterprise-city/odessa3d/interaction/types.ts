/**
 * Odessa 3D picking types. IDs are deterministic for a runtime session.
 * Never store raw Three.js objects in React state.
 */

export type PickBindingStatus = "BOUND" | "UNBOUND" | "AMBIGUOUS";

export type PickableBounds = {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
  minZ: number;
  maxZ: number;
};

export type PickableEntity = {
  pickId: string;
  assetId: string;
  objectUuid: string;
  meshName?: string;
  displayName?: string;
  materialName?: string;
  layerId?: string;
  classification?: string;
  enterpriseEntityId?: string;
  bindingStatus: PickBindingStatus;
  bounds?: PickableBounds;
  position?: { x: number; y: number; z: number };
  size?: { x: number; y: number; z: number };
};

export type EntityBindingResult = {
  status: PickBindingStatus;
  pickId: string;
  assetId: string;
  enterpriseEntityId?: string;
  buildingId?: string;
  label?: string;
  kind?: string;
  route?: string;
  module?: string;
  statusLabel?: string;
  reasons: string[];
};

export type SceneGraphAudit = {
  object3dCount: number;
  meshCount: number;
  namedMeshCount: number;
  unnamedMeshCount: number;
  meshesByAsset: Record<string, number>;
  materialsReused: number;
  uniqueMaterials: number;
  meshesWithUserData: number;
  meshesWithAssetId: number;
};

export type InteractionDiagnostics = {
  pickables: number;
  hovered: string | null;
  selected: string | null;
  selectedActive: boolean;
  raycastsPerSec: number;
  lastRaycastMs: number;
  candidates: number;
  hits: number;
  boundEntities: number;
  unboundEntities: number;
  ambiguousEntities: number;
  registrySize: number;
  materialClones: number;
  interactionEnabled: boolean;
  showSelectionBounds: boolean;
};

export type InteractionSnapshot = {
  hoveredPickId: string | null;
  selectedPickId: string | null;
  selectedActive: boolean;
  pickable: PickableEntity | null;
  binding: EntityBindingResult | null;
  interactionEnabled: boolean;
  clickWorld?: { x: number; y: number; z: number } | null;
  clickGeo?: { lat: number; lon: number; altitude?: number } | null;
  objectGeo?: { lat: number; lon: number; altitude?: number } | null;
  georeferenceReady?: boolean;
};
