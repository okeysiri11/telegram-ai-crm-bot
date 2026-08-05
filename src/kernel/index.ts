/**
 * @ados/kernel — ADOS OS Enterprise Kernel public API.
 * Business modules must depend on these exports; Kernel never imports verticals.
 */

export { Kernel, createKernel } from "./Kernel.js";
export type { KernelOptions } from "./Kernel.js";

export { BootLoader } from "./BootLoader.js";
export type { BootLoaderOptions } from "./BootLoader.js";

export {
  ServiceRegistry,
  ServiceNotFoundError,
  ServiceAlreadyRegisteredError,
} from "./ServiceRegistry.js";

export { Lifecycle } from "./Lifecycle.js";
export { HealthMonitor } from "./HealthMonitor.js";

/** @deprecated Prefer event_bus exports — Enterprise Event Bus. */
export { EventBus } from "./events/EventBus.js";

export {
  createEventBus,
  EventBus as EnterpriseEventBus,
  Event,
  EventSubscriber,
  EventPublisher,
  EventRegistry,
  EventHistory,
  EventDispatcher,
  EventFilter,
  KernelEventBusAdapter,
  StandardEventTypes,
} from "./event_bus/index.js";
export type {
  IEnterpriseEventBus,
  ADOSEvent,
  EventInput,
  EventHandler as EnterpriseEventHandler,
  Subscription,
  ReplayOptions,
  EventBusOptions,
} from "./event_bus/index.js";

export {
  createServiceMesh,
  ServiceMesh,
  ServiceDescriptor,
  ServiceEndpoint,
  ServiceDiscovery,
  ServiceResolver,
  ServiceHealth,
  ServiceRouter,
  ServicePolicy,
  LoadBalancer,
  descriptorFromKernelService,
  isVersionCompatible,
  compareSemVer,
} from "./service_mesh/index.js";
export type {
  IServiceMesh,
  IServiceDiscovery,
  IServiceResolver,
  IServiceHealth,
  IServiceRouter,
  DiscoveryQuery,
  RouteRequest,
  RouteResult,
  ServiceMeshOptions,
  ServiceDescriptorInit,
  ServicePolicyRule,
} from "./service_mesh/index.js";

export {
  createWorkflowEngine,
  createEnterpriseDeliveryWorkflow,
  WorkflowEngine,
  WorkflowDefinition,
  WorkflowInstance,
  WorkflowStep,
  WorkflowExecutor,
  WorkflowScheduler,
  WorkflowState,
  WorkflowContext,
  WorkflowHistory,
  WorkflowValidator,
} from "./workflow/index.js";
export type {
  IWorkflowEngine,
  IWorkflow,
  IWorkflowStep,
  IWorkflowExecutor,
  IWorkflowScheduler,
  IWorkflowContext,
  WorkflowDefinitionInit,
  WorkflowEngineOptions,
  WorkflowHistoryEntry,
  ApprovalDecision,
  StepHandler,
} from "./workflow/index.js";

export {
  createRuntimeServer,
  RuntimeServer,
  PLATFORM_VERSION,
} from "./runtime/index.js";
export type {
  RuntimeServerOptions,
  HealthResponse,
  StatusResponse,
  ServiceListItem,
  WorkflowListItem,
  MetricsResponse,
  LogEntry,
  EventEntry,
  AgentListItem,
  KernelInfoResponse,
} from "./runtime/index.js";

export {
  loadKernelConfig,
  createDefaultConfig,
  KERNEL_VERSION,
} from "./config/loadConfig.js";

export { InfrastructureService } from "./infra/InfrastructureService.js";
export type { InfrastructureServiceOptions } from "./infra/InfrastructureService.js";

export {
  EventBusService,
  EVENT_BUS_SERVICE_ID,
} from "./infra/EventBusService.js";

export {
  ProviderHostService,
  RuntimeHostService,
  MemoryHostService,
  PluginHostService,
  PROVIDER_HOST_SERVICE_ID,
  RUNTIME_HOST_SERVICE_ID,
  MEMORY_HOST_SERVICE_ID,
  PLUGIN_HOST_SERVICE_ID,
} from "./infra/hosts.js";

export type * from "./interfaces/index.js";
