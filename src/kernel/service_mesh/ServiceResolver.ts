import type { ServiceDescriptor } from "./ServiceDescriptor.js";
import type { IServiceDiscovery, IServiceResolver } from "./interfaces.js";
import type { SemVerRange, ServiceDependency } from "./types.js";
import { isVersionCompatible } from "./semver.js";

/**
 * Dependency and version-aware resolution.
 */
export class ServiceResolver implements IServiceResolver {
  constructor(private readonly discovery: IServiceDiscovery) {}

  isCompatible(version: string, range?: SemVerRange): boolean {
    return isVersionCompatible(version, range);
  }

  resolveByCapability(
    capability: string,
    range?: SemVerRange,
  ): ServiceDescriptor | undefined {
    const matches = this.discovery.discover({
      capability,
      ...(range !== undefined ? { version: range } : {}),
      healthyOnly: true,
    });
    return matches[0];
  }

  resolveDependencies(serviceId: string): {
    readonly ok: boolean;
    readonly missing: readonly ServiceDependency[];
    readonly resolved: readonly ServiceDescriptor[];
  } {
    const service = this.discovery.get(serviceId);
    if (!service) {
      return {
        ok: false,
        missing: [{ serviceId, optional: false }],
        resolved: [],
      };
    }

    const missing: ServiceDependency[] = [];
    const resolved: ServiceDescriptor[] = [];

    for (const dep of service.dependencies) {
      let match: ServiceDescriptor | undefined;

      if (dep.serviceId) {
        match = this.discovery.get(dep.serviceId);
        if (
          match &&
          dep.version &&
          !this.isCompatible(match.version, dep.version)
        ) {
          match = undefined;
        }
        if (
          match &&
          (match.status === "unhealthy" || match.status === "stopped")
        ) {
          match = undefined;
        }
      } else if (dep.capability) {
        match = this.resolveByCapability(dep.capability, dep.version);
      }

      if (!match) {
        if (!dep.optional) missing.push(dep);
      } else {
        resolved.push(match);
      }
    }

    return {
      ok: missing.length === 0,
      missing: Object.freeze(missing),
      resolved: Object.freeze(resolved),
    };
  }
}
