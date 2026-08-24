/**
 * Future satellite/map overlay — architecture only.
 * STEP 29.1 calibration uses 3D click + manually entered WGS84.
 * Do not import map SDKs or API keys here.
 */

export type SatelliteReferenceAdapter = {
  id: "none";
  kind: "future_overlay";
  enabled: false;
  provider: null;
  note: string;
};

export const SATELLITE_REFERENCE: SatelliteReferenceAdapter = {
  id: "none",
  kind: "future_overlay",
  enabled: false,
  provider: null,
  note: "Architecture placeholder. Calibration uses 3D click + manual WGS84 only.",
};
