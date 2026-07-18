import { apiGet, apiPost } from './api';
import type { DashboardPayload, WidgetPayload } from '../types/api';
import type { DependencyGraph, PluginRecord, PluginsPayload } from '../types/plugins';
import type { AICostSummary, AIModelInfo, AIProviderInfo } from '../types/ai';

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

  plugins: () => apiGet<PluginsPayload>('/management/plugins'),
  plugin: (id: string) => apiGet<PluginRecord>(`/management/plugins/${id}`),
  pluginInstall: (id: string) => apiPost<PluginRecord>(`/management/plugins/${id}/install`),
  pluginEnable: (id: string) => apiPost<PluginRecord>(`/management/plugins/${id}/enable`),
  pluginDisable: (id: string) => apiPost<PluginRecord>(`/management/plugins/${id}/disable`),
  pluginReload: (id: string) => apiPost<Record<string, unknown>>(`/management/plugins/${id}/reload`),
  pluginUninstall: (id: string) => apiPost<PluginRecord>(`/management/plugins/${id}/uninstall`),
  pluginHealth: (id?: string) =>
    apiGet<Record<string, unknown>>(id ? `/management/plugins/${id}/health` : '/management/plugins/health'),
  pluginDependencies: () => apiGet<DependencyGraph>('/management/plugins/dependencies'),

  aiStatus: () => apiGet<Record<string, unknown>>('/management/ai'),
  aiProviders: () => apiGet<{ providers: AIProviderInfo[] }>('/management/ai/providers'),
  aiModels: () => apiGet<{ models: AIModelInfo[] }>('/management/ai/models'),
  aiPrompts: () => apiGet<Record<string, unknown>>('/management/ai/prompts'),
  aiStatistics: () => apiGet<{ request_count: number; cache: Record<string, unknown>; providers: unknown[] }>('/management/ai/statistics'),
  aiCosts: () => apiGet<{ summary: AICostSummary; recent: unknown[] }>('/management/ai/costs'),
  aiComplete: (body: Record<string, unknown>) => apiPost<Record<string, unknown>>('/management/ai/complete', body),
};
