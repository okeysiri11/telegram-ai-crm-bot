export const ORGANIZATION_BRAIN_VERSION = "9.4.0";
export const ORGANIZATION_BRAIN_SPRINT = "27.2";
export const ORGANIZATION_BRAIN_API = "/api/organization-brain/v1";

export type BoardMember = {
  agentId: string;
  title: string;
  name: string;
  domain: string;
  status: string;
  load: number;
};

export type DepartmentRow = {
  id: string;
  name: string;
  efficiency: number;
  kpiScore: number;
  aiLoad: number;
  headcount: number;
};
