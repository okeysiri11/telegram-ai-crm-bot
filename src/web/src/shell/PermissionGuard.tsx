/**
 * Permission-aware route guard — Sprint 30.4.
 * Reuses workspace permissions + auth role; pairs with ProtectedRoute.
 */

import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useWorkspaceStore } from "@/workspace/workspaceStore";

export function PermissionGuard({
  children,
  require,
  fallback = "/workspace",
}: {
  children: ReactNode;
  require: string[];
  fallback?: string;
}) {
  const roleId = useAuthStore((s) => s.user?.roleId);
  const permissions = useWorkspaceStore((s) => s.workspace.permissions);

  if (roleId === "platform_owner" || permissions.includes("admin")) {
    return children;
  }
  const ok = require.some((p) => permissions.includes(p) || roleId === p);
  if (!ok) return <Navigate to={fallback} replace />;
  return children;
}
