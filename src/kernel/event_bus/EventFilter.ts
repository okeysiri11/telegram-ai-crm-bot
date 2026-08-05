import type { ADOSEvent, EventFilterCriteria, EventFilterFn } from "./types.js";

/**
 * Compiles filter criteria into a predicate for dispatch, history, and replay.
 */
export class EventFilter {
  static compile(criteria?: EventFilterCriteria): EventFilterFn {
    if (!criteria) {
      return () => true;
    }

    const typeSet =
      criteria.types && criteria.types.length > 0
        ? new Set(criteria.types)
        : null;
    const pattern = criteria.typePattern
      ? wildcardToRegExp(criteria.typePattern)
      : null;

    return (event: ADOSEvent): boolean => {
      if (typeSet && !typeSet.has(event.type)) {
        return false;
      }
      if (pattern && !pattern.test(event.type)) {
        return false;
      }
      if (
        criteria.minPriority !== undefined &&
        event.priority < criteria.minPriority
      ) {
        return false;
      }
      if (
        criteria.maxPriority !== undefined &&
        event.priority > criteria.maxPriority
      ) {
        return false;
      }
      if (
        criteria.source !== undefined &&
        event.metadata["source"] !== criteria.source
      ) {
        return false;
      }
      if (criteria.since !== undefined && event.timestamp < criteria.since) {
        return false;
      }
      if (criteria.until !== undefined && event.timestamp > criteria.until) {
        return false;
      }
      if (criteria.stickyOnly === true && !event.sticky) {
        return false;
      }
      if (criteria.predicate && !criteria.predicate(event)) {
        return false;
      }
      return true;
    };
  }

  static matchesWildcard(pattern: string, eventType: string): boolean {
    if (pattern === "*" || pattern === "**") {
      return true;
    }
    return wildcardToRegExp(pattern).test(eventType);
  }
}

function wildcardToRegExp(pattern: string): RegExp {
  // Escape regex specials except * which means "any segment/chars"
  const escaped = pattern
    .replace(/[.+^${}()|[\]\\]/g, "\\$&")
    .replace(/\*/g, ".*");
  return new RegExp(`^${escaped}$`);
}
