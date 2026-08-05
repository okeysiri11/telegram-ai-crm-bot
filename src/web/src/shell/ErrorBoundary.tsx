import { Component, type ReactNode } from "react";
import { telemetry } from "@/integrations/telemetry";
import { prodLog, reliabilityCopy, sanitizeErrorMessage } from "@/production";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error) {
    prodLog("error", "react_error_boundary", { message: sanitizeErrorMessage(error.message) });
    void telemetry.error("react_error_boundary", error);
  }
  render() {
    if (this.state.error) {
      const copy = reliabilityCopy("boundary");
      const safe = sanitizeErrorMessage(this.state.error.message);
      return (
        <div className="p-8 eds-page" role="alert">
          <p className="eds-quiet-label">Reliability</p>
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
              Try this screen again
            </button>
            <a
              href="/dashboard?mode=executive"
              className="eds-btn eds-focus-ring inline-flex h-10 items-center rounded-[var(--eds-radius-md)] border border-[var(--eds-border)] px-4"
            >
              Go to Dashboard
            </a>
            <a
              href="/workspace"
              className="eds-btn eds-focus-ring inline-flex h-10 items-center rounded-[var(--eds-radius-md)] border border-[var(--eds-border)] px-4"
            >
              Go to Workspace
            </a>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
