import type { ReleaseDashboardData } from "../types";
import { RELEASE_CODE, RELEASE_VERSION } from "../types";

/** Static RC dashboard snapshot for offline/UI (mirrors backend health report shape). */
export function buildReleaseDashboard(): ReleaseDashboardData {
  return {
    title: "Release Candidate Dashboard",
    version: RELEASE_VERSION,
    releaseCode: RELEASE_CODE,
    health: "ready",
    overallReadinessPct: 96.5,
    coverage: {
      integration: 100,
      applications: 95,
      routes: 100,
      security: 100,
      performance: 100,
      documentation: 100,
      tests: 100,
    },
    criticalIssues: [],
    warnings: ["soft_workspace_routes_without_dedicated_pages"],
    recommendations: [
      "proceed_to_production_ga_planning",
      "keep_rc_gate_green_before_ga",
      "monitor_search_and_command_latency",
      "maintain_security_regression_suite",
    ],
    integratedModules: 33,
    totalModules: 33,
    applicationCount: 16,
    platformPackages: 72,
    reactRoutes: 28,
  };
}
