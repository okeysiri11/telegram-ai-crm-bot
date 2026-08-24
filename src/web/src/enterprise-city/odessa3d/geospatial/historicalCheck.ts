/**
 * Historical STEP 30.1 CHECK. Never added to the solver.
 */

import type { CheckDraft } from "./calibrationSession";
import { evaluateCheckForensics } from "./calibrationDiagnostics";
import type { GeoCalibration, GeoControlPoint, GeoCoordinate, LocalWorldCoordinate } from "./types";

export const HISTORICAL_CHECK_WORLD: LocalWorldCoordinate = { x: -1935.01, y: 20.66, z: 15514.82 };
export const HISTORICAL_CHECK_ACTUAL_GPS: GeoCoordinate = { lat: 46.386267, lon: 30.705832 };
export const HISTORICAL_CHECK_PREDICTED_GPS_REPORTED: GeoCoordinate = { lat: 46.386292, lon: 30.705357 };
export const HISTORICAL_CHECK_ERROR_M_REPORTED = 36.58;
export const HISTORICAL_CHECK_EAST_ERROR_M_REPORTED = -36.47;
export const HISTORICAL_CHECK_NORTH_ERROR_M_REPORTED = 2.78;

export function historicalCheckDraft(): CheckDraft {
  return {
    world: { ...HISTORICAL_CHECK_WORLD },
    geo: { ...HISTORICAL_CHECK_ACTUAL_GPS },
    latText: String(HISTORICAL_CHECK_ACTUAL_GPS.lat),
    lonText: String(HISTORICAL_CHECK_ACTUAL_GPS.lon),
  };
}

export function evaluateHistoricalCheck(calibration: GeoCalibration | null, controls: readonly GeoControlPoint[] = []) {
  const live = evaluateCheckForensics(historicalCheckDraft(), controls, calibration);
  if (live.errorM != null) return live;
  return {
    ...live,
    predicted: HISTORICAL_CHECK_PREDICTED_GPS_REPORTED,
    errorM: HISTORICAL_CHECK_ERROR_M_REPORTED,
    eastErrorM: HISTORICAL_CHECK_EAST_ERROR_M_REPORTED,
    northErrorM: HISTORICAL_CHECK_NORTH_ERROR_M_REPORTED,
  };
}
