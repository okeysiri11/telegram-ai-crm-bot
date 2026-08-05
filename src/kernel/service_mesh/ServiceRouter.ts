import type { IServiceDiscovery, IServiceRouter } from "./interfaces.js";
import { LoadBalancer, type EndpointCandidate } from "./LoadBalancer.js";
import { ServicePolicy } from "./ServicePolicy.js";
import type {
  LoadBalanceStrategy,
  RouteRequest,
  RouteResult,
  ServicePolicyRule,
} from "./types.js";

/**
 * Routes local (and remote-ready) invocations with policy + failover.
 */
export class ServiceRouter implements IServiceRouter {
  private readonly balancer: LoadBalancer;
  private readonly policy: ServicePolicy;

  constructor(
    private readonly discovery: IServiceDiscovery,
    options?: {
      strategy?: LoadBalanceStrategy;
      policies?: readonly ServicePolicyRule[];
    },
  ) {
    this.balancer = new LoadBalancer(options?.strategy ?? "priority");
    this.policy = new ServicePolicy(options?.policies ?? []);
  }

  get policies(): ServicePolicy {
    return this.policy;
  }

  async callLocal<T = unknown>(
    serviceId: string,
    method: string,
    input?: unknown,
  ): Promise<RouteResult<T>> {
    return this.route<T>({ serviceId, method, input });
  }

  async route<T = unknown>(request: RouteRequest): Promise<RouteResult<T>> {
    const candidates = this.collectCandidates(request);
    if (candidates.length === 0) {
      return {
        ok: false,
        serviceId: request.serviceId ?? "",
        endpointId: "",
        version: "",
        error: "No eligible service/endpoint found",
        failoverCount: 0,
      };
    }

    const primary = this.balancer.select(candidates);
    if (!primary) {
      return {
        ok: false,
        serviceId: request.serviceId ?? "",
        endpointId: "",
        version: "",
        error: "Load balancer returned no endpoint",
        failoverCount: 0,
      };
    }

    const chain = [primary, ...this.balancer.failoverChain(candidates, primary)];
    let failoverCount = 0;
    let lastError = "Unknown routing error";

    for (const candidate of chain) {
      try {
        if (!candidate.endpoint.canInvoke()) {
          if (candidate.endpoint.isRemoteReady) {
            lastError = `Remote endpoint ${candidate.endpoint.id} not bound in this runtime`;
            failoverCount += 1;
            continue;
          }
          lastError = `Endpoint ${candidate.endpoint.id} cannot invoke`;
          failoverCount += 1;
          continue;
        }
        const data = (await candidate.endpoint.invoke(
          request.method,
          request.input,
        )) as T;
        return {
          ok: true,
          serviceId: candidate.service.id,
          endpointId: candidate.endpoint.id,
          version: candidate.service.version,
          data,
          failoverCount,
        };
      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);
        failoverCount += 1;
      }
    }

    return {
      ok: false,
      serviceId: primary.service.id,
      endpointId: primary.endpoint.id,
      version: primary.service.version,
      error: lastError,
      failoverCount: Math.max(0, failoverCount - 1),
    };
  }

  private collectCandidates(request: RouteRequest): EndpointCandidate[] {
    let services = request.serviceId
      ? this.discovery
          .discover({
            id: request.serviceId,
            ...(request.version !== undefined
              ? { version: request.version }
              : {}),
            healthyOnly: true,
          })
          .slice()
      : this.discovery
          .discover({
            ...(request.capability !== undefined
              ? { capability: request.capability }
              : {}),
            ...(request.version !== undefined
              ? { version: request.version }
              : {}),
            ...(request.tags !== undefined ? { tags: request.tags } : {}),
            healthyOnly: true,
          })
          .slice();

    services = this.policy.filterAllowed(services, request.capability);

    if (request.preferNodeId) {
      services.sort((a, b) => {
        const ap = a.nodeId === request.preferNodeId ? 1 : 0;
        const bp = b.nodeId === request.preferNodeId ? 1 : 0;
        return bp - ap;
      });
    }

    const candidates: EndpointCandidate[] = [];
    for (const service of services) {
      const endpoint = request.capability
        ? service.findEndpoint(request.capability)
        : service.primaryEndpoint();
      if (endpoint) {
        candidates.push({ service, endpoint });
      }
    }
    return candidates;
  }
}
