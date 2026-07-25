import type { BoardMember, DepartmentRow } from "../types";
import { ORGANIZATION_BRAIN_VERSION } from "../types";

const BOARD: BoardMember[] = [
  { agentId: "board_ceo", title: "CEO", name: "CEO AI", domain: "strategy_governance", status: "active", load: 0.35 },
  { agentId: "board_coo", title: "COO", name: "COO AI", domain: "operations_delivery", status: "active", load: 0.58 },
  { agentId: "board_cfo", title: "CFO", name: "CFO AI", domain: "finance_capital", status: "active", load: 0.35 },
  { agentId: "board_cto", title: "CTO", name: "CTO AI", domain: "technology_platform", status: "active", load: 0.35 },
  { agentId: "board_cmo", title: "CMO", name: "CMO AI", domain: "growth_brand", status: "active", load: 0.35 },
  { agentId: "board_chro", title: "CHRO", name: "CHRO AI", domain: "people_culture", status: "active", load: 0.35 },
  { agentId: "board_clo", title: "CLO", name: "CLO AI", domain: "legal_compliance", status: "active", load: 0.35 },
];

const DEPARTMENTS: DepartmentRow[] = [
  { id: "dept_sales", name: "Sales", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_marketing", name: "Marketing", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_finance", name: "Finance", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_hr", name: "HR", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_legal", name: "Legal", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 5 },
  { id: "dept_manufacturing", name: "Manufacturing", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_logistics", name: "Logistics", efficiency: 0.64, kpiScore: 71, aiLoad: 0.22, headcount: 12 },
  { id: "dept_crm", name: "CRM", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_erp", name: "ERP", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_analytics", name: "Analytics", efficiency: 0.78, kpiScore: 82, aiLoad: 0.22, headcount: 12 },
  { id: "dept_ai_department", name: "AI Department", efficiency: 0.78, kpiScore: 82, aiLoad: 0.4, headcount: 5 },
];

export function buildOrganizationDashboard() {
  const aiLoadAvg = BOARD.reduce((s, b) => s + b.load, 0) / BOARD.length;
  return {
    title: "Organization Executive Dashboard",
    version: ORGANIZATION_BRAIN_VERSION,
    companyState: "healthy" as const,
    kpi: { arrGrowth: 0.18, nps: 42, aiUtilization: 0.61, margin: 0.27 },
    departments: DEPARTMENTS,
    board: BOARD,
    employeeLoadAvg: 0.73,
    aiLoadAvg,
    financials: { revenueMtd: 1_250_000, opexMtd: 820_000, cashRunwayMonths: 14 },
    strategicGoals: [
      "Scale multi-agent OS across departments",
      "Raise NPS to 45+",
      "Automate 40% of CRM ops",
    ],
    alerts: [
      { level: "info", message: "Q3 pipeline review scheduled" },
      { level: "warn", message: "Logistics capacity at 86%" },
    ],
    recommendations: [
      "Reallocate AI agents to Sales outreach this week",
      "Approve Manufacturing overtime budget for peak demand",
    ],
  };
}

export const executiveBoard = { list: () => BOARD };
export const departmentCatalog = { list: () => DEPARTMENTS };
