import type { ServiceDescriptor } from "./ServiceDescriptor.js";
import type { ServicePolicyRule } from "./types.js";

/**
 * Allow/deny policies for mesh routing (capability, tags, priority).
 */
export class ServicePolicy {
  private readonly rules: ServicePolicyRule[];

  constructor(rules: readonly ServicePolicyRule[] = []) {
    this.rules = [...rules];
  }

  addRule(rule: ServicePolicyRule): void {
    this.rules.push(rule);
  }

  removeRule(id: string): boolean {
    const idx = this.rules.findIndex((r) => r.id === id);
    if (idx < 0) return false;
    this.rules.splice(idx, 1);
    return true;
  }

  list(): readonly ServicePolicyRule[] {
    return Object.freeze([...this.rules]);
  }

  /**
   * Deny wins if any deny matches; otherwise allow if any allow matches
   * or if there are no rules.
   */
  isAllowed(service: ServiceDescriptor, capability?: string): boolean {
    if (this.rules.length === 0) return true;

    const matched = this.rules.filter((rule) =>
      this.matches(rule, service, capability),
    );
    if (matched.length === 0) return true;

    if (matched.some((r) => r.action === "deny")) return false;
    return matched.some((r) => r.action === "allow");
  }

  filterAllowed(
    services: readonly ServiceDescriptor[],
    capability?: string,
  ): ServiceDescriptor[] {
    return services.filter((s) => this.isAllowed(s, capability));
  }

  private matches(
    rule: ServicePolicyRule,
    service: ServiceDescriptor,
    capability?: string,
  ): boolean {
    if (rule.serviceId && rule.serviceId !== service.id) return false;
    if (rule.capability) {
      if (capability && rule.capability !== capability) return false;
      if (!capability && !service.hasCapability(rule.capability)) return false;
    }
    if (rule.requiredTags && !service.hasAllTags(rule.requiredTags)) {
      return false;
    }
    if (
      rule.minPriority !== undefined &&
      service.priority < rule.minPriority
    ) {
      return false;
    }
    return true;
  }
}
