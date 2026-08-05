/** Sprint 30.8 — Enterprise Business Modules. */
export { BusinessModuleShell } from "./BusinessModuleShell";
export { CrmModulePage } from "./CrmModulePage";
export { ProjectsModulePage, countProjects } from "./ProjectsModulePage";
export { KnowledgeModulePage, countKnowledge } from "./KnowledgeModulePage";
export { CalendarModulePage, countCalendarEvents } from "./CalendarModulePage";
export { DriveModulePage, countDriveFiles } from "./DriveModulePage";
export { MarketplaceModulePage } from "./MarketplaceModulePage";
export { NotificationsModulePage } from "./NotificationsModulePage";
export { AiStudioModulePage } from "./AiStudioModulePage";
export { deriveOwnerMetrics } from "./deriveOwnerMetrics";
export { deriveGodModeMetrics, type GodModeMetric } from "./deriveGodModeMetrics";
export { hydrateCrm, readCrmCache } from "./crmApi";
