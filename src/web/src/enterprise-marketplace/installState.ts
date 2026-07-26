/**
 * Marketplace install records — Sprint 32.9.
 * Persists via localStorage (existing client persistence pattern).
 * No new Engine / Store library.
 */

import type { MarketplaceSolution, SolutionInstallStatus } from "./solutionCatalog";
import { MARKETPLACE_SOLUTIONS } from "./solutionCatalog";

const KEY = "ewp_marketplace_installed_v1";

export type InstalledRecord = {
  solutionId: string;
  status: SolutionInstallStatus;
  version: string;
  installedAt: string;
  imported: {
    team: boolean;
    skills: boolean;
    workflows: boolean;
    prompts: boolean;
  };
};

type InstallMap = Record<string, InstalledRecord>;

function readMap(): InstallMap {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return {};
    return JSON.parse(raw) as InstallMap;
  } catch {
    return {};
  }
}

function writeMap(map: InstallMap) {
  try {
    localStorage.setItem(KEY, JSON.stringify(map));
  } catch {
    /* ignore */
  }
}

export function listInstalled(): InstalledRecord[] {
  return Object.values(readMap());
}

export function getInstallRecord(solutionId: string): InstalledRecord | undefined {
  return readMap()[solutionId];
}

export function resolveStatus(solution: MarketplaceSolution): SolutionInstallStatus {
  const rec = getInstallRecord(solution.id);
  if (rec) return rec.status;
  return solution.statusDefault || "available";
}

/** One-click install — records import of Team / Skills / Workflow / Prompts. */
export function installSolution(solution: MarketplaceSolution): InstalledRecord {
  const map = readMap();
  const rec: InstalledRecord = {
    solutionId: solution.id,
    status: "installed",
    version: solution.version,
    installedAt: new Date().toISOString(),
    imported: {
      team: solution.aiTeam.length > 0,
      skills: solution.skills.length > 0,
      workflows: solution.workflows.length > 0,
      prompts: solution.prompts.length > 0,
    },
  };
  map[solution.id] = rec;
  writeMap(map);
  return rec;
}

export function setInstallStatus(solutionId: string, status: SolutionInstallStatus) {
  const map = readMap();
  const existing = map[solutionId];
  const sol = MARKETPLACE_SOLUTIONS.find((s) => s.id === solutionId);
  map[solutionId] = {
    solutionId,
    status,
    version: existing?.version || sol?.version || "1.0.0",
    installedAt: existing?.installedAt || new Date().toISOString(),
    imported: existing?.imported || { team: false, skills: false, workflows: false, prompts: false },
  };
  writeMap(map);
}

export function markUpdateAvailable(solutionId: string) {
  const map = readMap();
  if (!map[solutionId]) return;
  map[solutionId] = { ...map[solutionId], status: "update" };
  writeMap(map);
}

export type CompatibilityReport = {
  ok: boolean;
  checks: Array<{ id: string; label: string; pass: boolean; detail: string }>;
};

export function checkCompatibility(
  solution: MarketplaceSolution,
  ctx: {
    workspaceId?: string;
    ecosystem?: string;
    roleId?: string;
    hasAccess?: boolean;
    platformVersion?: string;
  },
): CompatibilityReport {
  const eco = (ctx.ecosystem || "platform").toLowerCase();
  const role = (ctx.roleId || "owner").toLowerCase();
  const checks = [
    {
      id: "workspace",
      label: "Workspace",
      pass: Boolean(ctx.workspaceId || "default"),
      detail: ctx.workspaceId ? `Workspace · ${ctx.workspaceId}` : "Default workspace ready",
    },
    {
      id: "ecosystem",
      label: "Business Ecosystem",
      pass:
        solution.ecosystems.includes("platform") ||
        solution.ecosystems.map((e) => e.toLowerCase()).includes(eco) ||
        eco === "platform",
      detail: `Requires ${solution.ecosystems.join(", ")} · current ${eco}`,
    },
    {
      id: "role",
      label: "Роль",
      pass: solution.roles.length === 0 || solution.roles.some((r) => r.toLowerCase() === role || role === "owner"),
      detail: `Requires ${solution.roles.join(", ") || "any"} · current ${role}`,
    },
    {
      id: "access",
      label: "Доступ",
      pass: ctx.hasAccess !== false,
      detail: ctx.hasAccess === false ? "Недостаточно прав" : "Доступ разрешён",
    },
    {
      id: "version",
      label: "Версия",
      pass: true,
      detail: `Solution ${solution.version} · platform ${ctx.platformVersion || "web"}`,
    },
  ];
  return { ok: checks.every((c) => c.pass), checks };
}
