import { useQuery } from '@tanstack/react-query';
import { managementApi } from '../services/management';
import { Card, Badge, Spinner } from '../components/ui/Card';

interface SkillRecord {
  skill_id: string;
  name: string;
  version: string;
  category: string;
  state: string;
  enabled: boolean;
  tags?: string[];
}

interface SkillHealthEntry {
  skill_id: string;
  status: string;
  state?: string;
  metrics?: {
    executions: number;
    success_rate: number;
    avg_latency_ms: number;
    avg_cost_usd: number;
    failures: number;
  };
}

export function AiSkillsPage() {
  const list = useQuery({ queryKey: ['ai-skills-list'], queryFn: () => managementApi.aiSkillsList(), refetchInterval: 30_000 });
  const health = useQuery({ queryKey: ['ai-skills-health'], queryFn: () => managementApi.aiSkillsHealth(), refetchInterval: 30_000 });
  const metrics = useQuery({ queryKey: ['ai-skills-metrics'], queryFn: () => managementApi.aiSkillsMetrics(), refetchInterval: 30_000 });

  const healthMap = new Map<string, SkillHealthEntry>(
    ((health.data?.skills as SkillHealthEntry[]) || []).map((s) => [s.skill_id, s]),
  );
  const metricsMap = new Map<string, SkillHealthEntry['metrics']>(
    Object.entries(metrics.data?.skills || {}).map(([id, m]) => [id, m as SkillHealthEntry['metrics']]),
  );

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">AI Skills</h1>
      <p className="mb-6 text-sm text-[var(--color-muted)]">
        Reusable business capabilities powered by AI. Plugins invoke skills — not LLM providers directly.
      </p>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card title="Installed Skills">
          {list.isLoading && <Spinner />}
          {list.data && <p className="text-2xl font-bold">{list.data.skills?.length || 0}</p>}
        </Card>
        <Card title="Healthy">
          {health.data && (
            <p className="text-2xl font-bold">
              {(health.data.skills as SkillHealthEntry[])?.filter((s) => s.status === 'healthy').length || 0}
            </p>
          )}
        </Card>
        <Card title="Total Executions">
          {metrics.data && <p className="text-2xl font-bold">{metrics.data.total_executions || 0}</p>}
        </Card>
        <Card title="Avg Success Rate">
          {metrics.data && (
            <p className="text-2xl font-bold">
              {(() => {
                const skills = Object.values(metrics.data.skills || {}) as NonNullable<SkillHealthEntry['metrics']>[];
                if (!skills.length) return '—';
                const avg = skills.reduce((a, s) => a + (s?.success_rate || 0), 0) / skills.length;
                return `${(avg * 100).toFixed(0)}%`;
              })()}
            </p>
          )}
        </Card>
      </div>

      <Card title="Installed Skills">
        {list.isLoading && <Spinner />}
        <div className="space-y-3">
          {((list.data?.skills as SkillRecord[]) || []).map((skill) => {
            const h = healthMap.get(skill.skill_id);
            const m = metricsMap.get(skill.skill_id);
            return (
              <div
                key={skill.skill_id}
                className="flex flex-col gap-2 rounded border border-[var(--color-border)] p-4 md:flex-row md:items-center md:justify-between"
              >
                <div>
                  <div className="font-medium">{skill.name}</div>
                  <div className="text-xs text-[var(--color-muted)]">
                    {skill.skill_id} · v{skill.version} · {skill.category}
                  </div>
                  {skill.tags && skill.tags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {skill.tags.map((tag) => (
                        <span key={tag} className="rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-3 text-sm">
                  <Badge variant={h?.status === 'healthy' ? 'success' : 'warning'}>{h?.status || skill.state}</Badge>
                  {m && (
                    <>
                      <span>{m.avg_latency_ms?.toFixed(0) || 0}ms</span>
                      <span>{m.executions || 0} runs</span>
                      <span>${Number(m.avg_cost_usd || 0).toFixed(4)}</span>
                      <span>{((m.success_rate || 0) * 100).toFixed(0)}% ok</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
