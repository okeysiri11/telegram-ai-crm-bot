import { useQuery } from '@tanstack/react-query';
import { managementApi } from '../services/management';
import { Card, Badge, Spinner } from '../components/ui/Card';

interface WorkflowRecord {
  workflow_id: string;
  name: string;
  version: string;
  category: string;
  state: string;
  description?: string;
  tags?: string[];
}

interface HistoryEntry {
  execution_id: string;
  workflow_id: string;
  status: string;
  latency_ms: number;
  cost_usd: number;
  timestamp: string;
}

interface ActiveExecution {
  execution_id: string;
  workflow_id: string;
  status: string;
  current_step: string | null;
}

export function AiWorkflowsPage() {
  const list = useQuery({ queryKey: ['ai-workflows-list'], queryFn: () => managementApi.aiWorkflowsList(), refetchInterval: 30_000 });
  const history = useQuery({ queryKey: ['ai-workflows-history'], queryFn: () => managementApi.aiWorkflowsHistory(), refetchInterval: 15_000 });
  const metrics = useQuery({ queryKey: ['ai-workflows-metrics'], queryFn: () => managementApi.aiWorkflowsMetrics(), refetchInterval: 30_000 });
  const status = useQuery({ queryKey: ['ai-workflows-status'], queryFn: () => managementApi.aiWorkflowsStatus(), refetchInterval: 10_000 });

  const active = (status.data?.active as ActiveExecution[]) || [];
  const metricsMap = metrics.data?.workflows as Record<string, { success_rate: number; avg_latency_ms: number; avg_cost_usd: number; executions: number }> | undefined;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">AI Workflows</h1>
      <p className="mb-6 text-sm text-[var(--color-muted)]">
        Reusable cognitive pipelines composed from AI Skills. Plugins invoke workflows instead of orchestrating skills manually.
      </p>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card title="Registered Workflows">
          {list.isLoading && <Spinner />}
          {list.data && <p className="text-2xl font-bold">{list.data.workflows?.length || 0}</p>}
        </Card>
        <Card title="Running Now">
          <p className="text-2xl font-bold">{active.length}</p>
        </Card>
        <Card title="Total Executions">
          {metrics.data && <p className="text-2xl font-bold">{metrics.data.total_executions || 0}</p>}
        </Card>
        <Card title="Avg Success Rate">
          {metrics.data && (
            <p className="text-2xl font-bold">
              {(() => {
                const wfs = Object.values(metricsMap || {});
                if (!wfs.length) return '—';
                const avg = wfs.reduce((a, w) => a + (w.success_rate || 0), 0) / wfs.length;
                return `${(avg * 100).toFixed(0)}%`;
              })()}
            </p>
          )}
        </Card>
      </div>

      {active.length > 0 && (
        <Card title="Running Workflows" className="mb-6">
          <div className="space-y-2">
            {active.map((ex) => (
              <div key={ex.execution_id} className="flex items-center justify-between rounded border border-[var(--color-border)] p-3">
                <div>
                  <div className="font-medium">{ex.workflow_id}</div>
                  <div className="text-xs text-[var(--color-muted)]">{ex.execution_id}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="warning">{ex.status}</Badge>
                  <span className="text-xs">step: {ex.current_step || '—'}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Registered Workflows">
          {list.isLoading && <Spinner />}
          <div className="space-y-3">
            {((list.data?.workflows as WorkflowRecord[]) || []).map((wf) => {
              const m = metricsMap?.[wf.workflow_id];
              return (
                <div key={wf.workflow_id} className="rounded border border-[var(--color-border)] p-4">
                  <div className="font-medium">{wf.name}</div>
                  <div className="text-xs text-[var(--color-muted)]">
                    {wf.workflow_id} · v{wf.version} · {wf.category}
                  </div>
                  {wf.description && <p className="mt-1 text-sm text-[var(--color-muted)]">{wf.description}</p>}
                  {m && (
                    <div className="mt-2 flex gap-3 text-xs text-[var(--color-muted)]">
                      <span>{m.executions} runs</span>
                      <span>{m.avg_latency_ms?.toFixed(0)}ms</span>
                      <span>${Number(m.avg_cost_usd || 0).toFixed(4)}</span>
                      <span>{((m.success_rate || 0) * 100).toFixed(0)}% ok</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        <Card title="Execution History">
          {history.isLoading && <Spinner />}
          <div className="space-y-2">
            {((history.data?.history as HistoryEntry[]) || []).slice(0, 20).map((h) => (
              <div key={h.execution_id} className="flex items-center justify-between rounded border border-[var(--color-border)] p-3 text-sm">
                <div>
                  <div className="font-medium">{h.workflow_id}</div>
                  <div className="text-xs text-[var(--color-muted)]">{h.timestamp}</div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={h.status === 'completed' ? 'success' : h.status === 'failed' ? 'danger' : 'warning'}>
                    {h.status}
                  </Badge>
                  <span className="text-xs">{h.latency_ms?.toFixed(0)}ms</span>
                  <span className="text-xs">${Number(h.cost_usd || 0).toFixed(4)}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
