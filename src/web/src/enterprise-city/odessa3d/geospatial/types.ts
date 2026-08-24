/**
 * Authoritative Odessa 3D geospatial types.
 * Do not scatter lat/lon constants in React components.
 */

export type GeoCoordinate = {
  lat: number;
  lon: number;
  altitude?: number;
};

export type LocalMeters = {
  east: number;
  north: number;
  up: number;
};

export type LocalWorldCoordinate = {
  x: number;
  y: number;
  z: number;
};

/** Ground-plane axis: east/north map onto X/Z (or negated). Up is Y in the current Odessa scene. */
export type HorizontalAxis = "x" | "-x" | "z" | "-z";
export type VerticalAxis = "y" | "-y";

export type AxisMapping = {
  east: HorizontalAxis;
  north: HorizontalAxis;
  up: VerticalAxis;
};

export type CalibrationConfidence = "EXACT" | "CALIBRATED" | "APPROXIMATE" | "UNAVAILABLE";

export type GeoreferenceStatus =
  | "READY_EXACT"
  | "READY_CALIBRATED"
  | "READY_APPROXIMATE"
  | "PROVISIONAL"
  | "CALIBRATION_REQUIRED"
  | "CALIBRATION_POOR"
  | "CALIBRATION_MODEL_MISMATCH"
  | "INVALID";

/** Mathematical ENU tangent origin — not proof that world (0,0,0) is this point. */
export type GeoOrigin = {
  referenceLat: number;
  referenceLon: number;
  referenceAltitude: number;
};

export type CalibrationQuality = "EXCELLENT" | "GOOD" | "ACCEPTABLE" | "POOR" | "INVALID" | "UNAVAILABLE";

export type GeoCalibration = {
  origin: GeoCoordinate;
  worldOrigin: LocalWorldCoordinate;
  metersPerWorldUnit: number;
  rotationRadians: number;
  axisMapping: AxisMapping;
  source: string;
  confidence: CalibrationConfidence;
};

export type GeoControlPoint = {
  id: string;
  geo: GeoCoordinate;
  world: LocalWorldCoordinate;
  label?: string;
  pickedAt?: string;
  coordinateSpace?: "world";
};

export type GeoAnchorType = "enterprise" | "poi" | "vehicle" | "drone" | "event" | "custom";

export type GeoAnchor = {
  id: string;
  name?: string;
  coordinate: GeoCoordinate;
  entityId?: string;
  type: GeoAnchorType;
  label?: string;
  metadata?: Record<string, unknown>;
};

export type PointErrorMeters = {
  id: string;
  errorMeters: number;
  horizontalErrorMeters?: number;
  error3dMeters?: number;
};

export type BoundsClass = "IN_BOUNDS" | "NEAR_BOUNDS" | "OUT_OF_BOUNDS";

export type GeoBounds = {
  north: number;
  south: number;
  east: number;
  west: number;
};

export type AltitudePolicy = {
  /** WGS84 altitude is optional; terrain DEM is not in this package. */
  terrainElevationKnown: false;
  /** Visual lift of POI markers above the sampled world Y, in world units when calibrated. */
  visualOffsetWorld: number;
  preserveAltitudeForTrackers: true;
};

export type WorldBox = {
  min: LocalWorldCoordinate;
  max: LocalWorldCoordinate;
};

export type CalibrationNeed = {
  code: string;
  detail: string;
};

export type CalibrationSolveResult = {
  status: GeoreferenceStatus;
  quality: CalibrationQuality;
  calibration: GeoCalibration | null;
  controlPointCount: number;
  meanErrorMeters: number | null;
  maxErrorMeters: number | null;
  meanErrorMeters3d?: number | null;
  maxErrorMeters3d?: number | null;
  independentResidualMeters?: number | null;
  scale: number | null;
  rotation: number | null;
  origin: GeoCoordinate | null;
  worldOrigin: LocalWorldCoordinate | null;
  reasons: string[];
  needs: CalibrationNeed[];
  pointErrors?: PointErrorMeters[];
};

export type RawControlObservation = {
  id: string;
  world: LocalWorldCoordinate | null;
  gps: GeoCoordinate | null;
  pickedAt: string | null;
  coordinateSpace: "world";
};

export type CalibrationModelRoot = {
  position: LocalWorldCoordinate;
  rotation: LocalWorldCoordinate;
  scale: LocalWorldCoordinate;
};

/** Persisted authored calibration. Never written into GLB/manifest files. */
export type AuthoredCalibrationRecord = {
  version: 1 | 2 | 3 | 4;
  schemaVersion?: 3 | 4;
  source: "AUTHORED_CONTROL_POINTS";
  confidence: "CALIBRATED";
  timestamp: string;
  modelFingerprint: string;
  controlPoints: GeoControlPoint[];
  observations?: RawControlObservation[];
  coordinateSpace?: "world";
  modelRoot?: CalibrationModelRoot;
  origin: GeoCoordinate;
  geoOrigin?: GeoOrigin;
  worldOrigin: LocalWorldCoordinate;
  translation: LocalWorldCoordinate;
  rotationRadians: number;
  metersPerWorldUnit: number;
  scale: number;
  axisMapping: AxisMapping;
  quality: CalibrationQuality;
  meanErrorMeters: number;
  maxErrorMeters: number;
  meanErrorMeters3d?: number | null;
  maxErrorMeters3d?: number | null;
  independentResidualMeters?: number | null;
  independentChecks?: RawControlObservation[];
  solverVersion?: string;
  sourceMetadata?: Record<string, unknown>;
  pointErrors?: PointErrorMeters[];
};

export type CalibrationSlotId = "A" | "B" | "C";
