import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { managementApi } from '../services/management';
import { Card, Badge, Spinner } from '../components/ui/Card';
import type { PluginRecord } from '../types/plugins';

export function PluginsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['plugins'],
    queryFn: () => managementApi.plugins(),
    refetchInterval: 30_000,
  });

  const deps = useQuery({
    queryKey: ['plugins-dependencies'],
    queryFn: () => managementApi.pluginDependencies(),
  });

  const health = useQuery({
    queryKey: ['plugins-health'],
    queryFn: () => managementApi.pluginHealth(),
  });

  const action = useMutation({
    mutationFn: async ({
      id,
      op,
    }: {
      id: string;
      op: 'install' | 'enable' | 'disable' | 'reload' | 'uninstall';
    }): Promise<PluginRecord | Record<string, unknown>> => {
      switch (op) {
        case 'install':
          return managementApi.pluginInstall(id);
        case 'enable':
          return managementApi.pluginEnable(id);
        case 'disable':
          return managementApi.pluginDisable(id);
        case 'reload':
          return managementApi.pluginReload(id);
        case 'uninstall':
          return managementApi.pluginUninstall(id);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plugins'] });
      queryClient.invalidateQueries({ queryKey: ['plugins-health'] });
    },
  });

  const plugins = (data?.plugins || data?.installed || []) as PluginRecord[];

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Plugins</h1>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm"
        >
          Refresh
        </button>
      </div>

      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card title="Summary">
          {isLoading && <Spinner />}
          {data?.count && (
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <dt>Discovered</dt>
              <dd>{data.count.discovered}</dd>
              <dt>Installed</dt>
              <dd>{data.count.installed}</dd>
              <dt>Enabled</dt>
              <dd>{data.count.enabled}</dd>
              <dt>Failed</dt>
              <dd>{data.count.failed}</dd>
            </dl>
          )}
        </Card>
        <Card title="Dependencies">
          {deps.isLoading && <Spinner />}
          {deps.data && (
            <p className="text-sm">
              Graph valid:{' '}
              <Badge variant={deps.data.valid ? 'success' : 'danger'}>
                {deps.data.valid ? 'yes' : 'no'}
              </Badge>
              <span className="ml-2 text-[var(--color-muted)]">
                {deps.data.edges?.length || 0} edges
              </span>
            </p>
          )}
        </Card>
        <Card title="Health">
          {health.isLoading && <Spinner />}
          {health.data && (
            <p className="text-sm">
              Overall:{' '}
              <Badge variant={health.data.overall === 'healthy' ? 'success' : 'warning'}>
                {String(health.data.overall)}
              </Badge>
              <span className="ml-2 text-[var(--color-muted)]">
                {Number(health.data.healthy)}/{Number(health.data.total)} healthy
              </span>
            </p>
          )}
        </Card>
      </div>

      {isError && <p className="text-red-500">Failed to load plugins</p>}

      <div className="space-y-4">
        {plugins.map((plugin) => (
          <Card key={plugin.id} title={`${plugin.name} (${plugin.id})`}>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Badge>{plugin.state}</Badge>
              <Badge variant="default">v{plugin.version}</Badge>
              {plugin.health && (
                <Badge variant={plugin.health.status === 'healthy' ? 'success' : 'warning'}>
                  {plugin.health.status}
                </Badge>
              )}
            </div>
            <p className="mb-3 text-sm text-[var(--color-muted)]">{plugin.description}</p>
            <div className="mb-3 text-xs text-[var(--color-muted)]">
              <div>Author: {plugin.author}</div>
              <div>Workflows: {(plugin.workflows || []).join(', ') || '—'}</div>
              <div>
                Dependencies:{' '}
                {JSON.stringify(plugin.dependencies?.required || []) || 'none'}
              </div>
            </div>
            {plugin.logs && plugin.logs.length > 0 && (
              <pre className="mb-3 max-h-24 overflow-auto rounded bg-slate-100 p-2 text-xs dark:bg-slate-800">
                {plugin.logs.join('\n')}
              </pre>
            )}
            <div className="flex flex-wrap gap-2">
              {plugin.state === 'discovered' && (
                <ActionButton label="Install" onClick={() => action.mutate({ id: plugin.id, op: 'install' })} />
              )}
              {(plugin.state === 'installed' || plugin.state === 'disabled' || plugin.state === 'failed') && (
                <ActionButton label="Enable" onClick={() => action.mutate({ id: plugin.id, op: 'enable' })} />
              )}
              {plugin.state === 'enabled' && (
                <>
                  <ActionButton label="Disable" onClick={() => action.mutate({ id: plugin.id, op: 'disable' })} />
                  <ActionButton label="Reload" onClick={() => action.mutate({ id: plugin.id, op: 'reload' })} />
                </>
              )}
              {plugin.state !== 'discovered' && plugin.state !== 'uninstalled' && (
                <ActionButton label="Uninstall" onClick={() => action.mutate({ id: plugin.id, op: 'uninstall' })} />
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ActionButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded border border-[var(--color-border)] px-3 py-1 text-xs hover:bg-slate-100 dark:hover:bg-slate-800"
    >
      {label}
    </button>
  );
}
