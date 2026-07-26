/**
 * Pilot role journeys — Sprint 31.4.
 * Validates Owner / Manager / Sales / Employee / Customer paths using existing auth + routes.
 * Seven pilots: Automotive + Beauty + Cafe + Agriculture + Legal + Bidex + Drone.
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
    description:
      "Login → Pilot → Mission Control → Auto + Beauty + Cafe + Agriculture + Legal + Bidex + Drone → Analytics",
    expectedRoleIds: ["platform_owner", "company_owner", "owner"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "pilot", label: "Pilot Dashboard", route: "/pilot", requiresAuth: true },
      { id: "mc", label: "Mission Control", route: "/platform-builder/mission-control", requiresAuth: true },
      { id: "auto", label: "Automotive workflow", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty workflow", route: "/workspace/beauty", requiresAuth: true },
      { id: "cafe", label: "Cafe workflow", route: "/workspace/cafe", requiresAuth: true },
      { id: "agro", label: "Agriculture workflow", route: "/workspace/agro", requiresAuth: true },
      { id: "legal", label: "Legal workflow", route: "/workspace/legal", requiresAuth: true },
      { id: "crypto", label: "Bidex workflow", route: "/workspace/crypto", requiresAuth: true },
      { id: "drone", label: "Drone workflow", route: "/workspace/drone", requiresAuth: true },
      { id: "owner_portal", label: "Owner portal", route: "/portals/owner", requiresAuth: true },
    ],
  },
  {
    role: "manager",
    title: "Manager",
    description: "Login → Workspace → Auto/Beauty/Cafe/Agro/Legal/Bidex/Drone → Notifications → Pilot metrics",
    expectedRoleIds: ["role_org_owner", "manager", "company_owner"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "workspace", label: "Workspace", route: "/workspace", requiresAuth: true },
      { id: "auto", label: "Automotive", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty schedule", route: "/workspace/beauty", requiresAuth: true },
      { id: "cafe", label: "Cafe kitchen", route: "/workspace/cafe", requiresAuth: true },
      { id: "agro", label: "Agriculture ops", route: "/workspace/agro", requiresAuth: true },
      { id: "legal", label: "Legal cases", route: "/workspace/legal", requiresAuth: true },
      { id: "crypto", label: "Bidex OTC", route: "/workspace/crypto", requiresAuth: true },
      { id: "drone", label: "Drone fleet", route: "/workspace/drone", requiresAuth: true },
      { id: "employee", label: "Employee portal", route: "/portals/employee", requiresAuth: true },
      { id: "pilot", label: "Pilot Dashboard", route: "/pilot", requiresAuth: true },
    ],
  },
  {
    role: "sales",
    title: "Sales",
    description: "Login → Auto → Beauty → Cafe → Agriculture → Legal → Bidex → Drone → Tasks",
    expectedRoleIds: ["role_org_owner", "manager", "employee", "sales_agent"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "auto", label: "Lead → CRM → Task", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty client journey", route: "/workspace/beauty", requiresAuth: true },
      { id: "cafe", label: "Cafe reservations", route: "/workspace/cafe", requiresAuth: true },
      { id: "agro", label: "Agriculture trade", route: "/workspace/agro", requiresAuth: true },
      { id: "legal", label: "Legal client intake", route: "/workspace/legal", requiresAuth: true },
      { id: "crypto", label: "Bidex desk", route: "/workspace/crypto", requiresAuth: true },
      { id: "drone", label: "Drone missions", route: "/workspace/drone", requiresAuth: true },
      { id: "crm", label: "CRM module", route: "/workspace/crm", requiresAuth: true },
      { id: "pilot", label: "Feedback", route: "/pilot", requiresAuth: true },
    ],
  },
  {
    role: "employee",
    title: "Employee",
    description: "Login → Employee portal → Beauty/Cafe/Agro/Legal/Bidex/Drone workspace → Pilot feedback",
    expectedRoleIds: ["employee", "role_org_owner", "manager"],
    steps: [
      { id: "login", label: "Login", route: "/login", requiresAuth: false },
      { id: "portal", label: "Employee portal", route: "/portals/employee", requiresAuth: true },
      { id: "beauty", label: "Beauty calendar", route: "/workspace/beauty", requiresAuth: true },
      { id: "cafe", label: "Cafe floor", route: "/workspace/cafe", requiresAuth: true },
      { id: "agro", label: "Agriculture harvest", route: "/workspace/agro", requiresAuth: true },
      { id: "legal", label: "Legal documents", route: "/workspace/legal", requiresAuth: true },
      { id: "crypto", label: "Bidex wallets", route: "/workspace/crypto", requiresAuth: true },
      { id: "drone", label: "Drone assembly", route: "/workspace/drone", requiresAuth: true },
      { id: "workspace", label: "Workspace", route: "/workspace", requiresAuth: true },
      { id: "pilot", label: "Pilot Dashboard", route: "/pilot", requiresAuth: true },
    ],
  },
  {
    role: "customer",
    title: "Customer",
    description: "Portal auth + Beauty/Cafe/Agro/Legal/Bidex/Drone paths → Customer portal shell",
    expectedRoleIds: ["customer", "role_org_owner", "platform_owner", "manager", "employee"],
    steps: [
      { id: "auto", label: "Portal auth in workflow", route: "/workspace/auto", requiresAuth: true },
      { id: "beauty", label: "Beauty appointment flow", route: "/workspace/beauty", requiresAuth: true },
      { id: "cafe", label: "Cafe order flow", route: "/workspace/cafe", requiresAuth: true },
      { id: "agro", label: "Agriculture marketplace", route: "/workspace/agro", requiresAuth: true },
      { id: "legal", label: "Legal matter status", route: "/workspace/legal", requiresAuth: true },
      { id: "crypto", label: "Bidex OTC status", route: "/workspace/crypto", requiresAuth: true },
      { id: "drone", label: "Drone mission status", route: "/workspace/drone", requiresAuth: true },
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
