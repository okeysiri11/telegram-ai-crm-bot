/**
 * Sprint 27.1 — Bottom status bar probes.
 * Soft health checks; UI stays green/amber/grey when APIs are offline.
 */

import { webConfig } from "@/config/webConfig";

export type StatusTone = "ok" | "warn" | "err" | "unknown";

export type StatusItemId =
  | "runtime"
  | "api"
  | "database"
  | "providers"
  | "voice"
  | "mcp"
  | "queue"
  | "build"
  | "version";

export type StatusProbe = {
  id: StatusItemId;
  label: string;
  /** Relative URL; empty = static / local-only indicator. */
  healthUrl?: string;
  staticTone?: StatusTone;
  staticDetail?: string;
};

export const STATUS_PROBES: StatusProbe[] = [
  { id: "runtime", label: "Runtime", healthUrl: "/api/enterprise-obs/v1/health" },
  { id: "api", label: "API", healthUrl: "/api/enterprise-hub/v1/health" },
  { id: "database", label: "Database", healthUrl: "/api/enterprise-obs/v1/health" },
  { id: "providers", label: "Providers", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  { id: "voice", label: "Voice", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  { id: "mcp", label: "MCP", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  { id: "queue", label: "Queue", healthUrl: "/api/platform-builder/v1/mission-control/status" },
  {
    id: "build",
    label: "Build",
    staticTone: "ok",
    staticDetail: import.meta.env.DEV ? "dev" : "production",
  },
  {
    id: "version",
    label: "Version",
    staticTone: "ok",
    staticDetail: webConfig.version,
  },
];

export type StatusSnapshot = {
  id: StatusItemId;
  label: string;
  tone: StatusTone;
  detail: string;
};
