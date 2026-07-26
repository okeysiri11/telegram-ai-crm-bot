/**
 * Shared UI inventory — Sprint 30.5.
 * Documents and exposes existing EDS/UI primitives — does not recreate them.
 */

export const SHARED_UI = {
  buttons: ["Button"],
  forms: ["Input", "Select", "Checkbox", "Switch", "Radio", "DatePicker"],
  tables: ["Table", "DataGrid", "Pagination"],
  cards: ["Card", "Badge", "Avatar"],
  dialogs: ["Modal", "Dialog", "Drawer"],
  notifications: ["NotificationsPanel"],
  charts: ["Charts"],
  widgets: ["Card", "Badge"],
  loaders: ["LoadingScreen", "Skeleton", "WidgetLoading"],
  errorPages: ["ErrorBoundary", "AccessDeniedPage", "ErrorPage"],
  emptyStates: ["EmptyState", "ExperienceState", "SuccessState"],
  permissions: ["PermissionGuard", "ProtectedRoute"],
} as const;

export function sharedUiChecklist(): { group: string; components: string[] }[] {
  return Object.entries(SHARED_UI).map(([group, components]) => ({
    group,
    components: [...components],
  }));
}
