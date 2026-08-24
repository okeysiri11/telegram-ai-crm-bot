/**
 * One-time urban material classification. Names first, then asset id, then color.
 * Never runs per frame.
 */

export type UrbanMaterialClass =
  | "BUILDING"
  | "ROAD"
  | "GROUND"
  | "VEGETATION"
  | "WATER"
  | "INDUSTRIAL"
  | "UNKNOWN";

const WATER_RE = /water|sea|ocean|bay|river|lake|canal|harbor|harbour/i;
const ROAD_RE = /road|street|asphalt|pavement|sidewalk|highway|curb|kerb|lane/i;
const GROUND_RE = /terrain|ground|earth|dirt|soil|plaza|sand|beach|quay/i;
const VEG_RE = /tree|bush|plant|foliage|vegetation|grass|park|hedge|lawn/i;
const IND_RE = /crane|tank|silo|industrial|warehouse|container|factory|dock|port_equip/i;
const BLDG_RE = /build|house|roof|wall|facade|façade|bldg|apart|resid|office|tower/i;

export type ClassifyInput = {
  meshName?: string;
  materialName?: string;
  assetId?: string;
  saturation?: number;
  lightness?: number;
  hue?: number;
};

function blob(input: ClassifyInput): string {
  return `${input.meshName || ""} ${input.materialName || ""} ${input.assetId || ""}`;
}

export function classifyUrbanMaterial(input: ClassifyInput): UrbanMaterialClass {
  const text = blob(input);
  if (WATER_RE.test(text)) return "WATER";
  if (ROAD_RE.test(text)) return "ROAD";
  if (VEG_RE.test(text)) return "VEGETATION";
  if (IND_RE.test(text)) return "INDUSTRIAL";
  if (GROUND_RE.test(text)) return "GROUND";
  if (BLDG_RE.test(text)) return "BUILDING";

  const s = input.saturation ?? 0;
  const l = input.lightness ?? 0.5;
  const h = input.hue ?? 0;
  if (s > 0.18 && h > 0.18 && h < 0.45) return "VEGETATION";
  if (s < 0.12 && l > 0.18 && l < 0.42) return "ROAD";
  if (s < 0.18 && l >= 0.42) return "BUILDING";
  return "UNKNOWN";
}

/** Low-saturation CAD gray/white — safe to normalize without flattening authored color. */
export function isPlaceholderUrban(saturation: number, lightness: number): boolean {
  return saturation < 0.16 || lightness > 0.86;
}
