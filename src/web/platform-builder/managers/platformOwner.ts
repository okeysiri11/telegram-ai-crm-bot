import { useAuthStore } from "@/auth/authStore";

export const PLATFORM_OWNER_ROLE = "platform_owner";

export function isPlatformOwner(): boolean {
  const user = useAuthStore.getState().user;
  if (!user) return false;
  if (user.roleId === PLATFORM_OWNER_ROLE || user.roleId === "owner") return true;
  // Demo convenience: owner@* emails act as Platform Owner
  return (user.email || "").toLowerCase().startsWith("owner@");
}

export function useIsPlatformOwner(): boolean {
  const user = useAuthStore((s) => s.user);
  if (!user) return false;
  if (user.roleId === PLATFORM_OWNER_ROLE || user.roleId === "owner") return true;
  return (user.email || "").toLowerCase().startsWith("owner@");
}
