/**
 * Sprint 30.8 — CRM API bind to Auto Marketplace CRM Engine + workspace cache.
 * Prefix: /api/auto/v1/crm (existing). No parallel CRM engine.
 */

import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { loadJson, saveJson, newId } from "./persist";

export type CrmClient = {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  companyId?: string;
  tags: string[];
  segment: string;
};

export type CrmCompany = {
  id: string;
  name: string;
  inn?: string;
  industry?: string;
};

export type CrmContact = {
  id: string;
  name: string;
  email: string;
  phone: string;
  clientId?: string;
  companyId?: string;
  role?: string;
};

export type CrmLead = {
  id: string;
  title: string;
  status: string;
  source: string;
  clientId?: string;
  score: number;
  notes: string;
};

export type CrmDeal = {
  id: string;
  title: string;
  stage: string;
  amount: number;
  clientId?: string;
  leadId?: string;
};

export type CrmNote = {
  id: string;
  entityType: string;
  entityId: string;
  body: string;
  createdAt: string;
};

export type CrmAttachment = {
  id: string;
  entityType: string;
  entityId: string;
  name: string;
  url: string;
  createdAt: string;
};

export type CrmActivity = {
  id: string;
  kind: string;
  title: string;
  entityId?: string;
  at: string;
};

export type CrmState = {
  clients: CrmClient[];
  companies: CrmCompany[];
  contacts: CrmContact[];
  leads: CrmLead[];
  deals: CrmDeal[];
  notes: CrmNote[];
  attachments: CrmAttachment[];
  activities: CrmActivity[];
  source: "api" | "workspace";
  loadedAt: string | null;
};

const EMPTY: CrmState = {
  clients: [],
  companies: [],
  contacts: [],
  leads: [],
  deals: [],
  notes: [],
  attachments: [],
  activities: [],
  source: "workspace",
  loadedAt: null,
};

function crmBase(): string {
  return `${webConfig.autoPrefix}/crm`;
}

function mapCustomer(raw: Record<string, unknown>): CrmClient {
  return {
    id: String(raw.customer_id || raw.id || newId("cli")),
    firstName: String(raw.first_name || raw.firstName || ""),
    lastName: String(raw.last_name || raw.lastName || ""),
    email: String(raw.email || ""),
    phone: String(raw.phone || ""),
    tags: Array.isArray(raw.tags) ? (raw.tags as string[]) : [],
    segment: String(raw.segment || "standard"),
  };
}

function mapLead(raw: Record<string, unknown>): CrmLead {
  return {
    id: String(raw.lead_id || raw.id || newId("lead")),
    title: String(raw.notes || raw.title || `Лид ${String(raw.lead_id || "").slice(0, 8)}`),
    status: String(raw.status || "new"),
    source: String(raw.source || "web"),
    clientId: raw.customer_id ? String(raw.customer_id) : undefined,
    score: Number(raw.score || 0),
    notes: String(raw.notes || ""),
  };
}

function mapDeal(raw: Record<string, unknown>): CrmDeal {
  return {
    id: String(raw.deal_id || raw.id || newId("deal")),
    title: String(raw.title || `Сделка ${String(raw.deal_id || "").slice(0, 8)}`),
    stage: String(raw.stage || "prospect"),
    amount: Number(raw.amount || raw.value || 0),
    clientId: raw.customer_id ? String(raw.customer_id) : undefined,
    leadId: raw.lead_id ? String(raw.lead_id) : undefined,
  };
}

export function readCrmCache(): CrmState {
  return loadJson<CrmState>("crm", EMPTY);
}

export function writeCrmCache(state: CrmState): void {
  saveJson("crm", state);
}

/** Hydrate from Auto CRM API; on failure keep workspace cache (no fake seed). */
export async function hydrateCrm(): Promise<CrmState> {
  const cached = readCrmCache();
  try {
    const [cRes, lRes, dRes, pRes] = await Promise.all([
      apiFetch(`${crmBase()}/customers`),
      apiFetch(`${crmBase()}/leads`),
      apiFetch(`${crmBase()}/deals`),
      apiFetch(`${crmBase()}/pipeline`),
    ]);
    if (!cRes.ok && !lRes.ok) {
      return { ...cached, source: "workspace", loadedAt: new Date().toISOString() };
    }
    const cJson = cRes.ok ? ((await cRes.json()) as { items?: Record<string, unknown>[] }) : { items: [] };
    const lJson = lRes.ok ? ((await lRes.json()) as { items?: Record<string, unknown>[] }) : { items: [] };
    const dJson = dRes.ok ? ((await dRes.json()) as { items?: Record<string, unknown>[] }) : { items: [] };
    const pipeline = pRes.ok ? ((await pRes.json()) as Record<string, unknown>) : {};

    const clients = (cJson.items || []).map(mapCustomer);
    const leads = (lJson.items || []).map(mapLead);
    const deals = (dJson.items || []).map(mapDeal);
    const activities: CrmActivity[] = [];
    if (pipeline && typeof pipeline === "object") {
      activities.push({
        id: newId("act"),
        kind: "pipeline",
        title: "Воронка синхронизирована",
        at: new Date().toISOString(),
      });
    }

    const next: CrmState = {
      ...cached,
      clients: clients.length ? clients : cached.clients,
      leads: leads.length ? leads : cached.leads,
      deals: deals.length ? deals : cached.deals,
      activities: activities.length ? activities : cached.activities,
      source: cRes.ok || lRes.ok ? "api" : "workspace",
      loadedAt: new Date().toISOString(),
    };
    writeCrmCache(next);
    return next;
  } catch {
    return { ...cached, source: "workspace", loadedAt: new Date().toISOString() };
  }
}

