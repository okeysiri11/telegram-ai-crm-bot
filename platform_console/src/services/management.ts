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

  aiSkillsList: () => apiGet<{ skills: unknown[] }>('/management/ai/skills/list'),
  aiSkillsHealth: () => apiGet<{ skills: unknown[]; total: number }>('/management/ai/skills/health'),
  aiSkillsMetrics: () => apiGet<{ total_executions: number; skills: Record<string, unknown> }>('/management/ai/skills/metrics'),
  aiSkillsExecute: (body: Record<string, unknown>) =>
    apiPost<Record<string, unknown>>('/management/ai/skills/execute', body),

  aiWorkflowsStatus: () => apiGet<{ summary: unknown; active: unknown[]; metrics: unknown }>('/management/ai/workflows'),
  aiWorkflowsList: () => apiGet<{ workflows: unknown[] }>('/management/ai/workflows/list'),
  aiWorkflowsTemplates: () => apiGet<{ templates: unknown[] }>('/management/ai/workflows/templates'),
  aiWorkflowsHistory: (limit = 50) => apiGet<{ history: unknown[] }>(`/management/ai/workflows/history?limit=${limit}`),
  aiWorkflowsMetrics: () => apiGet<{ total_executions: number; workflows: Record<string, unknown> }>('/management/ai/workflows/metrics'),
  aiWorkflowsExecute: (body: Record<string, unknown>) =>
    apiPost<Record<string, unknown>>('/management/ai/workflows/execute', body),

  aiMemoryStatistics: () => apiGet<{ statistics: Record<string, unknown> }>('/management/ai/memory/statistics'),
  aiMemorySearch: (q: string) => apiGet<{ results: unknown[]; latency_ms: number }>(`/management/ai/memory/search?q=${encodeURIComponent(q)}`),
  aiMemoryRemember: (body: Record<string, unknown>) => apiPost<Record<string, unknown>>('/management/ai/memory/remember', body),
  aiKnowledgeList: () => apiGet<{ documents: unknown[] }>('/management/ai/memory/knowledge'),
  aiKnowledgeIndex: (body: Record<string, unknown>) => apiPost<Record<string, unknown>>('/management/ai/memory/knowledge/index', body),

  migration: () => apiGet<Record<string, unknown>>('/management/migration'),
  migrationStatus: () => apiGet<Record<string, unknown>>('/management/migration/status'),
  migrationCoverage: () => apiGet<Record<string, unknown>>('/management/migration/coverage'),
  migrationDeprecated: () => apiGet<Record<string, unknown>>('/management/migration/deprecated'),
  migrationFeatureFlags: () => apiGet<Record<string, unknown>>('/management/migration/feature-flags'),
  migrationHealth: () => apiGet<Record<string, unknown>>('/management/migration/health'),
};
