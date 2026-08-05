import type { IService } from "../interfaces/IService.js";
import { ServiceDescriptor } from "./ServiceDescriptor.js";
import type { ServiceDescriptorInit } from "./types.js";

/**
 * Bridges kernel lifecycle IService → mesh ServiceDescriptor.
 * No business knowledge — infrastructure only.
 */
export function descriptorFromKernelService(
  service: IService,
  extras?: Partial<ServiceDescriptorInit>,
): ServiceDescriptor {
  const init: ServiceDescriptorInit = {
    id: service.id,
    version: service.version,
    name: extras?.name ?? service.id,
    capabilities: extras?.capabilities ?? [`service:${service.id}`, service.kind],
    tags: extras?.tags ?? [service.kind, "kernel"],
    priority: extras?.priority ?? 0,
    dependencies: extras?.dependencies ?? [],
    owner: extras?.owner ?? "ados.kernel",
    endpoints: extras?.endpoints ?? [
      {
        id: `${service.id}:lifecycle`,
        protocol: "local",
        capabilities: extras?.capabilities ?? [`service:${service.id}`],
        invoke: async (method: string) => {
          if (method === "health") return service.health();
          if (method === "uptime") return service.uptimeMs();
          if (method === "lifecycle") return service.getLifecycleState();
          throw new Error(`Unknown method: ${method}`);
        },
      },
    ],
    ...(extras?.nodeId !== undefined ? { nodeId: extras.nodeId } : {}),
    ...(extras?.metadata !== undefined ? { metadata: extras.metadata } : {}),
  };
  return ServiceDescriptor.create(init);
}
