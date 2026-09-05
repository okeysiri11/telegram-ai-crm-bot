/**
 * Safe loader for /workspace/recruiting/integrations.
 * Import failures stay local — they must not hit the global Reliability screen.
 */

import { lazy, Suspense, useMemo, useState } from "react";
import { ProviderConnectionBoundary, ProviderConnectionFallback } from "./ProviderConnectionBoundary";

export function SafeProviderConnectionsRoute() {
  const [generation, setGeneration] = useState(0);
  const retry = () => setGeneration((n) => n + 1);
  const LazyPage = useMemo(
    () =>
      lazy(() =>
        import("./ProviderConnectionsPage")
          .then((m) => ({ default: m.ProviderConnectionsPage }))
          .catch(() => ({
            default: function ProviderConnectionsLoadError() {
              return (
                <ProviderConnectionFallback
                  onRetry={retry}
                  onReload={() => window.location.reload()}
                />
              );
            },
          })),
      ),
    [generation],
  );

  return (
    <ProviderConnectionBoundary key={generation} onRetry={retry}>
      <Suspense fallback={<p className="eds-type-helper">Загрузка подключений…</p>}>
        <LazyPage />
      </Suspense>
    </ProviderConnectionBoundary>
  );
}
