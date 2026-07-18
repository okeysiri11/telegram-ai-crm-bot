import { useQuery } from '@tanstack/react-query';
import { managementApi } from '../services/management';
import { Card, Badge, Spinner } from '../components/ui/Card';

interface MemoryStats {
  memory?: { total: number; by_type: Record<string, number> };
  knowledge?: { documents: number; content_bytes: number; index: { total_chunks: number; documents_indexed: number } };
  embeddings?: { provider_id: string; dimensions: number }[];
  last_search_latency_ms?: number;
}

export function AiMemoryPage() {
  const stats = useQuery({ queryKey: ['ai-memory-stats'], queryFn: () => managementApi.aiMemoryStatistics(), refetchInterval: 30_000 });
  const search = useQuery({
    queryKey: ['ai-memory-search'],
    queryFn: () => managementApi.aiMemorySearch('conversation'),
    refetchInterval: 60_000,
  });

  const data = stats.data?.statistics as MemoryStats | undefined;

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">AI Memory</h1>
      <p className="mb-6 text-sm text-[var(--color-muted)]">
        Centralized persistent memory for AI Skills, Workflows, and Agents. No module implements its own memory.
      </p>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card title="Memory Entries">
          {stats.isLoading && <Spinner />}
          {data && <p className="text-2xl font-bold">{data.memory?.total || 0}</p>}
        </Card>
        <Card title="Knowledge Docs">
          {data && <p className="text-2xl font-bold">{data.knowledge?.documents || 0}</p>}
        </Card>
        <Card title="Indexed Chunks">
          {data && <p className="text-2xl font-bold">{data.knowledge?.index?.total_chunks || 0}</p>}
        </Card>
        <Card title="Search Latency">
          {data && <p className="text-2xl font-bold">{data.last_search_latency_ms?.toFixed(1) || 0}ms</p>}
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Memory by Type">
          {data?.memory?.by_type && (
            <div className="space-y-2">
              {Object.entries(data.memory.by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between rounded border border-[var(--color-border)] p-3">
                  <span className="font-medium">{type}</span>
                  <Badge>{count}</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="Embedding Providers">
          <div className="space-y-2">
            {(data?.embeddings || []).map((p) => (
              <div key={p.provider_id} className="flex items-center justify-between rounded border border-[var(--color-border)] p-3">
                <span className="font-medium">{p.provider_id}</span>
                <span className="text-xs text-[var(--color-muted)]">{p.dimensions} dims</span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Recent Search Results" className="lg:col-span-2">
          {search.isLoading && <Spinner />}
          <div className="space-y-2">
            {((search.data?.results as { content: string; score: number; source_type: string }[]) || []).slice(0, 5).map((r, i) => (
              <div key={i} className="rounded border border-[var(--color-border)] p-3 text-sm">
                <div className="mb-1 flex gap-2">
                  <Badge variant={r.source_type === 'knowledge' ? 'success' : 'default'}>{r.source_type}</Badge>
                  <span className="text-xs text-[var(--color-muted)]">score: {r.score}</span>
                </div>
                <p className="line-clamp-2">{r.content}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
