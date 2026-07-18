import { useQuery } from '@tanstack/react-query';
import { Card, Spinner } from '../components/ui/Card';

interface ManagementPageProps {
  title: string;
  queryKey: string;
  fetcher: () => Promise<Record<string, unknown>>;
}

export function ManagementPage({ title, queryKey, fetcher }: ManagementPageProps) {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [queryKey],
    queryFn: fetcher,
    refetchInterval: 30_000,
  });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">{title}</h1>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm"
        >
          Refresh
        </button>
      </div>
      <Card>
        {isLoading && <Spinner />}
        {isError && <p className="text-red-500">Failed to load {title.toLowerCase()}</p>}
        {data && (
          <pre className="max-h-[70vh] overflow-auto text-xs whitespace-pre-wrap">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </Card>
    </div>
  );
}
