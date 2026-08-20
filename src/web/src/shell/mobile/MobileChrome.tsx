import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useIsPlatformOwner } from "../../../platform-builder/managers/platformOwner";
import { resolveRoleLabel, useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { MobileBackBar } from "./MobileBackBar";
import { MobileBottomNav } from "./MobileBottomNav";
import { MobileMoreSheet } from "./MobileMoreSheet";
import { MobileTopBar } from "./MobileTopBar";
import { MobileWorkspaceDrawer } from "./MobileWorkspaceDrawer";
import { MobileWorkspaceSwitcherSheet } from "./MobileWorkspaceSwitcherSheet";
import {
  isDemoAccount,
  navFromContext,
  navFromVertical,
  PLATFORM_MANAGEMENT_NAV,
  sectionTitle,
  verticalIdFromPath,
  workspaceHomePath,
  workspaceLabel,
  workspaceSwitcherItems,
} from "./mobileWorkspace";
import { useOpsCabinetNavStore } from "./opsCabinetNavStore";
import { useMobileChromeStore } from "./mobileChromeStore";
import { useIsMobile } from "./useIsMobile";
import "./mobileShell.css";

export function MobileChrome() {
  const mobile = useIsMobile();
  const { pathname, search } = useLocation();
  const storedVertical = useVerticalWorkspaceStore((s) => s.verticalId);
  const cabinet = useOpsCabinetNavStore();
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  const ownerView = useRoleSwitcher((s) => s.isOwnerView());
  const isOwner = useIsPlatformOwner() || ownerView;
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    useMobileChromeStore.getState().closeAll();
  }, [pathname, search]);

  if (!mobile) return null;

  const verticalId = cabinet.verticalId || verticalIdFromPath(pathname, storedVertical);
  const label = cabinet.title || workspaceLabel(verticalId);
  const roleLabel = cabinet.roleHint || resolveRoleLabel(roleId);
  const items =
    cabinet.items.length > 0
      ? cabinet.items
      : navFromContext(pathname, search).length
        ? navFromContext(pathname, search)
        : navFromVertical(verticalId);
  const section = sectionTitle(pathname, search, verticalId, cabinet.items);
  const demo = isDemoAccount(user?.email, user?.tenantId);

  return (
    <>
      <MobileTopBar workspaceLabel={label} demo={demo} />
      <MobileBackBar section={section} workspaceLabel={label} verticalId={verticalId} />
      <MobileWorkspaceDrawer
        workspaceLabel={label}
        roleLabel={roleLabel}
        items={items}
        showPlatform={isOwner}
        platformItems={PLATFORM_MANAGEMENT_NAV}
      />
      <MobileMoreSheet />
      <MobileWorkspaceSwitcherSheet items={workspaceSwitcherItems()} />
      <MobileBottomNav workspaceHome={workspaceHomePath(verticalId)} />
    </>
  );
}

export { useIsMobile } from "./useIsMobile";
export { MobileHome } from "./MobileHome";
export { isDemoAccount, verticalIdFromPath, navFromVertical, workspaceLabel } from "./mobileWorkspace";
