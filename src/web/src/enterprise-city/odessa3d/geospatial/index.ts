/**
 * Odessa 3D geospatial core — WGS84 ↔ local meters ↔ Three.js world.
 */

export type {
  AltitudePolicy,
  AuthoredCalibrationRecord,
  AxisMapping,
  BoundsClass,
  CalibrationConfidence,
  CalibrationNeed,
  CalibrationQuality,
  CalibrationSlotId,
  CalibrationSolveResult,
  GeoAnchor,
  GeoAnchorType,
  GeoBounds,
  GeoCalibration,
  GeoControlPoint,
  GeoCoordinate,
  GeoOrigin,
  GeoreferenceStatus,
  LocalMeters,
  LocalWorldCoordinate,
  PointErrorMeters,
  WorldBox,
} from "./types";

export {
  ODESSA_ENU_ORIGIN,
  ODESSA_GEO_ORIGIN,
  enuDistanceMeters,
  formatLatLon,
  horizontalDistanceMeters,
  isFiniteGeo,
  localMetersToWgs84,
  metersPerDegreeLatitude,
  metersPerDegreeLongitude,
  wgs84ToLocalMeters,
} from "./localMeters";

export {
  IDENTITY_AXIS_MAPPING,
  UNCALIBRATED_GEOTRANSFORM_AXES,
  describeAxisMapping,
  geoToWorld,
  localMetersToWorld,
  mappedHorizontalAxes,
  worldToGeo,
  worldToLocalMeters,
} from "./worldTransform";

export {
  AUTHORED_CALIBRATION_SOURCE,
  AUTHORED_GEO_CONTROL_POINTS,
  DEFAULT_CALIBRATION_NEEDS,
  HORIZONTAL_AXIS_CANDIDATES,
  MIN_SEPARATION_M,
  RECOMMENDED_SEPARATION_M,
  MIN_WORLD_SEPARATION,
  canPersistQuality,
  clickGeoEnabled,
  independentHoldoutResidual,
  overlaysEnabled,
  qualityFromError,
  resolveOdessaCalibration,
  solveCalibrationFromControlPoints,
  solveCalibrationWithAxisInference,
} from "./geoCalibration";

export { odessaModelFingerprint } from "./modelFingerprint";
export {
  applyPasteToGpsFields,
  odessaMapHelperUrl,
  parseGpsNumber,
  parseLatLonPair,
  validateGpsInput,
} from "./gpsValidation";
export {
  CITY_2D_MAP_IS_GEOGRAPHIC,
  applyMapAssistedPaste,
  mapAssistedPickWorkflow,
  mapHelperOpenUrl,
} from "./mapAssistedPick";
export {
  AUTHORED_CALIBRATION_STORAGE_KEY,
  AUTHORED_CALIBRATION_STORAGE_KEY_V1,
  AUTHORED_CALIBRATION_STORAGE_KEY_V3,
  RAW_OBSERVATIONS_STORAGE_KEY,
  exportAuthoredCalibrationJson,
  importAuthoredCalibrationJson,
  loadAuthoredCalibration,
  loadRawObservations,
  parseAuthoredCalibrationJson,
  resetAuthoredCalibration,
  saveAuthoredCalibration,
  saveRawObservations,
} from "./calibrationStore";
export {
  CALIBRATION_SLOTS,
  applyGpsToSlot,
  buildAuthoredRecord,
  captureControlWorld,
  clearCalibrationSlot,
  completeControlPoints,
  controlPointDistances,
  copyCalibrationDebugData,
  formatCalibrationSessionDebug,
  draftFromControlPoints,
  draftFromObservations,
  checkFromObservation,
  emptyCalibrationDraft,
  evaluateCalibrationDraft,
  evaluateCheckPoint,
  emptyCheckDraft,
  isCollinearWorld,
  worldPairDistances,
  worldTriangleArea,
} from "./calibrationSession";
export type {
  CalibrationDraft,
  CalibrationEvaluation,
  CheckDraft,
  CheckEvaluation,
  DraftControlPoint,
} from "./calibrationSession";
export { SATELLITE_REFERENCE } from "./satelliteReference";
export { CalibrationMarkerRenderer } from "./calibrationMarkers";
export { CalibrationPanel } from "./CalibrationPanel";
export { CalibrationWizard } from "./CalibrationWizard";
export {
  IDENTITY_MODEL_ROOT,
  PACKAGE_EXPECTED_METERS_PER_WORLD_UNIT,
  PICK_COORDINATE_SPACE,
  SCALE_CONVENTION,
  axisMappingRms,
  bestAxisMapping,
  classifyScaleStatus,
  controlHorizontalResiduals,
  evaluateCheckForensics,
  formatGeoreferenceDiagnosticV3,
  identifyLikelyBadFromResiduals,
  identifyLikelyBadFromPairScales,
  identifyLikelyBadPoint,
  leaveOneOut,
  pairScaleRows,
} from "./calibrationDiagnostics";
export type { RawControlObservation, CalibrationModelRoot } from "./types";
export { CITED_ODESSA_PUBLIC_LANDMARKS, loadPublicLandmarkCache, parsePublicLandmarkCache, normalizeLandmarkName } from "./publicLandmarks";
export { extractModelLandmarks, matchableModelLandmarks } from "./modelLandmarks";
export { mapLandmarksExact } from "./landmarkMapping";
export { ransacSolveCalibration, SOLVER_VERSION } from "./ransacCalibration";
export { runAutomatedGeoreference } from "./autoGeoreference";
export { parseOsmDocument, extractOsmBuildings, extractOsmRoads, extractOsmCoastline } from "./osmGeometry";
export {
  parseModelSignatures,
  classifyModelName,
  localBuildingSignatures,
  localRoadSignatures,
  CITYWIDE_SPAN_M,
} from "./modelSignatures";
export {
  orderedFootprint,
  footprintsSimilar,
  footprintRelativeError,
  matchBuildings,
  matchRoads,
  spatialDistribution,
  coastlineMetric,
  polylineNearestRmsM,
  uniqueBidirectionalMatches,
  constellationConsistent,
  matchesToControlPoints,
} from "./geometricMatching";
export {
  pairScaleDistribution,
  summarizePairScales,
  allPairWorldUnitsPerMeter,
  scaleHypothesisSupported,
  HISTORICAL_SOLVER_SCALE_1_4475,
  PACKAGE_SCALE_1_0,
} from "./pairScaleStats";
export { qualityFromIndependentCheck, canPersistIndependent } from "./independentCheckQuality";
export { runGeometricGeoreference, searchAxisMappings, OSM_SOURCE_OVERPASS } from "./geometricGeoreference";
export { buildAlignmentDebugSvg, buildMatchesJson } from "./alignmentDebug";
export {
  HISTORICAL_CHECK_WORLD,
  HISTORICAL_CHECK_ACTUAL_GPS,
  evaluateHistoricalCheck,
  historicalCheckDraft,
} from "./historicalCheck";

export { classifyGeoAgainstBounds, worldBoxToGeoBounds } from "./geoBounds";

export {
  cacheAnchorWorlds,
  cityEntityToGeoAnchor,
  collectEnterpriseAnchors,
  DEV_GEO_ANCHORS,
  geoLocationToCoordinate,
  isPureWgs84,
} from "./geoAnchors";

export { geoSelectionBridge } from "./geoSelectionBridge";
export { GeoAnchorRenderer } from "./geoMarkers";
export { GeoDebugGrid, gridSpacingForDistance } from "./geoDebugGrid";
export { ALTITUDE_POLICY, GeoReferenceRuntime } from "./geoReference";
export type { GeoreferenceDiagnostics } from "./geoReference";
