import { ServiceEndpoint } from "./ServiceEndpoint.js";
import type {
  MeshHealthStatus,
  ServiceDependency,
  ServiceDescriptorInit,
} from "./types.js";

/**
 * Canonical mesh registration record for a service instance.
 */
export class ServiceDescriptor {
  readonly id: string;
  readonly name: string;
  readonly version: string;
  readonly capabilities: readonly string[];
  readonly tags: readonly string[];
  readonly priority: number;
  readonly dependencies: readonly ServiceDependency[];
  readonly endpoints: readonly ServiceEndpoint[];
  readonly owner: string;
  readonly nodeId: string;
  readonly metadata: Readonly<Record<string, unknown>>;
  readonly registeredAt: string;

  private _status: MeshHealthStatus;

  private constructor(
    init: ServiceDescriptorInit & { status?: MeshHealthStatus },
    endpoints: readonly ServiceEndpoint[],
  ) {
    this.id = init.id;
    this.name = init.name ?? init.id;
    this.version = init.version;
    this.capabilities = Object.freeze([...(init.capabilities ?? [])]);
    this.tags = Object.freeze([...(init.tags ?? [])]);
    this.priority = init.priority ?? 0;
    this.dependencies = Object.freeze([...(init.dependencies ?? [])]);
    this.endpoints = Object.freeze(endpoints);
    this.owner = init.owner ?? "unknown";
    this.nodeId = init.nodeId ?? "local";
    this.metadata = Object.freeze({ ...(init.metadata ?? {}) });
    this.registeredAt = new Date().toISOString();
    this._status = init.status ?? "starting";
  }

  static create(init: ServiceDescriptorInit): ServiceDescriptor {
    if (!init.id || !init.version) {
      throw new Error("ServiceDescriptor requires id and version");
    }
    const endpoints = (init.endpoints ?? []).map(
      (e) => new ServiceEndpoint(e),
    );
    // Default local endpoint if none provided
    const resolved =
      endpoints.length > 0
        ? endpoints
        : [
            new ServiceEndpoint({
              id: `${init.id}:default`,
              protocol: "local",
              capabilities: init.capabilities ?? [],
            }),
          ];
    return new ServiceDescriptor(init, resolved);
  }

  get status(): MeshHealthStatus {
    return this._status;
  }

  setStatus(status: MeshHealthStatus): void {
    this._status = status;
  }

  hasCapability(capability: string): boolean {
    return (
      this.capabilities.includes(capability) ||
      this.endpoints.some((e) => e.supportsCapability(capability))
    );
  }

  hasTag(tag: string): boolean {
    return this.tags.includes(tag);
  }

  hasAllTags(tags: readonly string[]): boolean {
    return tags.every((t) => this.tags.includes(t));
  }

  primaryEndpoint(): ServiceEndpoint | undefined {
    return this.endpoints[0];
  }

  findEndpoint(capability?: string): ServiceEndpoint | undefined {
    if (!capability) return this.primaryEndpoint();
    return (
      this.endpoints.find((e) => e.supportsCapability(capability)) ??
      (this.capabilities.includes(capability)
        ? this.primaryEndpoint()
        : undefined)
    );
  }

  toJSON(): Record<string, unknown> {
    return {
      id: this.id,
      name: this.name,
      version: this.version,
      capabilities: this.capabilities,
      tags: this.tags,
      priority: this.priority,
      dependencies: this.dependencies,
      endpoints: this.endpoints.map((e) => e.toJSON()),
      owner: this.owner,
      nodeId: this.nodeId,
      status: this._status,
      registeredAt: this.registeredAt,
      metadata: this.metadata,
    };
  }
}
