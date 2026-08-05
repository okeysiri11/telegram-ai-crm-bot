import type {
  EndpointProtocol,
  ServiceEndpointInit,
  ServiceInvoker,
} from "./types.js";

/**
 * Addressable endpoint for a mesh service (local or remote-ready).
 */
export class ServiceEndpoint {
  readonly id: string;
  readonly protocol: EndpointProtocol;
  readonly address: string;
  readonly capabilities: readonly string[];
  readonly weight: number;
  readonly metadata: Readonly<Record<string, unknown>>;
  private readonly invoker?: ServiceInvoker;

  constructor(init: ServiceEndpointInit) {
    this.id = init.id;
    this.protocol = init.protocol ?? "local";
    this.address = init.address ?? `local://${init.id}`;
    this.capabilities = Object.freeze([...(init.capabilities ?? [])]);
    this.weight = init.weight ?? 1;
    this.metadata = Object.freeze({ ...(init.metadata ?? {}) });
    if (init.invoke) {
      this.invoker = init.invoke;
    }
  }

  get isLocal(): boolean {
    return this.protocol === "local" || this.protocol === "internal";
  }

  get isRemoteReady(): boolean {
    return this.protocol === "http" || this.protocol === "grpc";
  }

  canInvoke(): boolean {
    return typeof this.invoker === "function";
  }

  async invoke(method: string, input?: unknown): Promise<unknown> {
    if (!this.invoker) {
      throw new Error(
        `Endpoint ${this.id} has no local invoker (remote-only or unbound)`,
      );
    }
    return this.invoker(method, input);
  }

  supportsCapability(capability: string): boolean {
    return this.capabilities.includes(capability);
  }

  toJSON(): Record<string, unknown> {
    return {
      id: this.id,
      protocol: this.protocol,
      address: this.address,
      capabilities: this.capabilities,
      weight: this.weight,
      metadata: this.metadata,
      canInvoke: this.canInvoke(),
    };
  }
}
