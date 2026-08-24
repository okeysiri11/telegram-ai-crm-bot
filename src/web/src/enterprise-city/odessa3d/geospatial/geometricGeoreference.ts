/**
 * STEP 30.5 geometric georeference. Does not invent A/B/C or alter city geometry.
 */

import type { GeoControlPoint } from "./types";
import { canPersistIndependent, percentileSorted, qualityFromIndependentCheck, rms } from "./independentCheckQuality";
import {
  coastlineMetric,
  matchBuildings,
  matchRoads,
  matchesToControlPoints,
  spatialDistribution,
  type GeometricMatchCandidate,
} from "./geometricMatching";
import { extractOsmBuildings, extractOsmCoastline, extractOsmRoads, parseOsmDocument, type OsmDocument } from "./osmGeometry";
import {
  localBuildingSignatures,
  localRoadSignatures,
  parseModelSignatures,
  waterSignatures,
  type ModelXzSignature,
} from "./modelSignatures";
import {
  HISTORICAL_SOLVER_SCALE_1_4475,
  PACKAGE_SCALE_1_0,
  pairScaleDistribution,
  scaleHypothesisSupported,
  type PairScaleDistribution,
} from "./pairScaleStats";
import { ransacSolveCalibration, SOLVER_VERSION } from "./ransacCalibration";
import { axisMappingRms, controlHorizontalResiduals, horizontalResidualMeters } from "./calibrationDiagnostics";
import { describeAxisMapping, geoToWorld } from "./worldTransform";
import { evaluateHistoricalCheck, HISTORICAL_CHECK_WORLD } from "./historicalCheck";
import { buildAuthoredRecord } from "./calibrationSession";
import { saveAuthoredCalibration, type CalibrationStorage } from "./calibrationStore";
import { buildAlignmentDebugSvg, buildMatchesJson } from "./alignmentDebug";

export const OSM_SOURCE_OVERPASS = "overpass-api.de";

export type GeometricGeoreferenceResult = {
  osmSource: string;
  osmBuildingCount: number;
  osmRoadCount: number;
  osmCoastlineWays: number;
  modelBuildingCandidates: number;
  modelRoadCandidates: number;
  coastlineMatchAvailable: boolean;
  coastlineRmsM: number | null;
  coastlinePrecisionNote: string;
  rawMatches: number;
  ransacInliers: number;
  ransacOutliers: number;
  matchedRegionCount: number;
  spatialOk: boolean;
  axisMapping: string;
  solverScale: number | null;
  solverRotationDeg: number | null;
  controlRmsM: number | null;
  controlP95M: number | null;
  independentCheckCount: number;
  independentCheckRmsM: number | null;
  independentCheckP95M: number | null;
  independentCheckMaxM: number | null;
  historicalCheckPredictedGps: string;
  historicalCheckErrorM: number | null;
  pairScale: PairScaleDistribution;
  scale14475Supported: boolean;
  scale10Supported: boolean;
  geometryChanged: false;
  step29RepairChanged: false;
  persisted: boolean;
  georeferenceStatus: ReturnType<typeof qualityFromIndependentCheck>;
  safeToStartStep31: boolean;
  rootCauseIfFailed: string;
  accepted: GeometricMatchCandidate[];
  rejected: GeometricMatchCandidate[];
  controlPoints: GeoControlPoint[];
  independentCheckPoints: GeoControlPoint[];
  debugSvg: string;
  matchesJson: Record<string, unknown>;
  solverVersion: string;
};

function holdOutSplit(points: GeoControlPoint[]): { fit: GeoControlPoint[]; hold: GeoControlPoint[] } {
  if (points.length < 4) return { fit: points, hold: [] };
  const holdCount = Math.max(1, Math.floor(points.length / 4));
  return { fit: points.slice(0, points.length - holdCount), hold: points.slice(points.length - holdCount) };
}

export function searchAxisMappings(points: readonly GeoControlPoint[]) {
  return axisMappingRms(points);
}

