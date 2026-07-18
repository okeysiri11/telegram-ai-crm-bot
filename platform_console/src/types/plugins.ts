export interface PluginHealth {
  plugin_id: string;
  status: string;
  message?: string;
  checked_at?: string;
}

export interface PluginRecord {
  id: string;
  name: string;
  version: string;
  author: string;
  description: string;
  state: string;
  permissions?: string[];
  workflows?: string[];
  dependencies?: { required?: Array<{ id: string; version?: string }>; optional?: Array<{ id: string; version?: string }> };
  health?: PluginHealth;
  logs?: string[];
}

export interface PluginsPayload {
  discovered: string[];
  installed: PluginRecord[];
  enabled: string[];
  disabled: string[];
  failed: string[];
  plugins?: PluginRecord[];
  count: {
    discovered: number;
    installed: number;
    enabled: number;
    disabled: number;
    failed: number;
  };
}

export interface DependencyGraph {
  nodes: Array<{ id: string; version: string; state: string }>;
  edges: Array<{ from: string; to: string; type: string }>;
  cycles: string[];
  valid: boolean;
}
