import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  language: string;
  timezone: string;
  setTheme: (theme: Theme) => void;
  setLanguage: (lang: string) => void;
  setTimezone: (tz: string) => void;
  resolvedTheme: () => 'light' | 'dark';
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      language: 'en',
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,

      setTheme: (theme) => {
        set({ theme });
        applyTheme(get().resolvedTheme());
      },

      setLanguage: (language) => set({ language }),
      setTimezone: (timezone) => set({ timezone }),

      resolvedTheme: () => {
        const t = get().theme;
        if (t === 'system') {
          return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        return t;
      },
    }),
    { name: 'platform-settings' },
  ),
);

export function applyTheme(theme: 'light' | 'dark'): void {
  document.documentElement.classList.toggle('dark', theme === 'dark');
}

export function initTheme(): void {
  applyTheme(useThemeStore.getState().resolvedTheme());
}
