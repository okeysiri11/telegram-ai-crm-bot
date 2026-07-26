/** Enterprise Data Fabric & Knowledge Graph — Sprint 33.3. */
export {
  FABRIC_ENTITIES,
  FABRIC_EDGES,
  KNOWLEDGE_CHAIN,
  getFabricEntity,
  KIND_LABEL,
} from "./fabricCatalog";
export type { FabricEntity, FabricEdge, FabricEntityKind } from "./fabricCatalog";
export { deriveDataFabric } from "./deriveFabric";
export type { FabricBundle, FabricLineage, FabricImpact, FabricExecutive } from "./deriveFabric";
export {
  EnterpriseDataFabricPage,
  DataFabricStrip,
  DataFabricOverviewCompact,
} from "./EnterpriseDataFabricPage";
