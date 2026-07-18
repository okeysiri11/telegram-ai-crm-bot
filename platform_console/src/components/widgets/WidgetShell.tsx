import { useWidget } from '../../hooks/useWidget';
import { getWidgetDef } from '../../widgets/registry';
import { Card, Spinner, Badge } from '../ui/Card';
import { formatRelativeTime } from '../../utils/format';
import { WidgetChart } from './WidgetChart';

interface WidgetShellProps {
  widgetId: string;
}

export function WidgetShell({ widgetId }: WidgetShellProps) {
  const def = getWidgetDef(widgetId);
  const { data, isLoading, isError, refetch, isFetching } = useWidget(widgetId);

  return (
    <Card
      title={def?.title || widgetId}
      actions={
        <div className="flex items-center gap-2">
          {data?.meta?.cache_hit && <Badge>cached</Badge>}
          {isFetching && <Badge variant="warning">updating</Badge>}
          <button
            type="button"
            onClick={() => refetch()}
            className="text-xs text-[var(--color-accent)] hover:underline"
          >
            Refresh
          </button>
        </div>
      }
      className="h-full"
    >
      {isLoading && <Spinner />}
      {isError && <p className="text-sm text-red-500">Failed to load widget</p>}
      {data && (
        <>
          <WidgetBody widgetId={widgetId} data={data.data} />
          <p className="mt-2 text-xs text-[var(--color-muted)]">
            Updated {formatRelativeTime(data.meta.updated_at)}
          </p>
        </>
      )}
    </Card>
  );
}

function WidgetBody({ widgetId, data }: { widgetId: string; data: Record<string, unknown> }) {
  const chartWidgets = [
    'top_kpis',
    'manager_load',
    'requests_by_vertical',
    'observability_performance',
    'job_execution_rate',
  ];
  if (chartWidgets.includes(widgetId)) {
    const chartType =
      widgetId.includes('rate') || widgetId.includes('performance') ? 'line' : 'bar';
    return <WidgetChart type={chartType} data={data} />;
  }

  const status = data.overall_status || data.status;
  if (status) {
    return (
      <div className="space-y-2">
        <Badge variant={String(status) === 'healthy' ? 'success' : 'warning'}>
          {String(status)}
        </Badge>
        <pre className="max-h-36 overflow-auto text-xs whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    );
  }

  return (
    <pre className="max-h-48 overflow-auto text-xs whitespace-pre-wrap">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
