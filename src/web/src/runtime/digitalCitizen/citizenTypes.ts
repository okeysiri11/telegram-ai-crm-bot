/**
 * Enterprise Digital Citizen types — Sprint 29.1.
 * Human layer of Enterprise Runtime / City (people, not companies).
 */

export const DIGITAL_CITIZEN_VERSION = "29.1";
export const EDC_PERSIST_KEY = "ews_digital_citizen_v1";
export const EDC_API_PREFIX = "/api/enterprise-edc/v1";

export type CitizenStatus = "active" | "inactive" | "suspended" | "invited" | "archived";

export type CitizenVerification = "unverified" | "pending" | "verified" | "rejected";

export type PresenceStatus =
  | "online"
  | "offline"
  | "busy"
  | "meeting"
  | "working"
  | "away"
  | "vacation"
  | "invisible";

export type OrganizationRole =
  | "owner"
  | "admin"
  | "manager"
  | "member"
  | "contractor"
  | "guest";

export type CitizenPermissionScope =
  | "self"
  | "manager"
  | "department"
  | "company"
  | "partners"
  | "public"
  | "enterprise_admin";

export type PersonalAiKind =
  | "personal"
  | "executive"
  | "developer"
  | "sales"
  | "finance"
  | "legal"
  | "assistant";

export type CitizenActivityName =
  | "CitizenCreated"
  | "CitizenUpdated"
  | "CitizenJoinedCompany"
  | "CitizenLeftCompany"
  | "RoleChanged"
  | "TaskAssigned"
  | "MeetingJoined"
  | "DocumentSigned"
  | "ProjectJoined"
  | "AIAssigned"
  | "PresenceChanged";

export type CitizenIdentity = {
  email: string;
  userId?: string;
  telegramId?: number;
  externalIds?: Record<string, string>;
};

export type CitizenPreferences = {
  locale: string;
  timezone: string;
  notifyEmail: boolean;
  notifyPush: boolean;
  theme?: "light" | "dark" | "system";
  defaultSurface?: string;
};

export type CitizenPresence = {
  status: PresenceStatus;
  since: string;
  locationLabel?: string;
  officeId?: string;
  cityBuildingId?: string;
  message?: string;
};

export type CitizenProfile = {
  id: string;
  displayName: string;
  firstName?: string;
  lastName?: string;
  title?: string;
  avatarUrl?: string;
  bio?: string;
  status: CitizenStatus;
  verification: CitizenVerification;
  identity: CitizenIdentity;
  preferences: CitizenPreferences;
  presence: CitizenPresence;
  metadata: Record<string, unknown>;
  primaryOrgId?: string;
  createdAt: string;
  updatedAt: string;
};

/** Alias used in sprint brief */
export type Citizen = CitizenProfile;

export type Department = {
  id: string;
  orgId: string;
  name: string;
  parentDepartmentId?: string;
};

export type Position = {
  id: string;
  orgId: string;
  title: string;
  departmentId?: string;
  level?: number;
};

export type EmploymentHistoryEntry = {
  id: string;
  orgId: string;
  role: OrganizationRole;
  positionTitle?: string;
  departmentId?: string;
  startedAt: string;
  endedAt?: string;
  reason?: string;
};

export type OrganizationMember = {
  id: string;
  citizenId: string;
  orgId: string;
  /** Links to Business Network business profile when available */
  businessProfileId?: string;
  role: OrganizationRole;
  departmentId?: string;
  positionId?: string;
  managerCitizenId?: string;
  ownershipPct?: number;
  active: boolean;
  joinedAt: string;
  leftAt?: string;
  history: EmploymentHistoryEntry[];
};

export type PersonalTask = {
  id: string;
  citizenId: string;
  title: string;
  done: boolean;
  dueAt?: string;
  projectId?: string;
  createdAt: string;
};

export type PersonalCalendarEvent = {
  id: string;
  citizenId: string;
  title: string;
  startsAt: string;
  endsAt: string;
  meeting?: boolean;
};

export type AssignedProject = {
  id: string;
  citizenId: string;
  projectId: string;
  projectName: string;
  role?: string;
  joinedAt: string;
};

export type WorkspaceBookmark = {
  id: string;
  label: string;
  path: string;
  favorite?: boolean;
};

export type CitizenWorkspace = {
  citizenId: string;
  dashboardTitle: string;
  tasks: PersonalTask[];
  calendar: PersonalCalendarEvent[];
  projects: AssignedProject[];
  documentRefs: string[];
  notificationIds: string[];
  bookmarks: WorkspaceBookmark[];
  favorites: string[];
  updatedAt: string;
};

export type PersonalAiAgent = {
  id: string;
  kind: PersonalAiKind;
  name: string;
  description?: string;
  ownerCitizenId?: string;
  assignedCitizenId?: string;
  orgId?: string;
  active: boolean;
  createdAt: string;
};

export type CitizenActivityEvent = {
  id: string;
  name: CitizenActivityName;
  citizenId: string;
  at: string;
  payload: Record<string, unknown>;
};

/** City runtime interface — no rendering */
export type CityCitizenFacade = {
  citizenId: string;
  displayName: string;
  avatarUrl?: string;
  presence: PresenceStatus;
  role?: OrganizationRole;
  companyOrgId?: string;
  companyBusinessProfileId?: string;
  officeId?: string;
  locationLabel?: string;
  cityBuildingId?: string;
  aiAssignmentIds: string[];
};
