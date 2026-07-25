import { Component, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  render() {
    if (this.state.error) {
      return (
        <div className="p-8">
          <h1 className="text-xl font-semibold">Something went wrong</h1>
          <pre className="mt-3 overflow-auto rounded bg-black/5 p-3 text-sm">{this.state.error.message}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
