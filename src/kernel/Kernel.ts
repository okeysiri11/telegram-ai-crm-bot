import { BootLoader } from "./BootLoader.js";
import { KERNEL_VERSION, loadKernelConfig } from "./config/loadConfig.js";
import { EventBus as EnterpriseEventBus } from "./event_bus/EventBus.js";
import { KernelEventBusAdapter } from "./event_bus/KernelEventBusAdapter.js";
import { HealthMonitor } from "./HealthMonitor.js";
import type { IBootLoader } from "./interfaces/IBootLoader.js";
import type { IEventBus } from "./interfaces/IEventBus.js";
import type { IHealthMonitor } from "./interfaces/IHealthMonitor.js";
import type { IKernel } from "./interfaces/IKernel.js";
import type { IServiceRegistry } from "./interfaces/IServiceRegistry.js";
import type {
  KernelConfig,
  LifecycleState,
  PlatformHealthReport,
} from "./interfaces/types.js";
import { Lifecycle } from "./Lifecycle.js";
import { ServiceRegistry } from "./ServiceRegistry.js";
import { EVENT_BUS_SERVICE_ID } from "./infra/EventBusService.js";
import {
  createServiceMesh,
  descriptorFromKernelService,
  type ServiceMesh,
  type ServiceMeshOptions,
} from "./service_mesh/index.js";
import {
  createWorkflowEngine,
  type WorkflowEngine,
  type WorkflowEngineOptions,
} from "./workflow/index.js";

export interface KernelOptions {
  readonly registry?: IServiceRegistry;
  readonly healthMonitor?: IHealthMonitor;
  readonly eventBus?: IEventBus;
  /** Full enterprise bus — preferred; wraps into IEventBus when set. */
  readonly enterpriseEventBus?: EnterpriseEventBus;
  readonly bootLoader?: IBootLoader;
  readonly serviceMesh?: ServiceMesh;
  readonly serviceMeshOptions?: ServiceMeshOptions;
  readonly workflowEngine?: WorkflowEngine;
  readonly workflowEngineOptions?: WorkflowEngineOptions;
  readonly config?: Partial<KernelConfig>;
}

/**
 * ADOS Enterprise Kernel — single entry point.
 *
 * Architecture invariants:
 * - Never imports business modules (CRM, ERP, Marketplace, AI Studio, …)
 * - Business modules / plugins depend on Kernel via interfaces
 * - Future plugins register through ServiceRegistry + plugin host
 * - Internal communication via Event Bus + Service Mesh
 */
export class Kernel implements IKernel {
  readonly version = KERNEL_VERSION;
  readonly registry: IServiceRegistry;
  readonly healthMonitor: IHealthMonitor;
  readonly eventBus: IEventBus;
  readonly bootLoader: IBootLoader;
  /** Enterprise backbone — Runtime/Agents/Modules should prefer this. */
  readonly enterpriseEventBus: EnterpriseEventBus;
  /** Discovery & routing backbone for every internal service. */
  readonly serviceMesh: ServiceMesh;
  /** Multi-step orchestration across agents/services via Event Bus + Mesh. */
  readonly workflowEngine: WorkflowEngine;

  private _config: KernelConfig;
  private readonly lifecycle = new Lifecycle("Created");
  private bootStartedAt = 0;

  constructor(options?: KernelOptions) {
    this.registry = options?.registry ?? new ServiceRegistry();
    this.healthMonitor = options?.healthMonitor ?? new HealthMonitor();
    const adapter =
      options?.eventBus instanceof KernelEventBusAdapter
        ? options.eventBus
        : options?.enterpriseEventBus
          ? new KernelEventBusAdapter(options.enterpriseEventBus)
          : options?.eventBus
            ? null
            : new KernelEventBusAdapter();

    if (adapter) {
      this.eventBus = adapter;
      this.enterpriseEventBus = adapter.enterprise;
    } else {
      const legacy = options?.eventBus;
      if (!legacy) {
        throw new Error("Kernel event bus configuration is invalid");
      }
      this.eventBus = legacy;
      this.enterpriseEventBus =
        options?.enterpriseEventBus ?? new EnterpriseEventBus();
    }
    this.bootLoader = options?.bootLoader ?? new BootLoader();
    this.serviceMesh =
      options?.serviceMesh ?? createServiceMesh(options?.serviceMeshOptions);
    this.workflowEngine =
      options?.workflowEngine ??
      createWorkflowEngine({
        ...options?.workflowEngineOptions,
        eventBus: {
          publish: async (event) => {
            await this.enterpriseEventBus.publish({
              type: event.type,
              payload: event.payload,
              mode: event.mode ?? "async",
            });
          },
          subscribe: (type, handler) => {
            const sub = this.enterpriseEventBus.subscribe(type, (ev) => {
              handler({ type: ev.type, payload: ev.payload });
            });
            return { unsubscribe: () => sub.unsubscribe() };
          },
        },
        serviceMesh: {
          route: (request) => this.serviceMesh.route(request),
        },
      });
    this._config = loadKernelConfig(options?.config);
  }

