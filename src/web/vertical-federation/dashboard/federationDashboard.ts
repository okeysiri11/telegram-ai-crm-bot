import type { CrossLink, VerticalRow } from "../types";
import { VERTICAL_FEDERATION_VERSION } from "../types";

const VERTICALS: VerticalRow[] = [
  { id: "vert_auto", name: "Auto", status: "production", kpiScore: 88, activity: 72, agents: 4, aiUtilization: 0.61, owner: "auto_ops", aiDirector: "Auto AI Director" },
  { id: "vert_beauty", name: "Beauty", status: "production", kpiScore: 86, activity: 68, agents: 3, aiUtilization: 0.55, owner: "beauty_ops", aiDirector: "Beauty AI Director" },
  { id: "vert_medical", name: "Medical", status: "ready", kpiScore: 84, activity: 55, agents: 3, aiUtilization: 0.48, owner: "medical_owner", aiDirector: "Medical AI Director" },
  { id: "vert_construction", name: "Construction", status: "ready", kpiScore: 82, activity: 50, agents: 2, aiUtilization: 0.45, owner: "construction_owner", aiDirector: "Construction AI Director" },
  { id: "vert_manufacturing", name: "Manufacturing", status: "ready", kpiScore: 81, activity: 52, agents: 3, aiUtilization: 0.5, owner: "manufacturing_owner", aiDirector: "Manufacturing AI Director" },
  { id: "vert_agriculture", name: "Agriculture", status: "ready", kpiScore: 80, activity: 47, agents: 2, aiUtilization: 0.42, owner: "agro_ops", aiDirector: "Agriculture AI Director" },
  { id: "vert_real_estate", name: "Real Estate", status: "ready", kpiScore: 79, activity: 44, agents: 2, aiUtilization: 0.4, owner: "real_estate_owner", aiDirector: "Real Estate AI Director" },
  { id: "vert_logistics", name: "Logistics", status: "ready", kpiScore: 78, activity: 66, agents: 4, aiUtilization: 0.86, owner: "logistics_owner", aiDirector: "Logistics AI Director" },
  { id: "vert_port", name: "Port", status: "ready", kpiScore: 85, activity: 60, agents: 3, aiUtilization: 0.58, owner: "port_ops", aiDirector: "Port AI Director" },
  { id: "vert_crypto", name: "Crypto", status: "ready", kpiScore: 83, activity: 58, agents: 3, aiUtilization: 0.53, owner: "treasury", aiDirector: "Crypto AI Director" },
  { id: "vert_finance", name: "Finance", status: "production", kpiScore: 90, activity: 70, agents: 4, aiUtilization: 0.64, owner: "cfo_office", aiDirector: "Finance AI Director" },
  { id: "vert_legal", name: "Legal", status: "production", kpiScore: 87, activity: 49, agents: 2, aiUtilization: 0.46, owner: "clo_office", aiDirector: "Legal AI Director" },
  { id: "vert_education", name: "Education", status: "pilot", kpiScore: 74, activity: 30, agents: 2, aiUtilization: 0.35, owner: "education_owner", aiDirector: "Education AI Director" },
  { id: "vert_retail", name: "Retail", status: "ready", kpiScore: 77, activity: 54, agents: 3, aiUtilization: 0.51, owner: "retail_owner", aiDirector: "Retail AI Director" },
  { id: "vert_hospitality", name: "Hospitality", status: "pilot", kpiScore: 73, activity: 28, agents: 2, aiUtilization: 0.33, owner: "hospitality_owner", aiDirector: "Hospitality AI Director" },
  { id: "vert_marketplace", name: "Marketplace", status: "ready", kpiScore: 81, activity: 62, agents: 3, aiUtilization: 0.57, owner: "marketplace_owner", aiDirector: "Marketplace AI Director" },
  { id: "vert_drone", name: "Drone", status: "ready", kpiScore: 76, activity: 41, agents: 2, aiUtilization: 0.49, owner: "ai_vision_lab", aiDirector: "Drone AI Director" },
];

const LINKS: CrossLink[] = [
  { source: "CRM", target: "Finance" },
  { source: "Finance", target: "ERP" },
  { source: "ERP", target: "Logistics" },
  { source: "Beauty", target: "CRM" },
  { source: "Medical", target: "Analytics" },
  { source: "Construction", target: "Marketplace" },
  { source: "Agro", target: "Drone" },
  { source: "Drone", target: "AI Vision" },
  { source: "Crypto", target: "Finance" },
];

export function buildVerticalFederationDashboard() {
  const agentsTotal = VERTICALS.reduce((s, v) => s + v.agents, 0);
  const aiAvg = VERTICALS.reduce((s, v) => s + v.aiUtilization, 0) / VERTICALS.length;
  return {
    title: "Vertical Federation Dashboard",
    version: VERTICAL_FEDERATION_VERSION,
    verticals: VERTICALS,
    links: LINKS,
    kpi: {
      verticalsTotal: VERTICALS.length,
      production: VERTICALS.filter((v) => v.status === "production").length,
      avgKpi: Math.round(VERTICALS.reduce((s, v) => s + v.kpiScore, 0) / VERTICALS.length),
      agentsTotal,
      aiUtilizationAvg: aiAvg,
    },
    events: [
      { type: "sync", message: "Auto ↔ Finance KPI sync completed" },
      { type: "publish", message: "Beauty published CRM widget pack" },
    ],
    alerts: [
      { level: "info", message: "Port throughput within SLA" },
      { level: "warn", message: "Logistics AI utilization above 85%" },
    ],
    recommendations: [
      "Connect Construction marketplace listings to CRM pipeline",
      "Promote Drone → AI Vision semantic knowledge pack to shared scope",
    ],
    executiveAiConnected: true,
  };
}

export const verticalRegistry = { list: () => VERTICALS };
export const crossVerticalLinks = { list: () => LINKS };
