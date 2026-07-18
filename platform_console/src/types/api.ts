export interface ManagementResponse<T = unknown> {
  success: boolean;
  timestamp: string;
  request_id: string;
  data: T;
  errors: string[];
}

export interface WidgetMeta {
  widget_id: string;
  updated_at: string;
  refresh_interval: number;
  status: string;
  cache_hit?: boolean;
  duration_ms?: number;
}

export interface WidgetPayload {
  meta: WidgetMeta;
  data: Record<string, unknown>;
}

export interface DashboardPayload {
  generated_at: string;
  widgets: Record<string, WidgetPayload>;
  duration_ms?: number;
  cache_hit?: boolean;
}

export interface RealtimeMessage {
  type: string;
  channel?: string;
  event?: string;
  widget_id?: string;
  timestamp?: string;
  data?: Record<string, unknown>;
}

export type UserRole = 'owner' | 'administrator' | 'readonly' | 'manager' | 'operator';