export async function createCrmClient(input: {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
}): Promise<CrmClient> {
  const body = {
    first_name: input.firstName,
    last_name: input.lastName,
    email: input.email,
    phone: input.phone,
  };
  try {
    const res = await apiFetch(`${crmBase()}/customers`, { method: "POST", body: JSON.stringify(body) });
    if (res.ok) {
      const raw = (await res.json()) as Record<string, unknown>;
      const client = mapCustomer(raw);
      const state = readCrmCache();
      state.clients = [client, ...state.clients];
      state.activities = [
        { id: newId("act"), kind: "client", title: `Клиент: ${client.firstName} ${client.lastName}`, at: new Date().toISOString() },
        ...state.activities,
      ];
      writeCrmCache(state);
      return client;
    }
  } catch {
    /* workspace fallback */
  }
  const client: CrmClient = {
    id: newId("cli"),
    firstName: input.firstName,
    lastName: input.lastName,
    email: input.email,
    phone: input.phone,
    tags: [],
    segment: "standard",
  };
  const state = readCrmCache();
  state.clients = [client, ...state.clients];
  state.source = "workspace";
  state.activities = [
    { id: newId("act"), kind: "client", title: `Клиент (workspace): ${client.firstName}`, at: new Date().toISOString() },
    ...state.activities,
  ];
  writeCrmCache(state);
  return client;
}

export function upsertLocalCompany(name: string, industry?: string): CrmCompany {
  const company: CrmCompany = { id: newId("co"), name, industry };
  const state = readCrmCache();
  state.companies = [company, ...state.companies];
  writeCrmCache(state);
  return company;
}

export function upsertLocalContact(input: Omit<CrmContact, "id">): CrmContact {
  const contact: CrmContact = { id: newId("ct"), ...input };
  const state = readCrmCache();
  state.contacts = [contact, ...state.contacts];
  writeCrmCache(state);
  return contact;
}

export async function createCrmLead(input: { title: string; source: string; notes: string }): Promise<CrmLead> {
  try {
    const res = await apiFetch(`${crmBase()}/leads`, {
      method: "POST",
      body: JSON.stringify({ notes: input.notes || input.title, source: input.source }),
    });
    if (res.ok) {
      const raw = (await res.json()) as Record<string, unknown>;
      const lead = { ...mapLead(raw), title: input.title || mapLead(raw).title };
      const state = readCrmCache();
      state.leads = [lead, ...state.leads];
      writeCrmCache(state);
      return lead;
    }
  } catch {
    /* fallback */
  }
  const lead: CrmLead = {
    id: newId("lead"),
    title: input.title,
    status: "new",
    source: input.source,
    score: 0,
    notes: input.notes,
  };
  const state = readCrmCache();
  state.leads = [lead, ...state.leads];
  writeCrmCache(state);
  return lead;
}

export async function createCrmDeal(input: { title: string; stage: string; amount: number }): Promise<CrmDeal> {
  try {
    const res = await apiFetch(`${crmBase()}/deals`, {
      method: "POST",
      body: JSON.stringify({ title: input.title, stage: input.stage, amount: input.amount }),
    });
    if (res.ok) {
      const raw = (await res.json()) as Record<string, unknown>;
      const deal = mapDeal(raw);
      const state = readCrmCache();
      state.deals = [deal, ...state.deals];
      writeCrmCache(state);
      return deal;
    }
  } catch {
    /* fallback */
  }
  const deal: CrmDeal = {
    id: newId("deal"),
    title: input.title,
    stage: input.stage,
    amount: input.amount,
  };
  const state = readCrmCache();
  state.deals = [deal, ...state.deals];
  writeCrmCache(state);
  return deal;
}

export function addCrmNote(entityType: string, entityId: string, body: string): CrmNote {
  const note: CrmNote = {
    id: newId("note"),
    entityType,
    entityId,
    body,
    createdAt: new Date().toISOString(),
  };
  const state = readCrmCache();
  state.notes = [note, ...state.notes];
  writeCrmCache(state);
  return note;
}

export function addCrmAttachment(entityType: string, entityId: string, name: string): CrmAttachment {
  const att: CrmAttachment = {
    id: newId("att"),
    entityType,
    entityId,
    name,
    url: `#attachment/${name}`,
    createdAt: new Date().toISOString(),
  };
  const state = readCrmCache();
  state.attachments = [att, ...state.attachments];
  writeCrmCache(state);
  return att;
}

export const PIPELINE_STAGES = [
  "prospect",
  "qualification",
  "proposal",
  "negotiation",
  "approval",
  "closed_won",
  "closed_lost",
] as const;
