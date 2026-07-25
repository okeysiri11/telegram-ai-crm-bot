export const RELEASE_VERSION = "9.2.0";
export const RELEASE_CODE = "RC1";
export const RELEASE_API = "/api/release/v1";
export const RELEASE_PATH = "src/web/release";

export type CoverageScores = {
  integration: number;
  applications: number;
  routes: number;
  security: number;
  performance: number;
  documentation: number;
  tests: number;
};

export type ReleaseDashboardData = {
  title: string;
  version: string;
  releaseCode: string;
  health: string;
  overallReadinessPct: number;
  coverage: CoverageScores;
  criticalIssues: string[];
  warnings: string[];
  recommendations: string[];
  integratedModules: number;
  totalModules: number;
  applicationCount: number;
  platformPackages: number;
  reactRoutes: number;
};
