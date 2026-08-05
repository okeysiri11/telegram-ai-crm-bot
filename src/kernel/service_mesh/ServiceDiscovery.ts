import { ServiceDescriptor } from "./ServiceDescriptor.js";
import type { IServiceDiscovery } from "./interfaces.js";
import type { DiscoveryQuery, ServiceDescriptorInit } from "./types.js";
import { isVersionCompatible } from "./semver.js";

/**
 * Automatic registration and query-based discovery.
 */
export class ServiceDiscovery implements IServiceDiscovery {
  private readonly byId = new Map<string, ServiceDescriptor>();

  register(
    descriptor: ServiceDescriptor | ServiceDescriptorInit,
  ): ServiceDescriptor {
    const desc =
      descriptor instanceof ServiceDescriptor
        ? descriptor
        : ServiceDescriptor.create(descriptor);
    this.byId.set(desc.id, desc);
    if (desc.status === "starting") {
      desc.setStatus("healthy");
    }
    return desc;
  }

  unregister(serviceId: string): boolean {
    return this.byId.delete(serviceId);
  }

  get(serviceId: string): ServiceDescriptor | undefined {
    return this.byId.get(serviceId);
  }

  list(): readonly ServiceDescriptor[] {
    return Object.freeze([...this.byId.values()]);
  }

  discover(query: DiscoveryQuery): readonly ServiceDescriptor[] {
    let results = [...this.byId.values()];

    if (query.id) {
      results = results.filter((s) => s.id === query.id);
    }
    if (query.capability) {
      const cap = query.capability;
      results = results.filter((s) => s.hasCapability(cap));
    }
    if (query.tag) {
      results = results.filter((s) => s.hasTag(query.tag!));
    }
    if (query.tags && query.tags.length > 0) {
      results = results.filter((s) => s.hasAllTags(query.tags!));
    }
    if (query.version) {
      results = results.filter((s) =>
        isVersionCompatible(s.version, query.version),
      );
    }
    if (query.healthyOnly) {
      results = results.filter(
        (s) => s.status === "healthy" || s.status === "degraded",
      );
    }
    if (query.protocol) {
      results = results.filter((s) =>
        s.endpoints.some((e) => e.protocol === query.protocol),
      );
    }

    results.sort((a, b) => b.priority - a.priority || a.id.localeCompare(b.id));
    return Object.freeze(results);
  }

  clear(): void {
    this.byId.clear();
  }
}
