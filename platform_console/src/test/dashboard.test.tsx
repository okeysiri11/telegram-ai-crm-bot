import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '../pages/DashboardPage';

vi.mock('../services/management', () => ({
  managementApi: {
    widget: vi.fn(async (id: string) => ({
      meta: { widget_id: id, updated_at: new Date().toISOString(), refresh_interval: 30, status: 'ok' },
      data: { status: 'healthy' },
    })),
  },
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders widget grid title', () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <DashboardPage />
      </QueryClientProvider>,
    );
    expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
  });
});
