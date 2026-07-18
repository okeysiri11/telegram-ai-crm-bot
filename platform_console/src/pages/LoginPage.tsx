import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Card } from '../components/ui/Card';

export function LoginPage() {
  const [telegramId, setTelegramId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);

  if (isLoggedIn) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(Number(telegramId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--color-surface)] p-4">
      <Card title="Platform Operations Center" className="w-full max-w-md">
        <p className="mb-4 text-sm text-[var(--color-muted)]">
          Sign in with your Telegram ID via the Platform Identity service.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm">
            Telegram ID
            <input
              type="number"
              required
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              className="mt-1 w-full rounded-lg border border-[var(--color-border)] bg-transparent px-3 py-2"
              placeholder="123456789"
            />
          </label>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-[var(--color-accent)] px-4 py-2 text-white disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </Card>
    </div>
  );
}
