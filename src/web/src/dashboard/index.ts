/** Enterprise Command Center — Sprint 32.3.2 + EP-01 Morning Brief + Sprint 27.1 modules. */
export { MissionControlStrip } from "./MissionControlStrip";
export { ExecutiveMorningBrief } from "./ExecutiveMorningBrief";
export { deriveMorningBrief, type MorningBrief, type BriefItem } from "./deriveMorningBrief";
export {
  ENTERPRISE_MODULE_CARDS,
  type EnterpriseModuleCard,
} from "./enterpriseModuleCards";
export {
  AI_ACTIVITY,
  BUSINESS_MODULES,
  DEFAULT_COMMAND_LAYOUT,
  KPI_CARDS,
  QUICK_ACTIONS,
  TODAY_ITEMS,
  loadCommandLayout,
  saveCommandLayout,
  toggleCommandSection,
  type BusinessModule,
  type CommandWidgetId,
  type KpiCard,
  type QuickAction,
} from "./commandCenterCatalog";
