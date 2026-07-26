/**
 * Pilot role journeys — Sprint 30.8.
 * Validates Owner / Manager / Sales / Employee / Customer paths using existing auth + routes.
 * Dual pilots: Automotive + Beauty.
 */

export type PilotRole = "owner" | "manager" | "sales" | "employee" | "customer";

export type JourneyStep = {
  id: string;
  label: string;
  route: string;
  requiresAuth: boolean;
};

export type RoleJourney = {
  role: PilotRole;
  title: string;
  description: string;
  expectedRoleIds: string[];
  steps: JourneyStep[];
};

export const PILOT_ROLE_JOURNEYS: RoleJourney[] = [
  {
    role: "owner",
    title: "Owner",
    description: "Login → Pilot → Mission Control → Automotive + Beauty workflows → Analytics",
    expectedRoleIds: ["platform_owner", "company_owner", "owner"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "pilot", label: "Pilot Dashboard", route: "/pilot", requiresAuth: true },
      { id: "mc", label: "Mission Control", route: "/platform-builder/mission-control", requiresAuth: true },
      { id: "auto", label: "Automotive workflow", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty workflow", route: "/workspace/beauty", requiresAuth: true },
      { id: "owner_portal", label: "Owner portal", route: "/portals/owner", requiresAuth: true },
    ],
  },
  {
    role: "manager",
    title: "Manager",
    description: "Login → Workspace → Auto/Beauty → Notifications → Pilot metrics",
    expectedRoleIds: ["role_org_owner", "manager", "company_owner"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "workspace", label: "Workspace", route: "/workspace", requiresAuth: true },
      { id: "auto", label: "Automotive", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty schedule", route: "/workspace/beauty", requiresAuth: true },
      { id: "employee", label: "Employee portal", route: "/portals/employee", requiresAuth: true },
      { id: "pilot", label: "Pilot Dashboard", route: "/pilot", requiresAuth: true },
    ],
  },
  {
    role: "sales",
    title: "Sales",
    description: "Login → Automotive lead workflow → Beauty CRM → Tasks → Notifications",
    expectedRoleIds: ["role_org_owner", "manager", "employee", "sales_agent"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "auto", label: "Lead → CRM → Task", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty client journey", route: "/workspace/beauty", requiresAuth: true },
      { id: "crm", label: "CRM module", route: "/workspace/crm", requiresAuth: true },
      { id: "pilot", label: "Feedback", route: "/pilot", requiresAuth: true },
    ],
  },
  {
    role: "employee",
    title: "Employee",
    description: "Login → Employee portal → Beauty workspace → Pilot feedback",
    expectedRoleIds: ["employee", "role_org_owner", "manager"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "portal", label: "Employee portal", route: "/portals/employee", requiresAuth: true },
      { id: "beauty", label: "Beauty calendar", route: "/workspace/beauty", requiresAuth: true },
      { id: "workspace", label: "Workspace", route: "/workspace", requiresAuth: true },
      { id: "pilot", label: "Pilot Dashboard", route: "/pilot", requiresAuth: true },
    ],
  },
  {
    role: "customer",
    title: "Customer",
    description: "Portal auth (Automotive) + Beauty booking path → Customer portal shell",
    expectedRoleIds: ["customer", "role_org_owner", "platform_owner", "manager", "employee"],
    steps: [
      { id: "auto", label: "Portal auth in workflow", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty appointment flow", route: "/workspace/beauty", requiresAuth: true },
      { id: "portal", label: "Customer portal", route: "/portals/customer", requiresAuth: true },
    ],
  },
];

export function matchJourneyRole(
  roleId: string | undefined,
  roles: string[] | undefined,
): PilotRole {
  const bag = new Set([...(roles || []), roleId || ""].map((r) => r.toLowerCase()));
  if (bag.has("platform_owner") || bag.has("owner") || bag.has("company_owner")) return "owner";
  if (bag.has("manager") || bag.has("role_org_owner")) return "manager";
  if (bag.has("sales_agent") || bag.has("sales")) return "sales";
  if (bag.has("customer")) return "customer";
  return "employee";
}

export type JourneyValidation = {
  role: PilotRole;
  title: string;
  roleMatch: boolean;
  steps: { id: string; label: string; route: string; reachable: boolean }[];
  ok: boolean;
};

export function validateJourneys(opts: {
  authenticated: boolean;
  roleId?: string;
  roles?: string[];
}): JourneyValidation[] {
  const matched = matchJourneyRole(opts.roleId, opts.roles);
  return PILOT_ROLE_JOURNEYS.map((j) => {
    const roleMatch =
      j.role === matched ||
      j.expectedRoleIds.some((r) =>
        [opts.roleId, ...(opts.roles || [])].map((x) => (x || "").toLowerCase()).includes(r.toLowerCase()),
      );
    const steps = j.steps.map((s) => ({
      id: s.id,
      label: s.label,
      route: s.route,
      reachable: !s.requiresAuth || opts.authenticated,
    }));
    return {
      role: j.role,
      title: j.title,
      roleMatch,
      steps,
      ok: steps.every((s) => s.reachable),
    };
  });
}
