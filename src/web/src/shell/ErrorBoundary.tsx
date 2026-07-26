import { Component, type ReactNode } from "react";
import { telemetry } from "@/integrations/telemetry";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error) {
    void telemetry.error("react_error_boundary", error);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="p-8">
          <h1 className="text-xl font-semibold">Something went wrong</h1>
          <pre className="mt-3 overflow-auto rounded bg-black/5 p-3 text-sm">{this.state.error.message}</pre>
          <button
            type="button"
            className="mt-4 rounded-md border px-3 py-2 text-sm"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
