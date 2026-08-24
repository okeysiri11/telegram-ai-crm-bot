import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { useIsPlatformOwner } from "../../../platform-builder/managers/platformOwner";
import { resolveRoleLabel, useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { VERTICAL_BY_ID } from "@/vertical-workspace/catalog";
import { MobileBackBar } from "./MobileBackBar";
import { MobileBottomNav } from "./MobileBottomNav";
import { MobileCreateSheet } from "./MobileCreateSheet";
import { MobileMoreSheet } from "./MobileMoreSheet";
import { MobileSearchSheet } from "./MobileSearchSheet";
import { MobileTopBar } from "./MobileTopBar";
import { MobileWorkspaceDrawer } from "./MobileWorkspaceDrawer";
import { MobileWorkspaceSwitcherSheet } from "./MobileWorkspaceSwitcherSheet";
import {
  isDemoAccount,
  isOwnerSystemContext,
  mobileDrawerNav,
  mobileHeaderWorkspaceLabel,
  mobileSwitcherItems,
  PLATFORM_MANAGEMENT_NAV,
  sectionTitle,
  verticalIdFromPath,
  workspaceContextCopy,
  workspaceLabel,
} from "./mobileWorkspace";
import { useOpsCabinetNavStore } from "./opsCabinetNavStore";
import { useMobileChromeStore } from "./mobileChromeStore";
import { useMobileOverlayHistory } from "./useMobileOverlayHistory";
import { useIsMobile } from "./useIsMobile";
import "./mobileShell.css";

export function MobileChrome() {
  const mobile = useIsMobile();
  const { pathname, search } = useLocation();
  const storedVertical = useVerticalWorkspaceStore((s) => s.verticalId);
  const setVerticalId = useVerticalWorkspaceStore((s) => s.setVerticalId);
  const cabinet = useOpsCabinetNavStore();
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  const ownerView = useRoleSwitcher((s) => s.isOwnerView());
  const isOwner = useIsPlatformOwner() || ownerView;
  const user = useAuthStore((s) => s.user);
  const orgLabel = useOrgSelector((s) => s.label());

  useMobileOverlayHistory();

  useEffect(() => {
    useMobileChromeStore.getState().closeAll();
  }, [pathname, search]);

  useEffect(() => {
    const fromPath = verticalIdFromPath(pathname, "");
    if (fromPath && VERTICAL_BY_ID[fromPath] && !isOwnerSystemContext(fromPath)) {
      setVerticalId(fromPath);
    }
  }, [pathname, setVerticalId]);

  if (!mobile) return null;

  const verticalId = cabinet.verticalId || verticalIdFromPath(pathname, storedVertical);
  const catalogLabel = cabinet.title || workspaceLabel(verticalId);
  const context = workspaceContextCopy(verticalId, catalogLabel);
  const headerLabel = mobileHeaderWorkspaceLabel(verticalId, orgLabel);
  const roleLabel = cabinet.roleHint || resolveRoleLabel(roleId);
  const items = mobileDrawerNav(verticalId, cabinet);
  const section = sectionTitle(pathname, search, verticalId, items);
  const demo = isDemoAccount(user?.email, user?.tenantId);
  const drawerTitle = isOwnerSystemContext(verticalId) ? context.title : catalogLabel;
  const ownerSystem = isOwnerSystemContext(verticalId);

  return (
    <>
      <MobileTopBar workspaceLabel={headerLabel} demo={demo} />
      <MobileBackBar section={section} workspaceLabel={drawerTitle} verticalId={verticalId} />
      <MobileWorkspaceDrawer
        workspaceLabel={drawerTitle}
        roleLabel={ownerSystem ? "Владелец" : roleLabel}
        items={items}
        showPlatform={Boolean(isOwner && ownerSystem)}
        platformItems={PLATFORM_MANAGEMENT_NAV}
      />
      <MobileMoreSheet />
      <MobileWorkspaceSwitcherSheet items={mobileSwitcherItems()} />
      <MobileCreateSheet verticalId={verticalId} />
      <MobileSearchSheet />
      <MobileBottomNav />
    </>
  );
}

export { useIsMobile } from "./useIsMobile";
export { MobileHome } from "./MobileHome";
export { isDemoAccount, verticalIdFromPath, navFromVertical, workspaceLabel } from "./mobileWorkspace";
