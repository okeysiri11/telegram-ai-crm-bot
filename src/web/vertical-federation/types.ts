export const VERTICAL_FEDERATION_VERSION = "9.4.0";
export const VERTICAL_FEDERATION_SPRINT = "27.3";
export const VERTICAL_FEDERATION_API = "/api/verticals/v1";

export type VerticalRow = {
  id: string;
  name: string;
  status: string;
  kpiScore: number;
  activity: number;
  agents: number;
  aiUtilization: number;
  owner: string;
  aiDirector: string;
};

export type CrossLink = {
  source: string;
  target: string;
};
