/**
 * Citizen digital workspace — Sprint 29.1.
 */

import type {
  AssignedProject,
  CitizenWorkspace,
  PersonalCalendarEvent,
  PersonalTask,
  WorkspaceBookmark,
} from "./citizenTypes";

const workspaces = new Map<string, CitizenWorkspace>();

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

function empty(citizenId: string): CitizenWorkspace {
  return {
    citizenId,
    dashboardTitle: "Personal Dashboard",
    tasks: [],
    calendar: [],
    projects: [],
    documentRefs: [],
    notificationIds: [],
    bookmarks: [],
    favorites: [],
    updatedAt: new Date().toISOString(),
  };
}

export const citizenWorkspaceService = {
  clear() {
    workspaces.clear();
  },

  ensure(citizenId: string) {
    let ws = workspaces.get(citizenId);
    if (!ws) {
      ws = empty(citizenId);
      workspaces.set(citizenId, ws);
    }
    return ws;
  },

  get(citizenId: string) {
    return this.ensure(citizenId);
  },

  addTask(citizenId: string, title: string, dueAt?: string, projectId?: string): PersonalTask {
    const ws = this.ensure(citizenId);
    const task: PersonalTask = {
      id: uid("task"),
      citizenId,
      title,
      done: false,
      dueAt,
      projectId,
      createdAt: new Date().toISOString(),
    };
    const next = {
      ...ws,
      tasks: [task, ...ws.tasks],
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return task;
  },

  completeTask(citizenId: string, taskId: string) {
    const ws = this.ensure(citizenId);
    const next = {
      ...ws,
      tasks: ws.tasks.map((t) => (t.id === taskId ? { ...t, done: true } : t)),
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return next;
  },

  addCalendarEvent(
    citizenId: string,
    input: Omit<PersonalCalendarEvent, "id" | "citizenId">,
  ) {
    const ws = this.ensure(citizenId);
    const event: PersonalCalendarEvent = { id: uid("cal"), citizenId, ...input };
    const next = {
      ...ws,
      calendar: [...ws.calendar, event].sort((a, b) => a.startsAt.localeCompare(b.startsAt)),
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return event;
  },

  assignProject(citizenId: string, project: Omit<AssignedProject, "citizenId" | "joinedAt" | "id"> & { id?: string }) {
    const ws = this.ensure(citizenId);
    const entry: AssignedProject = {
      id: project.id || uid("ap"),
      citizenId,
      projectId: project.projectId,
      projectName: project.projectName,
      role: project.role,
      joinedAt: new Date().toISOString(),
    };
    const next = {
      ...ws,
      projects: [entry, ...ws.projects.filter((p) => p.projectId !== entry.projectId)],
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return entry;
  },

  addDocument(citizenId: string, documentRef: string) {
    const ws = this.ensure(citizenId);
    if (ws.documentRefs.includes(documentRef)) return ws;
    const next = {
      ...ws,
      documentRefs: [documentRef, ...ws.documentRefs],
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return next;
  },

  pushNotification(citizenId: string, notificationId: string) {
    const ws = this.ensure(citizenId);
    const next = {
      ...ws,
      notificationIds: [notificationId, ...ws.notificationIds].slice(0, 50),
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return next;
  },

  addBookmark(citizenId: string, label: string, path: string, favorite = false) {
    const ws = this.ensure(citizenId);
    const bm: WorkspaceBookmark = { id: uid("bm"), label, path, favorite };
    const favorites = favorite ? [...new Set([path, ...ws.favorites])] : ws.favorites;
    const next = {
      ...ws,
      bookmarks: [bm, ...ws.bookmarks],
      favorites,
      updatedAt: new Date().toISOString(),
    };
    workspaces.set(citizenId, next);
    return bm;
  },

  toggleFavorite(citizenId: string, path: string) {
    const ws = this.ensure(citizenId);
    const has = ws.favorites.includes(path);
    const favorites = has ? ws.favorites.filter((f) => f !== path) : [...ws.favorites, path];
    const next = { ...ws, favorites, updatedAt: new Date().toISOString() };
    workspaces.set(citizenId, next);
    return next;
  },
};
