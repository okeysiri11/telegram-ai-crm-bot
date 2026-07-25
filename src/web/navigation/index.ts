/** Enterprise Navigation Platform — Sprint 26.5 */
export * from "./managers";
export * from "./types";
export { buildNavigationDashboard } from "./dashboard/navigationDashboard";
export { navigationPerformance } from "./performance";
export { CommandPalette } from "./components/CommandPalette";
export { NavigationProvider, useNavigationUi } from "./components/NavigationProvider";
export * from "./pages";

export const NAVIGATION_VERSION = "9.0.4";
export const NAVIGATION_PATH = "src/web/navigation";