  get config(): KernelConfig {
    return this._config;
  }

  getState(): LifecycleState {
    return this.lifecycle.state;
  }

  /**
   * Starts ADOS: load configuration, boot infrastructure, start services,
   * publish BootCompleted.
   */
  async start(configOverrides?: Partial<KernelConfig>): Promise<void> {
    this.lifecycle.assertState("Created", "Stopped");
    this.bootStartedAt = Date.now();

    if (configOverrides) {
      this._config = loadKernelConfig({
        ...this._config,
        ...configOverrides,
        featureFlags: {
          ...this._config.featureFlags,
          ...(configOverrides.featureFlags ?? {}),
        },
      });
    }

    if (this.lifecycle.state === "Stopped") {
      this.lifecycle.transition("Initialized");
    } else {
      this.lifecycle.transition("Initialized");
    }

    await this.bootLoader.boot({
      registry: this.registry,
      config: this._config,
      enterpriseEventBus: this.enterpriseEventBus,
    });

    for (const service of this.registry.list()) {
      this.healthMonitor.watch(service);
      if (!this.serviceMesh.discovery.get(service.id)) {
        this.serviceMesh.register(descriptorFromKernelService(service));
      }
    }
    this.serviceMesh.start();

    if (this._config.failFast) {
      const report = await this.healthMonitor.report();
      const criticalUnhealthy = report.services.filter(
        (s) =>
          (s.status === "unhealthy" || s.status === "unknown") &&
          s.details?.["critical"] === true,
      );
      if (criticalUnhealthy.length > 0) {
        const ids = criticalUnhealthy.map((s) => s.id).join(", ");
        throw new Error(`Kernel boot failed — unhealthy critical services: ${ids}`);
      }
    }

    this.lifecycle.transition("Started");

    const serviceIds = this.registry.list().map((s) => s.id);
    await this.eventBus.publish("BootCompleted", {
      kernelVersion: this.version,
      startedAt: new Date().toISOString(),
      durationMs: Date.now() - this.bootStartedAt,
      serviceIds,
      config: this._config,
    });

    if (this.registry.exists(EVENT_BUS_SERVICE_ID)) {
      // Event bus service already started by BootLoader; no-op hook for DI consumers.
    }
  }

  async stop(): Promise<void> {
    this.lifecycle.assertState("Started", "Paused");
    this.serviceMesh.stop();

    const services = [...this.registry.list()].reverse();
    for (const service of services) {
      const state = service.getLifecycleState();
      if (state === "Started" || state === "Paused" || state === "Initialized") {
        await service.stop();
      }
    }

    this.lifecycle.transition("Stopped");
  }

  async dispose(): Promise<void> {
    if (this.lifecycle.state === "Disposed") {
      return;
    }
    if (this.lifecycle.state === "Started" || this.lifecycle.state === "Paused") {
      await this.stop();
    }
    if (this.lifecycle.state === "Created") {
      this.lifecycle.transition("Disposed");
      this.cleanup();
      return;
    }

    const services = [...this.registry.list()].reverse();
    for (const service of services) {
      await service.dispose();
      this.healthMonitor.unwatch(service.id);
      this.registry.unregister(service.id);
    }

    this.eventBus.clear();
    await this.enterpriseEventBus.dispose();
    this.serviceMesh.dispose();
    this.workflowEngine.dispose();
    this.healthMonitor.clear();
    this.lifecycle.transition("Disposed");
  }

  async getHealth(): Promise<PlatformHealthReport> {
    return this.healthMonitor.report();
  }

  async pause(): Promise<void> {
    this.lifecycle.assertState("Started");
    for (const service of this.registry.list()) {
      if (service.getLifecycleState() === "Started" && service.pause) {
        await service.pause();
      }
    }
    this.lifecycle.transition("Paused");
  }

  async resume(): Promise<void> {
    this.lifecycle.assertState("Paused");
    for (const service of this.registry.list()) {
      if (service.getLifecycleState() === "Paused") {
        await service.start();
      }
    }
    this.lifecycle.transition("Started");
  }

  private cleanup(): void {
    this.eventBus.clear();
    void this.enterpriseEventBus.dispose();
    this.serviceMesh.dispose();
    this.workflowEngine.dispose();
    this.healthMonitor.clear();
    this.registry.clear();
  }
}

/** Factory helper — preferred entry for hosts and tests. */
export function createKernel(options?: KernelOptions): Kernel {
  return new Kernel(options);
}
