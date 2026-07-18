import { useQuery } from '@tanstack/react-query';
import { Badge, Card, Spinner } from '../components/ui/Card';
import { managementApi } from '../services/management';

type MigrationReport = {
  summary?: {
    platform_routed_percent?: number;
    runtime_platform_percent?: number;
    remaining_legacy_count?: number;
  };
  remaining_legacy?: string[];
  migrated_components?: string[];
  feature_flags?: Record<string, boolean>;
  deprecated_apis?: Array<{ name: string; replacement: string; hit_count?: number; removal_target?: string }>;
  health?: { ok?: boolean; unhealthy_count?: number; checks?: Array<{ subsystem: string; status: string; active_route: string }> };
  runtime?: { migration_ratio?: { platform_percent?: number; legacy_percent?: number } };
};

function pct(value: number | undefined) {
  return value != null ? `${value.toFixed(1)}%` : '—';
}

export function MigrationDashboardPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['migration'],
    queryFn: () => managementApi.migration() as Promise<MigrationReport>,
    refetchInterval: 30_000,
  });

  const platformPct =
    data?.runtime?.migration_ratio?.platform_percent ??
    data?.summary?.runtime_platform_percent ??
    data?.summary?.platform_routed_percent ??
    0;
  const legacyPct = 100 - (platformPct || 0);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Migration Dashboard</h1>
          <p className="text-sm text-[var(--color-muted)]">
            Platform Core vs legacy compatibility mode
          </p>
        </div>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm"
        >
          Refresh
        </button>
      </div>

      {isLoading && <Spinner />}
      {isError && <p className="text-red-500">Failed to load migration report</p>}

      {data && (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <Card title="Platform">
              <p className="text-3xl font-bold text-emerald-600">{pct(platformPct)}</p>
              <p className="text-xs text-[var(--color-muted)]">Default execution path</p>
            </Card>
            <Card title="Legacy">
              <p className="text-3xl font-bold text-amber-600">{pct(legacyPct)}</p>
              <p className="text-xs text-[var(--color-muted)]">Compatibility mode</p>
            </Card>
            <Card title="Remaining Legacy">
              <p className="text-3xl font-bold">{data.summary?.remaining_legacy_count ?? 0}</p>
              <p className="text-xs text-[var(--color-muted)]">Subsystems not on Platform</p>
            </Card>
            <Card title="Migration Health">
              <p className="text-3xl font-bold">
                {data.health?.ok ? (
                  <Badge variant="success">Healthy</Badge>
                ) : (
                  <Badge variant="warning">{data.health?.unhealthy_count ?? 0} issues</Badge>
                )}
              </p>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Feature Flags">
              <div className="space-y-2">
                {Object.entries(data.feature_flags ?? {}).map(([key, enabled]) => (
                  <div key={key} className="flex items-center justify-between text-sm">
                    <code>{key}</code>
                    <Badge variant={enabled ? 'warning' : 'success'}>{enabled ? 'legacy' : 'platform'}</Badge>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="Subsystem Health">
              <div className="max-h-64 space-y-2 overflow-auto">
                {(data.health?.checks ?? []).map((check) => (
                  <div key={check.subsystem} className="flex items-center justify-between text-sm">
                    <span>{check.subsystem}</span>
                    <span className="flex gap-2">
                      <Badge variant={check.active_route === 'platform' ? 'success' : 'warning'}>
                        {check.active_route}
                      </Badge>
                      <Badge variant={check.status === 'healthy' ? 'success' : 'danger'}>{check.status}</Badge>
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card title="Deprecated APIs">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="py-2 pr-4">API</th>
                    <th className="py-2 pr-4">Replacement</th>
                    <th className="py-2 pr-4">Calls</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.deprecated_apis ?? []).map((api) => (
                    <tr key={api.name} className="border-b border-[var(--color-border)]">
                      <td className="py-2 pr-4 font-mono text-xs">{api.name}</td>
                      <td className="py-2 pr-4">{api.replacement}</td>
                      <td className="py-2 pr-4">{api.hit_count ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Migrated Components">
              <ul className="list-inside list-disc text-sm">
                {(data.migrated_components ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
                {(data.migrated_components ?? []).length === 0 && (
                  <li className="text-[var(--color-muted)]">No runtime hits yet</li>
                )}
              </ul>
            </Card>
            <Card title="Remaining Legacy">
              <ul className="list-inside list-disc text-sm">
                {(data.remaining_legacy ?? []).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
