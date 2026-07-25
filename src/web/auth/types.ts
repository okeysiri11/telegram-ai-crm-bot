export type UserStatus = "active" | "disabled" | "invited" | "locked";

export type IdentityUser = {
  userId: string;
  name: string;
  avatar: string;
  email: string;
  username: string;
  company: string;
  department: string;
  position: string;
  language: "en" | "ru" | "uk";
  timeZone: string;
  status: UserStatus;
  lastLogin: string;
};

export type Organization = {
  organizationId: string;
  name: string;
  parentOrganization: string | null;
  owner: string;
  activeUsers: number;
  license: string;
  status: "active" | "suspended";
  kind: "company" | "department" | "team" | "branch" | "project";
};

export type RoleScope = "system" | "organization" | "project" | "custom";

export type Role = {
  roleId: string;
  name: string;
  scope: RoleScope;
  inheritsFrom: string[];
  permissionGroups: string[];
  template?: string;
};

export type PermissionDomain =
  | "crm"
  | "erp"
  | "ai_agents"
  | "finance"
  | "hr"
  | "analytics"
  | "marketplace"
  | "administration"
  | "api_access";

export type Permission = {
  permissionId: string;
  domain: PermissionDomain;
  action: string;
  syncedWithRbac: boolean;
};

export type SessionRecord = {
  sessionId: string;
  device: string;
  browser: string;
  ipAddress: string;
  lastActivity: string;
  current: boolean;
};

export type LoginHistoryEntry = {
  id: string;
  at: string;
  ipAddress: string;
  success: boolean;
  method: string;
};

export type MfaMethod = "totp" | "email_code" | "backup_codes";
export type MfaExtension = "fido2" | "webauthn" | "hardware_security_keys";

export type SecuritySnapshot = {
  mfaStatus: "enabled" | "disabled" | "partial";
  trustedDevices: number;
  recentLogins: number;
  failedAttempts: number;
  securityEvents: number;
  passwordAgeDays: number;
  riskScore: number;
};

export type ActivityKind =
  | "login"
  | "password_change"
  | "mfa_change"
  | "role_change"
  | "permission_change"
  | "device";

export type ActivityEntry = {
  id: string;
  kind: ActivityKind;
  summary: string;
  at: string;
};
