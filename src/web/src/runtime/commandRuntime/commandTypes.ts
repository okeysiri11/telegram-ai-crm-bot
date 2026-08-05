/**
 * Command Runtime types — Sprint 28.6 / 28.7.
 */

export const COMMAND_RUNTIME_VERSION = "28.7";

export type CommandRole =
  | "admin"
  | "developer"
  | "manager"
  | "operator"
  | "client"
  | "guest";

export type CommandKind =
  | "open_module"
  | "open_desktop_window"
  | "navigate"
  | "focus_window"
  | "close_window"
  | "minimize_window"
  | "maximize_window"
  | "launch_ai_studio"
  | "launch_production"
  | "launch_city"
  | "launch_dashboard"
  | "search"
  | "quick_action"
  | "run_workflow"
  | "run_agent"
  | "show_notification"
  | "workspace"
  | "system"
  | "macro"
  | "undo"
  | "redo";

export type CommandArgs = Record<string, unknown>;

export type PolicyScope =
  | "user"
  | "organization"
  | "workspace"
  | "device"
  | "remote_session";

export type CommandPolicyContext = {
  scope: PolicyScope;
  userId: string | null;
  organizationId: string | null;
  workspaceId: string | null;
  deviceId: string | null;
  remoteSessionId: string | null;
  tenantId: string | null;
};

export type CommandDefinition = {
  id: string;
  action: string;
  label: string;
  kind: CommandKind;
  keywords: string[];
  route?: string;
  permission?: string;
  minRole?: CommandRole;
  notifyOnSuccess?: boolean;
  policyScopes?: PolicyScope[];
  handler?: (
    ctx: CommandExecutionContext,
    args: CommandArgs,
  ) => CommandHandlerResult | Promise<CommandHandlerResult>;
};

export type CommandExecutionContext = {
  role: CommandRole;
  roles: string[];
  permissions: string[];
  userId: string | null;
  path: string;
  moduleId: string | null;
  surface: "desktop" | "shell" | "palette" | "system";
  navigate: (path: string) => void;
  args: CommandArgs;
  policy?: CommandPolicyContext;
};

export type CommandHandlerResult = {
  ok: boolean;
  route?: string;
  message?: string;
  error?: string;
  cancelled?: boolean;
  data?: Record<string, unknown>;
};

export type CommandResult = CommandHandlerResult & {
  id: string;
  action: string;
  label: string;
  durationMs: number;
};

export type CommandHistoryEntry = {
  id: string;
  commandId: string;
  action: string;
  label: string;
  ok: boolean;
  at: string;
  route?: string;
  error?: string;
};

export type CommandEventName =
  | "command.started"
  | "command.completed"
  | "command.failed"
  | "command.cancelled";

export type UndoableCommand = {
  id: string;
  commandId: string;
  action: string;
  label: string;
  args: CommandArgs;
  previousPath: string;
  route?: string;
  kind: CommandKind;
  at: string;
  groupId?: string;
  transactionId?: string;
};

export type CommandMacroStep = {
  commandId: string;
  action: string;
  args?: CommandArgs;
};

export type CommandMacro = {
  id: string;
  name: string;
  steps: CommandMacroStep[];
  favorite: boolean;
  createdAt: string;
  updatedAt: string;
};

export type CommandAnalyticsSnapshot = {
  executionCount: number;
  successRate: number;
  failures: number;
  avgDurationMs: number;
  usage: Record<string, number>;
  favorites: string[];
  aiUsage: number;
  popular: { id: string; count: number }[];
  errors: { id: string; error: string; at: string }[];
};
