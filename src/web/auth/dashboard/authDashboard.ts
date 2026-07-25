import {
  activityCenter,
  mfaCenter,
  organizationManager,
  permissionManager,
  roleManager,
  securityCenter,
  sessionManager,
  userManager,
} from "../managers";

export function buildAuthenticationDashboard() {
  const users = userManager.list();
  const sessions = sessionManager.activeSessions();
  const security = securityCenter.snapshot();
  const orgs = organizationManager.list();
  const roles = roleManager.list();
  const permissions = permissionManager.list();
  const activity = activityCenter.list();
  const history = sessionManager.loginHistory();
  return {
    userOverview: { total: users.length, active: users.filter((u) => u.status === "active").length },
    activeSessions: sessions,
    securityStatus: security,
    organizations: orgs,
    roles,
    permissions: permissionManager.domains(),
    permissionCount: permissions.length,
    recentActivity: activity.slice(0, 5),
    loginAnalytics: {
      successRate: history.filter((h) => h.success).length / Math.max(history.length, 1),
      total: history.length,
    },
    mfaAdoption: {
      methods: mfaCenter.methods,
      extensionsReady: mfaCenter.extensionsReady,
      ...mfaCenter.status,
    },
  };
}
