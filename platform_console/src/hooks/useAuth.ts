import { useEffect } from 'react';
import { useAuthStore } from '../stores/authStore';

const REFRESH_INTERVAL_MS = 10 * 60 * 1000;

export function useAuthRefresh(): void {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const refreshToken = useAuthStore((s) => s.refreshToken);

  useEffect(() => {
    if (!isLoggedIn) return;
    const timer = setInterval(() => {
      refreshToken().catch(() => undefined);
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [isLoggedIn, refreshToken]);
}
