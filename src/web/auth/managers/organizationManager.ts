import type { Organization } from "../types";

const orgs: Organization[] = [
  {
    organizationId: "org_demo",
    name: "Demo Corp",
    parentOrganization: null,
    owner: "usr_owner",
    activeUsers: 12,
    license: "enterprise",
    status: "active",
    kind: "company",
  },
  {
    organizationId: "org_ops",
    name: "Operations",
    parentOrganization: "org_demo",
    owner: "usr_ops",
    activeUsers: 5,
    license: "enterprise",
    status: "active",
    kind: "department",
  },
  {
    organizationId: "org_team_ai",
    name: "AI Team",
    parentOrganization: "org_ops",
    owner: "usr_owner",
    activeUsers: 3,
    license: "enterprise",
    status: "active",
    kind: "team",
  },
  {
    organizationId: "org_branch_kyiv",
    name: "Kyiv Branch",
    parentOrganization: "org_demo",
    owner: "usr_owner",
    activeUsers: 4,
    license: "enterprise",
    status: "active",
    kind: "branch",
  },
  {
    organizationId: "org_proj_web",
    name: "Enterprise Web",
    parentOrganization: "org_ops",
    owner: "usr_owner",
    activeUsers: 6,
    license: "enterprise",
    status: "active",
    kind: "project",
  },
];

export const organizationManager = {
  list(): Organization[] {
    return [...orgs];
  },
  get(id: string): Organization | undefined {
    return orgs.find((o) => o.organizationId === id);
  },
};