export function runGeometricGeoreference(input: {
  osmBuildingsDoc?: unknown;
  osmRoadsDoc?: unknown;
  osmCoastDoc?: unknown;
  modelSignatures?: unknown;
  modelRows?: readonly ModelXzSignature[];
  osmSource?: string;
  storage?: CalibrationStorage | null;
  modelFingerprint?: string;
  /** Historical STEP 30.1 CHECK is always reported; include it in independent stats only for the real Odessa model. */
  includeHistoricalCheck?: boolean;
}): GeometricGeoreferenceResult {
  const buildingsDoc: OsmDocument = parseOsmDocument(input.osmBuildingsDoc ?? { elements: [] });
  const roadsDoc: OsmDocument = parseOsmDocument(input.osmRoadsDoc ?? { elements: [] });
  const coastDoc: OsmDocument = parseOsmDocument(input.osmCoastDoc ?? { elements: [] });
  const osmBuildings = extractOsmBuildings(buildingsDoc);
  const osmRoads = extractOsmRoads(roadsDoc);
  const osmCoast = extractOsmCoastline(coastDoc);
  const modelDoc = parseModelSignatures(input.modelRows ? { rows: input.modelRows } : (input.modelSignatures ?? { rows: [] }));
  const buildings = localBuildingSignatures(modelDoc.rows);
  const roads = localRoadSignatures(modelDoc.rows);
  const water = waterSignatures(modelDoc.rows);

  const bMatch = matchBuildings(buildings, osmBuildings);
  const rMatch = matchRoads(roads, osmRoads);
  const accepted = [...bMatch.accepted, ...rMatch.accepted];
  const rejected = [...bMatch.rejected, ...rMatch.rejected];
  const rawMatches = bMatch.raw.length + rMatch.raw.length;

  const emptyPair = pairScaleDistribution([]);
  const histEmpty = evaluateHistoricalCheck(null);
  const coastEmpty = coastlineMetric(water, osmCoast, null);

  const base = {
    osmSource: input.osmSource ?? OSM_SOURCE_OVERPASS,
    osmBuildingCount: osmBuildings.length,
    osmRoadCount: osmRoads.length,
    osmCoastlineWays: osmCoast.length,
    modelBuildingCandidates: buildings.length,
    modelRoadCandidates: roads.length,
    coastlineMatchAvailable: coastEmpty.available,
    coastlineRmsM: coastEmpty.rmsM,
    coastlinePrecisionNote: coastEmpty.precisionNote,
    rawMatches,
    ransacInliers: 0,
    ransacOutliers: 0,
    matchedRegionCount: 0,
    spatialOk: false,
    axisMapping: "—",
    solverScale: null as number | null,
    solverRotationDeg: null as number | null,
    controlRmsM: null as number | null,
    controlP95M: null as number | null,
    independentCheckCount: 0,
    independentCheckRmsM: null as number | null,
    independentCheckP95M: null as number | null,
    independentCheckMaxM: null as number | null,
    historicalCheckPredictedGps: histEmpty.predicted
      ? `${histEmpty.predicted.lat.toFixed(6)}, ${histEmpty.predicted.lon.toFixed(6)}`
      : "46.386292, 30.705357",
    historicalCheckErrorM: histEmpty.errorM,
    pairScale: emptyPair,
    scale14475Supported: false,
    scale10Supported: false,
    geometryChanged: false as const,
    step29RepairChanged: false as const,
    persisted: false,
    georeferenceStatus: "BLOCKED" as ReturnType<typeof qualityFromIndependentCheck>,
    safeToStartStep31: false,
    rootCauseIfFailed: "NO_PROVEN_GEOMETRIC_CORRESPONDENCE",
    accepted,
    rejected,
    controlPoints: [] as GeoControlPoint[],
    independentCheckPoints: [] as GeoControlPoint[],
    debugSvg: "",
    matchesJson: {} as Record<string, unknown>,
    solverVersion: SOLVER_VERSION,
  };

  const debugCommon = {
    model: modelDoc.rows,
    osmBuildings,
    osmRoads,
    osmCoast,
    accepted,
    rejected,
    checkWorld: HISTORICAL_CHECK_WORLD,
    calibration: null,
  };
  base.debugSvg = buildAlignmentDebugSvg(debugCommon);
  base.matchesJson = buildMatchesJson({
    osmSource: base.osmSource,
    osmBuildingCount: base.osmBuildingCount,
    osmRoadCount: base.osmRoadCount,
    modelBuildingCandidates: base.modelBuildingCandidates,
    modelRoadCandidates: base.modelRoadCandidates,
    accepted,
    rejected,
    rawCount: rawMatches,
  });

  if (accepted.length < 3) {
    if (bMatch.raw.length + rMatch.raw.length > 0) {
      base.rootCauseIfFailed =
        "FOOTPRINT_CANDIDATES_FAILED_UNIQUENESS_OR_CONSTELLATION — model buildings are mostly city-wide batches; local AABBs are not a unique lock onto OSM";
    }
    return base;
  }

  const controls = matchesToControlPoints(accepted);
  const spatial = spatialDistribution(controls);
  base.matchedRegionCount = spatial.matchedRegionCount;
  base.spatialOk = spatial.ok;
  if (!spatial.ok) {
    base.rootCauseIfFailed = spatial.collinear
      ? "MATCHES_COLLINEAR"
      : "MATCHES_NOT_SPATIALLY_DISTRIBUTED";
    return base;
  }

  const { fit, hold } = holdOutSplit(controls);
  const ransac = ransacSolveCalibration(fit);
  const solve = ransac.solve;
  const cal = solve.calibration;
  base.ransacInliers = ransac.inliers.length;
  base.ransacOutliers = ransac.rejected.length;
  base.controlPoints = ransac.inliers.length >= 3 ? ransac.inliers : fit;
  base.independentCheckPoints = hold;

  const pair = pairScaleDistribution(base.controlPoints);
  base.pairScale = pair;
  base.scale14475Supported = scaleHypothesisSupported(pair, HISTORICAL_SOLVER_SCALE_1_4475);
  base.scale10Supported = scaleHypothesisSupported(pair, PACKAGE_SCALE_1_0);

  if (!cal) {
    base.rootCauseIfFailed = "SIMILARITY_SOLVER_FAILED";
    return base;
  }

  const coast = coastlineMetric(water, osmCoast, cal);
  base.coastlineMatchAvailable = coast.available;
  base.coastlineRmsM = coast.rmsM;
  base.coastlinePrecisionNote = coast.precisionNote;

  const horiz = controlHorizontalResiduals(base.controlPoints, cal, geoToWorld);
  const horizVals = [...horiz.map((h) => h.horizontalM)].sort((a, b) => a - b);
  base.controlRmsM = rms(horizVals);
  base.controlP95M = percentileSorted(horizVals, 0.95);
  base.axisMapping = describeAxisMapping(cal.axisMapping);
  base.solverScale = solve.scale;
  base.solverRotationDeg = solve.rotation != null ? (solve.rotation * 180) / Math.PI : null;

  const holdErrs = hold.map((p) => horizontalResidualMeters(p.world, p.geo, cal).errorM);
  const hist = evaluateHistoricalCheck(cal, base.controlPoints);
  const includeHistorical = input.includeHistoricalCheck !== false;
  const independent = [...holdErrs, ...(includeHistorical ? [hist.errorM] : [])].filter(
    (n): n is number => n != null && Number.isFinite(n),
  );
  const independentSorted = [...independent].sort((a, b) => a - b);
  base.independentCheckCount = independent.length;
  base.independentCheckRmsM = rms(independent);
  base.independentCheckP95M = percentileSorted(independentSorted, 0.95);
  base.independentCheckMaxM = independent.length ? Math.max(...independent) : null;
  base.historicalCheckErrorM = hist.errorM;
  base.historicalCheckPredictedGps = hist.predicted
    ? `${hist.predicted.lat.toFixed(6)}, ${hist.predicted.lon.toFixed(6)}`
    : "—";

  const status = qualityFromIndependentCheck(base.independentCheckRmsM, base.independentCheckP95M);
  base.georeferenceStatus = status;
  base.safeToStartStep31 = canPersistIndependent(status);
  if (!canPersistIndependent(status)) {
    base.rootCauseIfFailed =
      status === "FAILED"
        ? "INDEPENDENT_CHECK_EXCEEDS_ACCEPTABLE"
        : "INDEPENDENT_CHECK_UNAVAILABLE";
  } else {
    base.rootCauseIfFailed = "";
  }

  if (cal && canPersistIndependent(status) && input.storage && input.modelFingerprint) {
    const record = buildAuthoredRecord({
      solve,
      controlPoints: base.controlPoints,
      modelFingerprint: input.modelFingerprint,
      independentResidualMeters: base.independentCheckRmsM,
    });
    if (record) {
      base.persisted = saveAuthoredCalibration(
        {
          ...record,
          version: 4,
          schemaVersion: 4,
          independentChecks: hold.map((p) => ({
            id: p.id,
            world: p.world,
            gps: p.geo,
            pickedAt: null,
            coordinateSpace: "world" as const,
          })),
        },
        input.storage,
      );
    }
  }

  base.debugSvg = buildAlignmentDebugSvg({
    ...debugCommon,
    accepted,
    rejected,
    calibration: cal,
    residuals: base.controlPoints.map((p) => ({
      from: p.world,
      to: geoToWorld(p.geo, cal),
    })),
  });

  return base;
}
