import { useQuery } from '@tanstack/react-query';
import { managementApi } from '../services/management';
import { Card, Badge, Spinner } from '../components/ui/Card';

export function AiPage() {
  const status = useQuery({ queryKey: ['ai-status'], queryFn: () => managementApi.aiStatus(), refetchInterval: 30_000 });
  const providers = useQuery({ queryKey: ['ai-providers'], queryFn: () => managementApi.aiProviders() });
  const models = useQuery({ queryKey: ['ai-models'], queryFn: () => managementApi.aiModels() });
  const costs = useQuery({ queryKey: ['ai-costs'], queryFn: () => managementApi.aiCosts() });
  const stats = useQuery({ queryKey: ['ai-statistics'], queryFn: () => managementApi.aiStatistics() });

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">AI Platform</h1>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card title="Requests">
          {stats.isLoading && <Spinner />}
          {stats.data && <p className="text-2xl font-bold">{stats.data.request_count}</p>}
        </Card>
        <Card title="Cache Hit Rate">
          {stats.data && (
            <p className="text-2xl font-bold">{((Number(stats.data.cache?.hit_rate) || 0) * 100).toFixed(0)}%</p>
          )}
        </Card>
        <Card title="Total Cost">
          {costs.data && (
            <p className="text-2xl font-bold">${Number(costs.data.summary?.total_usd || 0).toFixed(4)}</p>
          )}
        </Card>
        <Card title="Providers">
          {providers.data && <p className="text-2xl font-bold">{providers.data.providers?.length || 0}</p>}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Providers">
          {providers.isLoading && <Spinner />}
          <div className="space-y-3">
            {(providers.data?.providers || []).map((p) => (
              <div key={p.provider_id} className="flex items-center justify-between rounded border border-[var(--color-border)] p-3">
                <div>
                  <div className="font-medium">{p.name}</div>
                  <div className="text-xs text-[var(--color-muted)]">{p.provider_id}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={p.status === 'available' ? 'success' : 'warning'}>{p.status}</Badge>
                  <span className="text-xs text-[var(--color-muted)]">{p.latency_ms?.toFixed(0)}ms</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Models">
          {models.isLoading && <Spinner />}
          <div className="max-h-80 space-y-2 overflow-y-auto">
            {(models.data?.models || []).map((m) => (
              <div key={`${m.provider_id}:${m.model_id}`} className="flex justify-between text-sm">
                <span>{m.display_name}</span>
                <span className="text-[var(--color-muted)]">{m.context_window?.toLocaleString()} ctx</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Cost Breakdown">
          {costs.isLoading && <Spinner />}
          {costs.data?.summary && (
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt>Tokens in</dt>
              <dd>{costs.data.summary.tokens_in}</dd>
              <dt>Tokens out</dt>
              <dd>{costs.data.summary.tokens_out}</dd>
              <dt>By provider</dt>
              <dd>
                <pre className="text-xs">{JSON.stringify(costs.data.summary.by_provider, null, 2)}</pre>
              </dd>
            </dl>
          )}
        </Card>

        <Card title="Usage Statistics">
          {status.isLoading && <Spinner />}
          {status.data && (
            <pre className="max-h-64 overflow-auto text-xs whitespace-pre-wrap">
              {JSON.stringify(status.data, null, 2)}
            </pre>
          )}
        </Card>
      </div>
    </div>
  );
}
