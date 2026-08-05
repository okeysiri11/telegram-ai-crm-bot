import type { IBootLoader, BootLoaderContext } from "./interfaces/IBootLoader.js";
import type { IService } from "./interfaces/IService.js";
import type { BootPhase } from "./interfaces/types.js";
import { EventBusService } from "./infra/EventBusService.js";
import {
  MemoryHostService,
  PluginHostService,
  ProviderHostService,
  RuntimeHostService,
} from "./infra/hosts.js";

export interface BootLoaderOptions {
  /**
   * Optional extra infrastructure services (plugins / test doubles).
   * Must not be business verticals — caller responsibility.
   */
  readonly extraServices?: readonly IService[];
}

/**
 * Infrastructure boot sequence.
 * Never imports CRM, ERP, Marketplace, AI Studio, or other verticals.
 */
export class BootLoader implements IBootLoader {
  private readonly _phases: BootPhase[] = [];
  private readonly extraServices: readonly IService[];

  constructor(options?: BootLoaderOptions) {
    this.extraServices = options?.extraServices ?? [];
  }

  get phasesCompleted(): readonly BootPhase[] {
    return Object.freeze([...this._phases]);
  }

  async boot(context: BootLoaderContext): Promise<void> {
    this._phases.length = 0;
    const { registry, config, enterpriseEventBus } = context;

    this.mark("load-config");
    if (!config.version) {
      throw new Error("Kernel config missing version");
    }

    this.mark("register-services");
    const eventBusService = new EventBusService(enterpriseEventBus);
    const providerHost = new ProviderHostService();
    const runtimeHost = new RuntimeHostService();
    const memoryHost = new MemoryHostService();
    const pluginHost = new PluginHostService();

    const coreServices: IService[] = [
      eventBusService,
      providerHost,
      runtimeHost,
      memoryHost,
      pluginHost,
      ...this.extraServices,
    ];

    for (const service of coreServices) {
      if (!registry.exists(service.id)) {
        registry.register(service);
      }
    }

    this.mark("initialize-providers");
    if (config.featureFlags["providers"] !== false) {
      await this.initAndStart(registry.resolve(providerHost.id));
    }

    this.mark("initialize-runtime");
    if (config.featureFlags["runtime"] !== false) {
      await this.initAndStart(registry.resolve(runtimeHost.id));
    }

    this.mark("initialize-memory");
    if (config.featureFlags["memory"] !== false) {
      await this.initAndStart(registry.resolve(memoryHost.id));
    }

    this.mark("initialize-plugins");
    if (config.featureFlags["plugins"] !== false) {
      await this.initAndStart(registry.resolve(pluginHost.id));
    }

    this.mark("start-services");
    for (const service of registry.list()) {
      const state = service.getLifecycleState();
      if (state === "Created") {
        await service.initialize();
      }
      const afterInit = service.getLifecycleState();
      if (
        afterInit === "Initialized" ||
        afterInit === "Stopped" ||
        afterInit === "Paused"
      ) {
        await service.start();
      }
    }

    this.mark("boot-completed");
  }

  private mark(phase: BootPhase): void {
    this._phases.push(phase);
  }

  private async initAndStart(service: IService): Promise<void> {
    if (service.getLifecycleState() === "Created") {
      await service.initialize();
    }
    if (
      service.getLifecycleState() === "Initialized" ||
      service.getLifecycleState() === "Stopped" ||
      service.getLifecycleState() === "Paused"
    ) {
      await service.start();
    }
  }
}
