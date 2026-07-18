import { describe, it, expect, beforeEach } from 'vitest';
import { useAuthStore } from '../stores/authStore';

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ isLoggedIn: false, roles: [], actorTelegramId: null });
  });

  it('hasRole respects role hierarchy', () => {
    useAuthStore.setState({ roles: ['administrator'] });
    expect(useAuthStore.getState().hasRole('readonly')).toBe(true);
    expect(useAuthStore.getState().hasRole('administrator')).toBe(true);
    expect(useAuthStore.getState().hasRole('owner')).toBe(false);
  });

  it('logout clears session state', () => {
    useAuthStore.setState({ isLoggedIn: true, roles: ['owner'], actorTelegramId: 1 });
    localStorage.setItem('access_token', 'x');
    useAuthStore.getState().logout();
    expect(useAuthStore.getState().isLoggedIn).toBe(false);
    expect(localStorage.getItem('access_token')).toBeNull();
  });
});
