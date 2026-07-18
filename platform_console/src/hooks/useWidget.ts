import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { managementApi } from '../services/management';
import { realtimeClient } from '../services/realtime';
import { apiWidgetId } from '../widgets/registry';
import type { WidgetPayload } from '../types/api';

export function useDashboard(refresh = false) {
  return useQuery({
    queryKey: ['dashboard', refresh],
    queryFn: () => managementApi.dashboard(refresh),
    refetchInterval: 60_000,
  });
}

export function useWidget(widgetId: string) {
  const queryClient = useQueryClient();
  const apiId = apiWidgetId(widgetId);

  const query = useQuery({
    queryKey: ['widget', apiId],
    queryFn: () => managementApi.widget(apiId),
    staleTime: 10_000,
  });

  useEffect(() => {
    return realtimeClient.onMessage((msg) => {
      if (msg.type !== 'event') return;
      const widgets = msg.data?.widgets as Record<string, WidgetPayload> | undefined;
      if (widgets?.[apiId]) {
        queryClient.setQueryData(['widget', apiId], widgets[apiId]);
      } else if (msg.widget_id === apiId && msg.data) {
        queryClient.invalidateQueries({ queryKey: ['widget', apiId] });
      }
    });
  }, [apiId, queryClient]);

  return query;
}

export function useManagementResource<T>(
  key: string,
  fetcher: () => Promise<T>,
  enabled = true,
) {
  return useQuery({ queryKey: [key], queryFn: fetcher, enabled });
}
