/**
 * Route-scoped Error Boundary — Sprint 1.1.1.
 * Isolates City / Concierge / Control Tower / Mission Control failures
 * without taking down the whole shell.
 */

import { Component, type ReactNode } from "react";
import { telemetry } from "@/integrations/telemetry";
import { prodLog, reliabilityCopy, sanitizeErrorMessage } from "@/production";

type Props = {
  children: ReactNode;
  /** Zone label for logs + recovery UI */
  zone: string;
  /** Optional safe recovery href */
  recoveryHref?: string;
};

type State = { error: Error | null };

export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    const zone = this.props.zone;
    prodLog("error", "route_error_boundary", {
      zone,
      message: sanitizeErrorMessage(error.message),
    });
    void telemetry.error(`route_error_boundary:${zone}`, error);
  }

  render() {
    if (this.state.error) {
      const copy = reliabilityCopy("boundary");
      const safe = sanitizeErrorMessage(this.state.error.message);
      const href = this.props.recoveryHref || "/dashboard?mode=executive";
      return (
        <div className="p-6 eds-page" role="alert" data-error-zone={this.props.zone}>
          <p className="eds-quiet-label">Route Reliability · {this.props.zone}</p>
          <h1 className="eds-type-h2 mt-1">{copy.title}</h1>
          <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">{copy.happened}</p>
          <p className="mt-1 eds-type-small">{copy.action}</p>
          <p className="mt-1 eds-type-helper">{copy.auto}</p>
          <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface-sunken)] p-3 text-sm">
            {safe}
          </pre>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              className="eds-btn eds-focus-ring h-10 rounded-[var(--eds-radius-md)] bg-[var(--eds-primary)] px-4 text-white"
              onClick={() => this.setState({ error: null })}
            >
              Retry {this.props.zone}
            </button>
            <a
              href={href}
              className="eds-btn eds-focus-ring inline-flex h-10 items-center rounded-[var(--eds-radius-md)] border border-[var(--eds-border)] px-4"
            >
              Go to Dashboard
            </a>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
