import { apiGet } from './api';
import type { DashboardPayload, WidgetPayload } from '../types/api';

export const managementApi = {
  dashboard: (refresh = false) =>
    apiGet<DashboardPayload>(`/management/dashboard${refresh ? '?refresh=true' : ''}`),

  widget: (widgetId: string, noCache = false) =>
    apiGet<WidgetPayload>(
      `/management/dashboard/widgets/${widgetId}${noCache ? '?no_cache=true' : ''}`,
    ),

  system: () => apiGet<Record<string, unknown>>('/management/system'),
  health: () => apiGet<Record<string, unknown>>('/management/health'),
  requests: () => apiGet<Record<string, unknown>>('/management/requests'),
  managers: () => apiGet<Record<string, unknown>>('/management/managers'),
  workflows: () => apiGet<Record<string, unknown>>('/management/workflows'),
  configuration: () => apiGet<Record<string, unknown>>('/management/configuration'),
  audit: (limit = 50) => apiGet<Record<string, unknown>>(`/management/audit?limit=${limit}`),
  jobs: () => apiGet<Record<string, unknown>>('/management/jobs'),
  integrations: () => apiGet<Record<string, unknown>>('/management/integrations'),
  observability: () => apiGet<Record<string, unknown>>('/management/observability'),
  kpi: () => apiGet<Record<string, unknown>>('/management/kpi'),
  realtime: () => apiGet<Record<string, unknown>>('/management/realtime'),
};
