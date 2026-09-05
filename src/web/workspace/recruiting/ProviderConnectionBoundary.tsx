/**
 * Local fallback for provider connection UI.
 * Must not escalate to the global Reliability / RouteErrorBoundary screen.
 */

import { Component, type ReactNode } from "react";
import { Button } from "@/ui";
import { PROVIDER_WIZARD_LOAD_ERROR_RU } from "./providerConnectionCopy";

type Props = {
  children: ReactNode;
  onRetry?: () => void;
};

type State = { error: Error | null };

export function ProviderConnectionFallback({
  onRetry,
  onReload,
}: {
  onRetry: () => void;
  onReload: () => void;
}) {
  return (
    <div className="eds-card p-4" role="alert" data-testid="provider-connection-fallback">
      <p className="eds-type-body whitespace-pre-line">{PROVIDER_WIZARD_LOAD_ERROR_RU}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button size="sm" onClick={onRetry} data-testid="provider-connection-retry">
          Повторить
        </Button>
        <Button size="sm" variant="secondary" onClick={onReload} data-testid="provider-connection-reload">
          Обновить страницу
        </Button>
      </div>
    </div>
  );
}

export class ProviderConnectionBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <ProviderConnectionFallback
          onRetry={() => {
            this.setState({ error: null });
            this.props.onRetry?.();
          }}
          onReload={() => window.location.reload()}
        />
      );
    }
    return this.props.children;
  }
}
