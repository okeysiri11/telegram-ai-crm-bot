/**
 * ADOS Enterprise Service Mesh — public exports.
 */

export { ServiceMesh, createServiceMesh } from "./ServiceMesh.js";
export { ServiceDescriptor } from "./ServiceDescriptor.js";
export { ServiceEndpoint } from "./ServiceEndpoint.js";
export { ServiceDiscovery } from "./ServiceDiscovery.js";
export { ServiceResolver } from "./ServiceResolver.js";
export { ServiceHealth } from "./ServiceHealth.js";
export { ServiceRouter } from "./ServiceRouter.js";
export { ServicePolicy } from "./ServicePolicy.js";
export { LoadBalancer } from "./LoadBalancer.js";
export { descriptorFromKernelService } from "./fromKernelService.js";
export { compareSemVer, isVersionCompatible, parseSemVer } from "./semver.js";

export type {
  IMeshRegistrable,
  IServiceDiscovery,
  IServiceHealth,
  IServiceMesh,
  IServiceResolver,
  IServiceRouter,
} from "./interfaces.js";

export type {
  DiscoveryQuery,
  EndpointProtocol,
  HeartbeatRecord,
  LoadBalanceStrategy,
  MeshHealthStatus,
  RouteRequest,
  RouteResult,
  SemVerRange,
  ServiceDependency,
  ServiceDescriptorInit,
  ServiceEndpointInit,
  ServiceInvoker,
  ServiceMeshOptions,
  ServicePolicyRule,
} from "./types.js";
