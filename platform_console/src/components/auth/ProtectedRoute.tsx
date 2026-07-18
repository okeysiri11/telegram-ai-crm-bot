import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

interface ProtectedRouteProps {
  children: ReactNode;
  minRole?: 'readonly' | 'administrator' | 'owner';
}

export function ProtectedRoute({ children, minRole }: ProtectedRouteProps) {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn);
  const hasRole = useAuthStore((s) => s.hasRole);

  if (!isLoggedIn) {
    return <Navigate to="/login" replace />;
  }

  if (minRole && !hasRole(minRole)) {
    return <Navigate to="/" replace />;
  }

  return children;
}
