import type { IService } from "./IService.js";
import type { ServiceRegistrationOptions } from "./types.js";

/**
 * Dependency-injection ready service registry.
 * Resolves by service id; never knows about business verticals.
 */
export interface IServiceRegistry {
  register<T extends IService>(
    service: T,
    options?: ServiceRegistrationOptions,
  ): void;
  unregister(id: string): boolean;
  resolve<T extends IService = IService>(id: string): T;
  exists(id: string): boolean;
  list(): readonly IService[];
  clear(): void;
}
