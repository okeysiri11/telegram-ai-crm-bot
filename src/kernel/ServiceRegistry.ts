import type { IService } from "./interfaces/IService.js";
import type { IServiceRegistry } from "./interfaces/IServiceRegistry.js";
import type { ServiceRegistrationOptions } from "./interfaces/types.js";

export class ServiceNotFoundError extends Error {
  constructor(readonly serviceId: string) {
    super(`Service not found: ${serviceId}`);
    this.name = "ServiceNotFoundError";
  }
}

export class ServiceAlreadyRegisteredError extends Error {
  constructor(readonly serviceId: string) {
    super(`Service already registered: ${serviceId}`);
    this.name = "ServiceAlreadyRegisteredError";
  }
}

/**
 * In-memory DI-ready service registry.
 */
export class ServiceRegistry implements IServiceRegistry {
  private readonly services = new Map<string, IService>();

  register<T extends IService>(
    service: T,
    options?: ServiceRegistrationOptions,
  ): void {
    const replace = options?.replace === true;
    if (this.services.has(service.id) && !replace) {
      throw new ServiceAlreadyRegisteredError(service.id);
    }
    this.services.set(service.id, service);
  }

  unregister(id: string): boolean {
    return this.services.delete(id);
  }

  resolve<T extends IService = IService>(id: string): T {
    const service = this.services.get(id);
    if (!service) {
      throw new ServiceNotFoundError(id);
    }
    return service as T;
  }

  exists(id: string): boolean {
    return this.services.has(id);
  }

  list(): readonly IService[] {
    return Object.freeze([...this.services.values()]);
  }

  clear(): void {
    this.services.clear();
  }
}
