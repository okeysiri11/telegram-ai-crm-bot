/** Sprint 41.1 — GlobeFly seeded UI demo data (localStorage). */

export type GlobeFlySeed = {
  company: {
    name: string;
    industry: string;
    website: string;
    logoDataUrl: string | null;
  };
  clients: Array<{ id: string; name: string; email: string; status: string }>;
  leads: Array<{ id: string; title: string; source: string; status: string }>;
  deals: Array<{ id: string; title: string; stage: string; amount: number }>;
  documents: Array<{ id: string; name: string; type: string; sizeKb: number }>;
  invoices: Array<{ id: string; number: string; amount: number; status: string }>;
  knowledge: Array<{ id: string; title: string; summary: string }>;
  aiPrompts: string[];
  dashboard: { openLeads: number; activeDeals: number; revenueMtd: number };
};

export const GLOBEFLY_SEED: GlobeFlySeed = {
  company: {
    name: "GlobeFly",
    industry: "Туризм и авиабилеты",
    website: "https://globefly.example",
    logoDataUrl: null,
  },
  clients: [
    { id: "gf_c1", name: "Авиа Тур+", email: "ops@aviatour.example", status: "active" },
    { id: "gf_c2", name: "Travel Soft", email: "hello@travelsoft.example", status: "active" },
    { id: "gf_c3", name: "Sky Partners", email: "sales@skypartners.example", status: "lead" },
  ],
  leads: [
    { id: "gf_l1", title: "Корпоративные билеты Q3", source: "web", status: "new" },
    { id: "gf_l2", title: "Партнёрство OTA", source: "referral", status: "qualified" },
  ],
  deals: [
    { id: "gf_d1", title: "Подписка B2B API", stage: "proposal", amount: 420000 },
    { id: "gf_d2", title: "White-label кабинет", stage: "negotiation", amount: 890000 },
  ],
  documents: [
    { id: "gf_doc1", name: "Договор_GlobeFly.pdf", type: "pdf", sizeKb: 240 },
    { id: "gf_doc2", name: "Прайс_2026.xlsx", type: "xlsx", sizeKb: 88 },
    { id: "gf_doc3", name: "Бриф_клиента.docx", type: "docx", sizeKb: 64 },
  ],
  invoices: [
    { id: "gf_inv1", number: "GF-2026-001", amount: 120000, status: "paid" },
    { id: "gf_inv2", number: "GF-2026-014", amount: 56000, status: "open" },
  ],
  knowledge: [
    {
      id: "gf_k1",
      title: "Как создать лид",
      summary: "CRM → Лиды → Создать. Укажите источник и контакт.",
    },
    {
      id: "gf_k2",
      title: "Сделка по воронке",
      summary: "Откройте сделку и перемещайте стадии: квалификация → предложение → закрытие.",
    },
  ],
  aiPrompts: [
    "Суммируй открытые сделки GlobeFly",
    "Какие лиды требуют внимания сегодня?",
    "Подготовь рекомендации по клиенту Авиа Тур+",
  ],
  dashboard: { openLeads: 2, activeDeals: 2, revenueMtd: 176000 },
};
