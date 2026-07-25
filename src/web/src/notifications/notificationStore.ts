import { create } from "zustand";

export type NotificationKind =
  | "in_app"
  | "toast"
  | "alert"
  | "task"
  | "ai"
  | "workflow";

export type AppNotification = {
  id: string;
  kind: NotificationKind;
  title: string;
  body: string;
  createdAt: string;
  read: boolean;
};

type NotifState = {
  items: AppNotification[];
  push: (n: Omit<AppNotification, "id" | "createdAt" | "read">) => void;
  markRead: (id: string) => void;
  clear: () => void;
};

export const useNotificationStore = create<NotifState>((set) => ({
  items: [
    {
      id: "n1",
      kind: "ai",
      title: "AI insight ready",
      body: "Weekly forecast available",
      createdAt: new Date().toISOString(),
      read: false,
    },
    {
      id: "n2",
      kind: "workflow",
      title: "Approval pending",
      body: "Invoice workflow awaits owner",
      createdAt: new Date().toISOString(),
      read: false,
    },
  ],
  push: (n) =>
    set((s) => ({
      items: [
        {
          ...n,
          id: `n_${Math.random().toString(36).slice(2, 9)}`,
          createdAt: new Date().toISOString(),
          read: false,
        },
        ...s.items,
      ],
    })),
  markRead: (id) =>
    set((s) => ({
      items: s.items.map((i) => (i.id === id ? { ...i, read: true } : i)),
    })),
  clear: () => set({ items: [] }),
}));
