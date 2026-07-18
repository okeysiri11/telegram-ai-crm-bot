import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { useAuthStore } from '../stores/authStore';

describe('routing', () => {
  it('shows login page when logged out', () => {
    useAuthStore.setState({ isLoggedIn: false, roles: [], actorTelegramId: null });
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Platform Operations Center/i)).toBeInTheDocument();
  });

  it('protected route redirects when logged out', () => {
    useAuthStore.setState({ isLoggedIn: false, roles: [], actorTelegramId: null });
    render(
      <MemoryRouter initialEntries={['/']}>
        <ProtectedRoute>
          <div>Secret</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );
    expect(screen.queryByText('Secret')).not.toBeInTheDocument();
  });

  it('protected route renders children when logged in', () => {
    useAuthStore.setState({ isLoggedIn: true, roles: ['owner'], actorTelegramId: 1 });
    render(
      <MemoryRouter>
        <ProtectedRoute>
          <div>Secret</div>
        </ProtectedRoute>
      </MemoryRouter>,
    );
    expect(screen.getByText('Secret')).toBeInTheDocument();
  });
});
