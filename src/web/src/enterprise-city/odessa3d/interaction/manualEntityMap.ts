/**
 * Explicit 3D asset/mesh → Enterprise City building id.
 * Empty until a real mapping is authored. Never fuzzy-match tile GLBs.
 */

import type { CityBuildingId } from "../../cityCatalog";

/** Keys: exact assetId or exact meshName. Values: catalog building ids only. */
export const MANUAL_ODESSA_ENTITY_MAP: Readonly<Record<string, CityBuildingId>> = {
  // Intentionally empty: Odessa GLB tiles currently have no semantic building ids.
};
