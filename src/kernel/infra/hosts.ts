import { InfrastructureService } from "./InfrastructureService.js";

/** Host for future UPP providers — no vendor imports. */
export const PROVIDER_HOST_SERVICE_ID = "ados.provider_host";

export class ProviderHostService extends InfrastructureService {
  constructor() {
    super({
      id: PROVIDER_HOST_SERVICE_ID,
      kind: "provider-host",
      version: "1.0.0",
      critical: true,
    });
  }
}

/** Host for AI Runtime — stub ready for sprint wiring. */
export const RUNTIME_HOST_SERVICE_ID = "ados.runtime_host";

export class RuntimeHostService extends InfrastructureService {
  constructor() {
    super({
      id: RUNTIME_HOST_SERVICE_ID,
      kind: "runtime-host",
      version: "1.0.0",
      critical: true,
    });
  }
}

/** Host for Enterprise Memory — stub ready for memory engine. */
export const MEMORY_HOST_SERVICE_ID = "ados.memory_host";

export class MemoryHostService extends InfrastructureService {
  constructor() {
    super({
      id: MEMORY_HOST_SERVICE_ID,
      kind: "memory-host",
      version: "1.0.0",
      critical: true,
    });
  }
}

/** Host for SDK Plugin Manager — future plugins register here. */
export const PLUGIN_HOST_SERVICE_ID = "ados.plugin_host";

export class PluginHostService extends InfrastructureService {
  private readonly pluginIds = new Set<string>();

  constructor() {
    super({
      id: PLUGIN_HOST_SERVICE_ID,
      kind: "plugin-host",
      version: "1.0.0",
      critical: false,
    });
  }

  /** Extension seam: plugins register ids without Core changes. */
  registerPluginId(pluginId: string): void {
    this.pluginIds.add(pluginId);
  }

  listPluginIds(): readonly string[] {
    return Object.freeze([...this.pluginIds]);
  }
}
