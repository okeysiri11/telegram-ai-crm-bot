/**
 * Local Odessa 3D error boundary — keeps /enterprise-city alive when the 3D view throws.
 */

import { Component, type ErrorInfo, type ReactNode } from "react";

export type OdessaCaughtError = {
  name: string;
  message: string;
  stack: string;
};

type Props = {
  children: ReactNode;
  fallback: (error: OdessaCaughtError, reset: () => void) => ReactNode;
};

type State = { error: OdessaCaughtError | null };

export class Odessa3DErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return {
      error: {
        name: error?.name || "Error",
        message: error?.message || String(error),
        stack: typeof error?.stack === "string" ? error.stack.split("\n").slice(0, 8).join("\n") : "",
      },
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[Odessa3D] view render failed", error, info.componentStack);
  }

  reset = () => this.setState({ error: null });

  render() {
    if (this.state.error) {
      return this.props.fallback(this.state.error, this.reset);
    }
    return this.props.children;
  }
}

export type OdessaRuntimeFault = {
  phase: string;
  errorName: string;
  errorMessage: string;
  stack: string;
  manifest: string;
  controller: string;
  webgl: string;
  progressJson: string;
};

export function OdessaRuntimeFaultPanel(props: OdessaRuntimeFault & { onRetry?: () => void }) {
  return (
    <div className="ec-3d-runtime-fault p-3 text-xs" data-testid="odessa-runtime-fault" role="alert">
      <p className="mb-1 font-semibold">Odessa 3D runtime diagnostic (temporary)</p>
      <dl className="grid grid-cols-1 gap-1">
        <div>
          <dt className="opacity-70">phase</dt>
          <dd data-testid="odessa-fault-phase">{props.phase}</dd>
        </div>
        <div>
          <dt className="opacity-70">error.name</dt>
          <dd>{props.errorName}</dd>
        </div>
        <div>
          <dt className="opacity-70">error.message</dt>
          <dd>{props.errorMessage}</dd>
        </div>
        <div>
          <dt className="opacity-70">stack</dt>
          <dd>
            <pre className="max-h-32 overflow-auto whitespace-pre-wrap">{props.stack || "—"}</pre>
          </dd>
        </div>
        <div>
          <dt className="opacity-70">manifest</dt>
          <dd>{props.manifest}</dd>
        </div>
        <div>
          <dt className="opacity-70">controller</dt>
          <dd>{props.controller}</dd>
        </div>
        <div>
          <dt className="opacity-70">webgl</dt>
          <dd>{props.webgl}</dd>
        </div>
        <div>
          <dt className="opacity-70">progress</dt>
          <dd>
            <pre className="max-h-32 overflow-auto whitespace-pre-wrap">{props.progressJson}</pre>
          </dd>
        </div>
      </dl>
      {props.onRetry ? (
        <button type="button" className="mt-2 min-h-11 rounded border px-3" onClick={props.onRetry}>
          Retry 3D
        </button>
      ) : null}
    </div>
  );
}
