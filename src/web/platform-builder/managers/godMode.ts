export const GOD_CAPABILITIES = [
  "edit_any_object",
  "edit_any_vertical",
  "edit_any_application",
  "edit_any_ai",
  "edit_any_organization",
  "edit_any_workflow",
  "edit_any_knowledge_base",
  "edit_any_dashboard",
  "edit_any_automation",
  "edit_any_api",
  "edit_any_template",
  "edit_any_builder",
  "system_diagnostics",
  "architecture_management",
  "developer_console",
  "version_history",
  "rollback_manager",
] as const;

export const CONTROL_CENTER_SURFACES = [
  "platform_control_center",
  "global_search",
  "object_inspector",
  "live_object_editor",
  "global_registry",
  "system_health",
  "platform_diagnostics",
  "architecture_explorer",
  "audit_center",
  "explain_mode",
] as const;

export const OWNER_HEADERS = {
  "Content-Type": "application/json",
  "X-Platform-Роль": "platform_owner",
} as const;
