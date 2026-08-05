/**
 * Sprint 27.3 / 27.4 — Workspace session types (open tabs / active workspace / closed stack).
 */

export type WorkspaceTab = {
  id: string;
  title: string;
  path: string;
  moduleId?: string;
  pinned: boolean;
  openedAt: string;
};

export type WorkspaceSessionSnapshot = {
  /** v1 = tabs only; v2 adds closedTabs for reopen. */
  version: 1 | 2;
  activeWorkspaceId: string;
  activeTabId: string | null;
  tabs: WorkspaceTab[];
  closedTabs?: WorkspaceTab[];
  updatedAt: string;
};

export const WORKSPACE_SESSION_KEY = "ews_workspace_session_v1";
export const ACTIVITY_JOURNAL_KEY = "ews_activity_journal_v1";
export const MAX_CLOSED_TABS = 20;
