/** Enterprise Navigation Platform — Sprint 26.5 */
export * from "./managers";
export * from "./types";
export { buildNavigationDashboard } from "./dashboard/navigationDashboard";
export { navigationPerformance } from "./performance";
export { CommandPalette } from "./components/CommandPalette";
export { QuickSwitcher } from "./components/QuickSwitcher";
export { NavigationProvider, useNavigationUi } from "./components/NavigationProvider";
export * from "./pages";

export const NAVIGATION_VERSION = "9.2.0";
export const NAVIGATION_PATH = "src/web/navigation";
export const NAVIGATION_API = "/api/enterprise-navigation/v1";
