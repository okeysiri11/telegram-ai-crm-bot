export interface AIProviderInfo {
  provider_id: string;
  name: string;
  enabled: boolean;
  status: string;
  latency_ms: number;
  models: string[];
}

export interface AIModelInfo {
  provider_id: string;
  model_id: string;
  display_name: string;
  context_window: number;
  status: string;
}

export interface AICostSummary {
  total_usd: number;
  threshold_usd: number;
  threshold_exceeded: boolean;
  request_count: number;
  tokens_in: number;
  tokens_out: number;
  by_provider: Record<string, number>;
  by_model: Record<string, number>;
  by_plugin: Record<string, number>;
}
