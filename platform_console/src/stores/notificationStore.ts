import { create } from 'zustand';
import type { RealtimeMessage } from '../types/api';

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'critical';
  timestamp: string;
  read: boolean;
}

interface NotificationState {
  items: NotificationItem[];
  unreadCount: number;
  addFromRealtime: (msg: RealtimeMessage) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clear: () => void;
}

let counter = 0;

export const useNotificationStore = create<NotificationState>((set) => ({
  items: [],
  unreadCount: 0,

  addFromRealtime: (msg) => {
    if (msg.type !== 'event') return;
    const item: NotificationItem = {
      id: `n-${++counter}`,
      title: msg.event || 'Event',
      message: JSON.stringify(msg.data ?? {}).slice(0, 120),
      severity: msg.channel === 'system' ? 'warning' : 'info',
      timestamp: msg.timestamp || new Date().toISOString(),
      read: false,
    };
    set((s) => ({
      items: [item, ...s.items].slice(0, 100),
      unreadCount: s.unreadCount + 1,
    }));
  },

  markRead: (id) =>
    set((s) => ({
      items: s.items.map((i) => (i.id === id ? { ...i, read: true } : i)),
      unreadCount: Math.max(0, s.unreadCount - 1),
    })),

  markAllRead: () =>
    set((s) => ({
      items: s.items.map((i) => ({ ...i, read: true })),
      unreadCount: 0,
    })),

  clear: () => set({ items: [], unreadCount: 0 }),
}));
