/**
 * AUTO 1.0 — private import & dealership operating system.
 * Vehicle is the central entity. No fake financials, no dead success buttons.
 */

import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { Button, Card, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { BusinessCabinetShell, type OpsNavItem, type OpsSection } from "../business-ops/BusinessCabinetShell";
import {
  asList,
  autoOpsDelete,
  autoOpsFileUrl,
  autoOpsGet,
  autoOpsPost,
  autoOpsUpload,
  pick,
} from "../business-ops/opsApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";
import {
  CARD_RU,
  DOC_RU,
  EXPENSE_RU,
  FIN_RU,
  PHOTO_RU,
  PURCHASE_STATUSES,
  ROLE_RU,
  STATUS_RU,
  money,
  vehicleTitle,
} from "./autoLabels";
import { AutoLogisticsDesk, LogisticsSettingsPanel, VehicleLogisticsBlock } from "./AutoLogisticsDesk";
import { AutoCustomsDesk, CustomsSettingsPanel, VehicleCustomsBlock } from "./AutoCustomsDesk";
import { AutoCrmDesk, AutoReportsDesk, CrmSettingsPanel, VehicleCrmBlock } from "./AutoCrmDesk";
import { AutoAnalyticsDesk } from "./AutoAnalyticsDesk";
import { AutoFinanceDesk } from "./AutoFinanceDesk";
import { AutoDocumentsDesk, DocumentPackageCard, DocumentTemplatesSettings } from "./AutoDocumentsDesk";
import { AutoSystemStatus } from "./AutoSystemStatus";

const NAV: OpsNavItem[] = [
  { id: "overview", label: "Обзор" },
  { id: "vehicles", label: "Автомобили" },
  { id: "purchases", label: "Закупки" },
  { id: "logistics", label: "Логистика" },
  { id: "customs", label: "Растаможка" },
  { id: "clients", label: "Клиенты" },
  { id: "sales", label: "Продажи" },
  { id: "expenses", label: "Платежи и расходы" },
  { id: "documents", label: "Документы" },
  { id: "tasks", label: "CRM и задачи" },
  { id: "telegram", label: "Telegram" },
  { id: "reports", label: "Отчёты" },
  { id: "analytics", label: "Аналитика" },
  { id: "finance", label: "Финансы" },
  { id: "settings", label: "Настройки" },
];

const VIEW_ALIAS: Record<string, string> = {
  home: "overview",
  cars: "vehicles",
  import: "purchases",
  warehouse: "vehicles",
  crm: "tasks",
  analytics: "analytics",
  economy: "analytics",
  cashflow: "finance",
  deals: "sales",
  сделки: "sales",
};

function mapRole(roleId: string): string {
  const r = roleId.toLowerCase();
  if (r.includes("accountant") || r.includes("бухгалтер")) return "auto_accountant";
  if (r.includes("director") || r.includes("директор") || r.includes("owner")) return "auto_director";
  if (r === "admin" || r === "administrator" || r.includes("админ")) return "auto_admin";
  if (r.includes("forwarder") || r.includes("экспедитор")) return "auto_forwarder";
  if (r.includes("customs") || r.includes("тамож") || r.includes("брокер")) return "auto_customs";
  if (r.includes("client") || r.includes("customer") || r.includes("guest")) return "client";
  return "auto_manager";
}

type Rec = Record<string, unknown>;

type Bundle = {
  vehicles: Rec[];
  clients: Rec[];
  expenses: Rec[];
  documents: Rec[];
  photos: Rec[];
  tasks: Rec[];
  audit: Rec[];
  dashboard: Rec;
  catalogs: Rec;
  telegram: Rec;
  settings: Rec;
  reports: Rec;
};

const empty = (): Bundle => ({
  vehicles: [],
  clients: [],
  expenses: [],
  documents: [],
  photos: [],
  tasks: [],
  audit: [],
  dashboard: {},
  catalogs: {},
  telegram: {},
  settings: {},
  reports: {},
});

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="eds-type-caption text-[var(--eds-text-muted)]">{label}</span>
      {children}
    </label>
  );
}

function KpiGrid({ items }: { items: { label: string; value: string }[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5" data-testid="auto-kpi-grid">
      {items.map((c) => (
        <Card key={c.label} className="p-3">
          <p className="eds-type-caption text-[var(--eds-text-muted)]">{c.label}</p>
          <p className="mt-1 eds-type-title text-xl">{c.value}</p>
        </Card>
      ))}
    </div>
  );
}

function DirectorToday({
  headers,
  canFinance,
  onOpenVehicle,
}: {
  headers: Record<string, string>;
  canFinance: boolean;
  onOpenVehicle: (id: string) => void;
}) {
  const [summary, setSummary] = useState<string>("");
  const [risks, setRisks] = useState<Rec[]>([]);
  useEffect(() => {
    void autoOpsGet("/analytics/director", headers).then((res) => {
      const json = (res.json || {}) as Rec;
      setSummary(String(json.summary_ru || ""));
      setRisks(asList(json.risks, ["risks", "items"]) as Rec[]);
    });
  }, [headers]);
  if (!summary) return null;
  return (
    <Card title="На сегодня">
      <p className="eds-type-body" data-testid="auto-director-summary">{summary}</p>
      {canFinance && risks.length ? (
        <ul className="mt-2 space-y-1">
          {risks.slice(0, 6).map((r, i) => (
            <li key={`${r.vehicle_id || r.id}-${i}`}>
              <button className="underline" onClick={() => r.vehicle_id && onOpenVehicle(String(r.vehicle_id))}>
                {String(r.message_ru || "")}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}

function AutoGlobalSearch({ headers, onOpenVehicle }: { headers: Record<string, string>; onOpenVehicle: (id: string) => void }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Rec[]>([]);
  async function run(value: string) {
    setQ(value);
    if (!value.trim()) {
      setHits([]);
      return;
    }
    const res = await autoOpsGet(`/search?q=${encodeURIComponent(value)}`, headers);
    setHits(asList(res.json) as Rec[]);
  }
  return (
    <Card title="Поиск">
      <Input value={q} onChange={(e) => void run(e.target.value)} placeholder="VIN, перевозка, контейнер, BOL, клиент" />
      {hits.length ? (
        <ul className="mt-2 eds-type-helper" data-testid="auto-global-search">
          {hits.slice(0, 10).map((h) => (
            <li key={`${h.kind}-${h.id}`}>
              {h.kind === "vehicle" ? (
                <button className="underline" onClick={() => onOpenVehicle(String(h.id))}>
                  {pick(h, "kind")}: {pick(h, "title")} {pick(h, "extra")}
                </button>
              ) : (
                <span>
                  {pick(h, "kind")}: {pick(h, "title")} {pick(h, "extra")}
                </span>
              )}
            </li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}

export function AutoBusinessPage() {
  const caps = resolveCabinetCaps("auto");
  const organizationId = useOrgSelector((s) => s.organizationId);
  const orgLabel = useOrgSelector((s) => s.label());
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const autoRole = mapRole(activeRoleId);
  const canOperate = caps.canOperate && autoRole !== "client";
  const canCreate =
    canOperate &&
    (autoRole === "auto_director" ||
      autoRole === "auto_manager" ||
      autoRole === "auto_forwarder" ||
      autoRole === "auto_customs" ||
      autoRole === "platform_owner");
  const canFinance = caps.canSeeFinance || autoRole === "auto_accountant" || autoRole === "auto_director";
  const canAdmin = autoRole === "auto_admin" || autoRole === "auto_director" || autoRole === "platform_owner";
  const canLogistics = canCreate && autoRole !== "auto_accountant";
  const canCustoms = canLogistics || autoRole === "auto_customs";

  const [params, setParams] = useSearchParams();
  const rawView = params.get("view") || "overview";
  const view = VIEW_ALIAS[rawView] || rawView;
  const action = params.get("action") || "";
  const vehicleId = params.get("vehicle") || "";

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [bundle, setBundle] = useState<Bundle>(empty);
  const [profile, setProfile] = useState<Rec | null>(null);
  const [tab, setTab] = useState("overview");
  const [showCreate, setShowCreate] = useState(action === "vehicle" || action === "create");

  useEffect(() => {
    if (action === "vehicle" || action === "create") setShowCreate(true);
  }, [action]);

  const headers = useMemo(
    () => ({
      "X-Organization-Id": organizationId,
      "X-Tenant-Id": organizationId,
      "X-Role": autoRole,
      "X-Principal": autoRole,
    }),
    [organizationId, autoRole],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [dash, vehicles, clients, expenses, documents, photos, tasks, audit, catalogs, telegram, settings, reports] =
        await Promise.all([
          autoOpsGet("/dashboard", headers),
          autoOpsGet("/vehicles", headers),
          autoOpsGet("/clients", headers),
          canFinance ? autoOpsGet("/expenses", headers) : Promise.resolve({ ok: true, status: 200, json: { items: [] } }),
          autoOpsGet("/documents", headers),
          autoOpsGet("/photos", headers),
          autoOpsGet("/tasks", headers),
          autoOpsGet("/audit", headers),
          autoOpsGet("/catalogs", headers),
          autoOpsGet("/telegram", headers),
          autoOpsGet("/settings", headers),
          canFinance ? autoOpsGet("/reports", headers) : Promise.resolve({ ok: true, status: 200, json: {} }),
        ]);
      const fail = [dash, vehicles].find((r) => !r.ok);
      if (fail) {
        const j = fail.json as Rec;
        setError(String(j.message_ru || j.error || `HTTP ${fail.status}`));
      }
      setBundle({
        vehicles: asList(vehicles.json) as Rec[],
        clients: asList(clients.json) as Rec[],
        expenses: asList(expenses.json) as Rec[],
        documents: asList(documents.json) as Rec[],
        photos: asList(photos.json) as Rec[],
        tasks: asList(tasks.json) as Rec[],
        audit: asList(audit.json) as Rec[],
        dashboard: (dash.json || {}) as Rec,
        catalogs: ((catalogs.json as Rec)?.catalogs || catalogs.json || {}) as Rec,
        telegram: (telegram.json || {}) as Rec,
        settings: (settings.json || {}) as Rec,
        reports: (reports.json || {}) as Rec,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "network_error");
    } finally {
      setLoading(false);
    }
  }, [headers, canFinance]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (action === "vehicle" || action === "create") setShowCreate(true);
  }, [action]);

  const openVehicle = useCallback(
    async (id: string) => {
      const next = new URLSearchParams(params);
      next.set("view", "vehicles");
      next.set("vehicle", id);
      next.delete("action");
      setParams(next);
      const res = await autoOpsGet(`/vehicles/${id}`, headers);
      if (!res.ok) {
        setMsg(String((res.json as Rec).message_ru || "Не удалось открыть автомобиль"));
        setProfile(null);
        return;
      }
      setProfile(res.json as Rec);
      setTab("overview");
      setShowCreate(false);
    },
    [headers, params, setParams],
  );

  useEffect(() => {
    if (vehicleId) void openVehicle(vehicleId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [vehicleId]);

  async function post(path: string, body: Rec): Promise<boolean> {
    setMsg(null);
    const res = await autoOpsPost(path, body, headers);
    const j = res.json as Rec;
    if (!res.ok || j.ok === false) {
      setMsg(String(j.message_ru || j.error || "Операция не выполнена"));
      return false;
    }
    setMsg(j.warning ? String(j.message_ru || "Сохранено с предупреждением") : "Сохранено");
    await load();
    return true;
  }

  const dash = bundle.dashboard;
  const cards = (dash.cards || {}) as Rec;
  const finance = (dash.finance || {}) as Rec;
  const attention = asList(dash.attention, ["attention"]) as Rec[];

  const filteredVehicles = useCallback(
    (statuses?: string[]) => {
      let rows = bundle.vehicles;
      if (statuses) rows = rows.filter((v) => statuses.includes(String(v.status || "")));
      return rows;
    },
    [bundle.vehicles],
  );

  const vehicleRows = (list: Rec[]) =>
    list.map((v) => ({
      id: String(v.id || ""),
      photo: v.cover_file_id ? "есть" : "—",
      thumb: v.cover_file_id ? autoOpsFileUrl(String(v.cover_file_id)) : "",
      title: vehicleTitle(v),
      vin: pick(v, "vin"),
      year: pick(v, "year"),
      status: STATUS_RU[String(v.status)] || pick(v, "status_ru", "status"),
      location: pick(v, "location_current"),
      purchase: money(v.purchase_price, String(v.purchase_currency || "USD")),
      invested: canFinance ? money(v.invested) : "скрыто",
      client: pick(v, "client_name"),
      manager: pick(v, "assigned_manager_id"),
      docs: `📎 ${Number(v.document_count || 0)}${Number(v.documents_missing || 0) ? ` ⚠ ${v.documents_missing} missing` : ""}`,
      updated: pick(v, "updated_at"),
    }));

  const vehicleSection = (id: string, title: string, description: string, list: Rec[]): OpsSection => ({
    id,
    title,
    description,
    columns: [
      { key: "photo", label: "Фото" },
      { key: "title", label: "Автомобиль" },
      { key: "vin", label: "VIN" },
      { key: "year", label: "Год" },
      { key: "status", label: "Статус" },
      { key: "location", label: "Где находится" },
      { key: "purchase", label: "Цена покупки" },
      { key: "invested", label: "Вложено" },
      { key: "client", label: "Клиент" },
      { key: "manager", label: "Менеджер" },
      { key: "docs", label: "Документы" },
      { key: "updated", label: "Последнее изменение" },
    ],
    rows: vehicleRows(list),
    statusFilterKey: "status",
    thumbKey: "thumb",
    onRowOpen: (row) => void openVehicle(String(row.id)),
    emptyTitle: "Автомобилей пока нет",
    emptyDescription: "Добавьте первый автомобиль по VIN, марке и ссылке на аукцион. Фиктивные записи система не создаёт.",
    emptyCtaLabel: canCreate ? "+ Добавить автомобиль" : undefined,
    emptyCtaOnClick: canCreate ? () => setShowCreate(true) : undefined,
    quickActions: canCreate ? [{ label: "+ Добавить автомобиль", onClick: () => setShowCreate(true) }] : [],
    rowActions: (row) => (
      <Button size="sm" variant="secondary" onClick={() => void openVehicle(String(row.id))}>
        Открыть
      </Button>
    ),
    panel: showCreate || (id === "vehicles" && profile) ? (
      <div className="space-y-4">
        {showCreate ? (
          <VehicleCreateForm
            canCreate={canCreate}
            onCancel={() => setShowCreate(false)}
            onSubmit={async (body) => {
              const ok = await post("/vehicles", body);
              if (ok) setShowCreate(false);
            }}
          />
        ) : null}
        {id === "vehicles" && profile ? (
          <VehicleProfile
            data={profile}
            tab={tab}
            setTab={setTab}
            canCreate={canCreate}
            canFinance={canFinance}
            canOperate={canOperate}
            msg={msg}
            onClose={() => {
              setProfile(null);
              const next = new URLSearchParams(params);
              next.delete("vehicle");
              setParams(next);
            }}
            onReload={() => vehicleId && void openVehicle(vehicleId)}
            onPost={post}
            headers={headers}
            load={load}
          />
        ) : null}
      </div>
    ) : undefined,
  });

  const sections: Record<string, OpsSection> = {
    overview: {
      id: "overview",
      title: "Обзор",
      description: "Что у нас есть, где машины, сколько вложено и что требует внимания.",
      columns: [],
      rows: [],
      panel: (
        <div className="space-y-4" data-testid="auto-overview">
          <AutoGlobalSearch headers={headers} onOpenVehicle={(id) => void openVehicle(id)} />
          <DirectorToday headers={headers} canFinance={canFinance} onOpenVehicle={(id) => void openVehicle(id)} />
          <KpiGrid
            items={Object.entries(CARD_RU).map(([k, label]) => ({
              label,
              value: String(cards[k] ?? 0),
            }))}
          />
          {canFinance && !finance.restricted ? (
            <KpiGrid
              items={Object.entries(FIN_RU).map(([k, label]) => ({
                label,
                value: money(finance[k], String(finance.currency || "USD")),
              }))}
            />
          ) : (
            <p className="eds-type-helper" data-testid="auto-finance-restricted">
              Финансовые KPI видят директор и бухгалтер. Суммы считаются только по фактическим расходам.
            </p>
          )}
          <Card title="Требует внимания">
            {attention.length ? (
              <ul className="space-y-2">
                {attention.map((a) => (
                  <li key={String(a.vehicle_id)}>
                    <button className="text-left underline" onClick={() => void openVehicle(String(a.vehicle_id))}>
                      {String(a.title)} · {String(a.status_ru)}
                    </button>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">{(a.reasons as string[])?.join(" · ")}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="eds-type-helper">Сейчас нет сигналов — либо парк пуст, либо по машинам заполнены ключевые поля.</p>
            )}
          </Card>
        </div>
      ),
    },
    vehicles: vehicleSection("vehicles", "Автомобили", "Рабочий список парка. Поиск по VIN, марке, лоту, клиенту и внутреннему номеру.", bundle.vehicles),
    purchases: vehicleSection("purchases", "Закупки", "Интерес, аукцион, выигрыш и покупка.", filteredVehicles(PURCHASE_STATUSES)),
    logistics: {
      id: "logistics",
      title: "Логистика",
      description: "Операционный стол перевозок: где автомобиль сейчас, контейнер, судно, ETA.",
      columns: [],
      rows: [],
      panel: (
        <AutoLogisticsDesk
          headers={headers}
          canCreate={canLogistics}
          canFinance={canFinance}
          vehicles={bundle.vehicles}
          onOpenVehicle={(id) => void openVehicle(id)}
        />
      ),
    },
    customs: {
      id: "customs",
      title: "Растаможка",
      description: "Операционный стол: где автомобиль, какие документы, сколько платить, кто отвечает.",
      columns: [],
      rows: [],
      panel: (
        <AutoCustomsDesk
          headers={headers}
          canCreate={canCustoms}
          canFinance={canFinance}
          canAdmin={canAdmin}
          vehicles={bundle.vehicles}
          onOpenVehicle={(id) => void openVehicle(id)}
        />
      ),
    },
    clients: {
      id: "clients",
      title: "Клиенты",
      description: "Клиенты и сделки. Кто, какая машина, какой этап, сколько должны.",
      columns: [],
      rows: [],
      panel: (
        <AutoCrmDesk
          headers={headers}
          canCreate={canCreate}
          canFinance={canFinance}
          vehicles={bundle.vehicles}
          clients={bundle.clients}
          initialTab="leads"
          onOpenVehicle={(id) => void openVehicle(id)}
        />
      ),
    },
    sales: {
      id: "sales",
      title: "Продажи",
      description: "Сделки: резерв, депозит, договор, платежи, выдача. Одна сделка — один автомобиль.",
      columns: [],
      rows: [],
      panel: (
        <AutoCrmDesk
          headers={headers}
          canCreate={canCreate}
          canFinance={canFinance}
          vehicles={bundle.vehicles}
          clients={bundle.clients}
          initialTab="paying"
          onOpenVehicle={(id) => void openVehicle(id)}
        />
      ),
    },
    expenses: {
      id: "expenses",
      title: "Платежи и расходы",
      description: "Каждый расход привязан к автомобилю. Итоги считаются только по этим записям.",
      columns: [
        { key: "vehicle", label: "Автомобиль" },
        { key: "category", label: "Категория" },
        { key: "amount", label: "Сумма" },
        { key: "status", label: "Статус оплаты" },
        { key: "date", label: "Дата" },
      ],
      rows: canFinance
        ? bundle.expenses.map((e) => ({
            id: String(e.id || ""),
            vehicle: pick(e, "vehicle_id"),
            category: EXPENSE_RU[String(e.category)] || pick(e, "category"),
            amount: money(e.amount, String(e.currency || "USD")),
            status: pick(e, "payment_status"),
            date: pick(e, "payment_date"),
          }))
        : [],
      emptyTitle: canFinance ? "Расходов пока нет" : "Нет доступа",
      emptyDescription: canFinance
        ? "Добавьте фактический платёж. Система не подставляет примерные суммы."
        : "Платежи и расходы видят директор и бухгалтер.",
      panel: canFinance ? (
        <ExpenseForm vehicles={bundle.vehicles} onSubmit={(body) => post("/expenses", body)} />
      ) : (
        <p className="eds-type-helper">Раздел закрыт для вашей роли.</p>
      ),
    },
    documents: {
      id: "documents",
      title: "Документы",
      description: "Документы автомобиля, клиента, поставки, таможни, продажи или платежа. Не публикуются наружу.",
      columns: [
        { key: "file", label: "Файл" },
        { key: "type", label: "Тип" },
        { key: "owner", label: "Привязка" },
        { key: "vehicle", label: "Авто" },
      ],
      rows: bundle.documents.map((d) => ({
        id: String(d.id || ""),
        file: pick(d, "file_name", "title"),
        type: DOC_RU[String(d.document_type)] || pick(d, "document_type"),
        owner: pick(d, "owner_type"),
        vehicle: pick(d, "vehicle_id"),
      })),
      emptyTitle: "Документов пока нет",
      emptyDescription: "Загрузите инвойс, title, B/L или договор и привяжите к автомобилю.",
      panel: (
        <div className="space-y-4">
          <AutoDocumentsDesk headers={headers} vehicles={bundle.vehicles} canCreate={canCreate} onDone={load} />
          <DocumentUpload vehicles={bundle.vehicles} headers={headers} onDone={load} setMsg={setMsg} />
        </div>
      ),
    },
    tasks: {
      id: "tasks",
      title: "CRM и задачи",
      description: "Задачи по автомобилям и клиентам. CRM контактов — в разделе Клиенты.",
      columns: [
        { key: "title", label: "Задача" },
        { key: "status", label: "Статус" },
        { key: "vehicle", label: "Авто" },
        { key: "due", label: "Срок" },
      ],
      rows: bundle.tasks.map((t) => ({
        id: String(t.id || ""),
        title: pick(t, "title"),
        status: pick(t, "status"),
        vehicle: pick(t, "vehicle_id"),
        due: pick(t, "due_at"),
      })),
      emptyTitle: "Задач пока нет",
      emptyDescription: "Создайте задачу и привяжите её к автомобилю.",
      panel: canCreate ? <TaskForm vehicles={bundle.vehicles} onSubmit={(body) => post("/tasks", body)} /> : undefined,
    },
    telegram: {
      id: "telegram",
      title: "Telegram",
      description: "Команды Авто в существующем боте ADOS. Новый бот не строится.",
      columns: [],
      rows: [],
      panel: (
        <div data-testid="auto-telegram">
        <Card>
          <p className="eds-type-body">{String(bundle.telegram.message_ru || "Команды Авто включены в существующем боте ADOS. Новый бот не строится.")}</p>
          <p className="mt-2 eds-type-helper">
            Статус: {String(bundle.telegram.status || "live")} · Реализация: {bundle.telegram.implemented ? "сотрудники (закрытый канал)" : "нет"}
          </p>
          <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
            Живые команды для авторизованных сотрудников: /auto, /vin, /logistics, /customs, /client, /deal, /expense, /pay, /task, /photo, /doc, /reserve, /report. Новый бот не строится.
          </p>
        </Card>
        </div>
      ),
    },
    reports: {
      id: "reports",
      title: "Отчёты",
      description: "Сводка по фактическим записям. Пустые цифры — отсутствие данных, не «ноль рынка».",
      columns: [],
      rows: [],
      panel: <AutoReportsDesk headers={headers} canFinance={canFinance} />,
    },
    analytics: {
      id: "analytics",
      title: "Аналитика",
      description: "Экономика автомобилей, продажи, менеджеры, логистика и воронка. Только фактические записи.",
      columns: [],
      rows: [],
      panel: (
        <AutoAnalyticsDesk
          headers={headers}
          canFinance={canFinance}
          onOpenVehicle={(id) => void openVehicle(id)}
        />
      ),
    },
    finance: {
      id: "finance",
      title: "Финансы",
      description: "Сводка, cash flow, дебиторка и счета учёта. Стартовый остаток не выдумывается.",
      columns: [],
      rows: [],
      panel: (
        <AutoFinanceDesk
          headers={headers}
          canFinance={canFinance}
          canWrite={canFinance}
          onOpenVehicle={(id) => void openVehicle(id)}
        />
      ),
    },
    settings: {
      id: "settings",
      title: "Настройки",
      description: "Компания, роли, статусы, категории, документы, логистика, Telegram и техническое состояние.",
      columns: [],
      rows: [],
      panel: <SettingsPanel settings={bundle.settings} catalogs={bundle.catalogs} canAdmin={canAdmin} orgLabel={orgLabel} headers={headers} canCreate={canCreate} />,
    },
  };

  return (
    <>
      <BusinessCabinetShell
        verticalId="auto"
        title="Авто"
        subtitle="Закрытая операционная система импорта и продажи автомобилей компании"
        nav={NAV.map((item) => ({
          ...item,
          hidden:
            Boolean(item.hidden) ||
            ((item.id === "finance" || item.id === "expenses" || item.id === "reports") && !canFinance) ||
            (item.id === "settings" && !canAdmin),
        }))}
        sections={sections}
        defaultSection="overview"
        loading={loading}
        error={error}
        onRefresh={() => void load()}
        testId="auto-business-cabinet"
        roleHint={`${ROLE_RU[autoRole] || autoRole} · ${orgLabel}`}
      />
      {msg ? (
        <p className="px-4 eds-type-helper" data-testid="auto-form-msg">
          {msg}
        </p>
      ) : null}
    </>
  );
}

function VehicleCreateForm({
  canCreate,
  onCancel,
  onSubmit,
}: {
  canCreate: boolean;
  onCancel: () => void;
  onSubmit: (body: Rec) => Promise<void>;
}) {
  const [form, setForm] = useState({
    vin: "",
    manufacturer: "",
    model: "",
    year: "",
    trim: "",
    mileage: "",
    exterior_color: "",
    purchase_country: "",
    auction_name: "",
    auction_lot: "",
    auction_url: "",
    purchase_date: "",
    purchase_price: "",
    purchase_currency: "USD",
    buyer_fee: "",
    location_current: "",
    origin_port: "",
    destination_port: "",
    assigned_manager_id: "",
  });
  if (!canCreate) return <p className="eds-type-helper">Создание автомобилей недоступно для вашей роли.</p>;
  function set(k: string, v: string) {
    setForm((s) => ({ ...s, [k]: v }));
  }
  return (
        <Card title="Добавить автомобиль">
          <div data-testid="auto-vehicle-create">
      <form
        className="space-y-4"
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          const body: Rec = { ...form };
          Object.keys(body).forEach((k) => {
            if (body[k] === "") delete body[k];
          });
          void onSubmit(body);
        }}
      >
        <p className="eds-type-helper">Обязательно: VIN. Для быстрого старта достаточно ещё марки/модели или ссылки на аукцион.</p>
        <h3 className="eds-type-section">Основное</h3>
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="VIN"><Input value={form.vin} onChange={(e) => set("vin", e.target.value)} required /></Field>
          <Field label="Марка"><Input value={form.manufacturer} onChange={(e) => set("manufacturer", e.target.value)} /></Field>
          <Field label="Модель"><Input value={form.model} onChange={(e) => set("model", e.target.value)} /></Field>
          <Field label="Год"><Input value={form.year} onChange={(e) => set("year", e.target.value)} /></Field>
          <Field label="Комплектация"><Input value={form.trim} onChange={(e) => set("trim", e.target.value)} /></Field>
          <Field label="Пробег"><Input value={form.mileage} onChange={(e) => set("mileage", e.target.value)} /></Field>
          <Field label="Цвет"><Input value={form.exterior_color} onChange={(e) => set("exterior_color", e.target.value)} /></Field>
        </div>
        <h3 className="eds-type-section">Покупка</h3>
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="Страна"><Input value={form.purchase_country} onChange={(e) => set("purchase_country", e.target.value)} /></Field>
          <Field label="Аукцион"><Input value={form.auction_name} onChange={(e) => set("auction_name", e.target.value)} /></Field>
          <Field label="Номер лота"><Input value={form.auction_lot} onChange={(e) => set("auction_lot", e.target.value)} /></Field>
          <Field label="Ссылка на автомобиль"><Input value={form.auction_url} onChange={(e) => set("auction_url", e.target.value)} /></Field>
          <Field label="Дата покупки"><Input type="date" value={form.purchase_date} onChange={(e) => set("purchase_date", e.target.value)} /></Field>
          <Field label="Цена покупки"><Input value={form.purchase_price} onChange={(e) => set("purchase_price", e.target.value)} /></Field>
          <Field label="Валюта"><Input value={form.purchase_currency} onChange={(e) => set("purchase_currency", e.target.value)} /></Field>
          <Field label="Комиссия аукциона"><Input value={form.buyer_fee} onChange={(e) => set("buyer_fee", e.target.value)} /></Field>
        </div>
        <h3 className="eds-type-section">Логистика</h3>
        <div className="grid gap-3 md:grid-cols-3">
          <Field label="Текущее местоположение"><Input value={form.location_current} onChange={(e) => set("location_current", e.target.value)} /></Field>
          <Field label="Порт отправления"><Input value={form.origin_port} onChange={(e) => set("origin_port", e.target.value)} /></Field>
          <Field label="Порт назначения"><Input value={form.destination_port} onChange={(e) => set("destination_port", e.target.value)} /></Field>
        </div>
        <h3 className="eds-type-section">Ответственный</h3>
        <Field label="Менеджер"><Input value={form.assigned_manager_id} onChange={(e) => set("assigned_manager_id", e.target.value)} /></Field>
        <div className="flex gap-2">
          <Button type="submit" className="ews-primary-cta">Сохранить</Button>
          <Button type="button" variant="secondary" onClick={onCancel}>Отмена</Button>
        </div>
      </form>
        </div>
    </Card>
  );
}

const PROFILE_TABS = [
  ["overview", "Обзор"],
  ["purchase", "Покупка"],
  ["logistics", "Логистика"],
  ["customs", "Таможня"],
  ["sale", "Клиент / продажа"],
  ["sale_package", "Пакет продажи"],
  ["registration", "Регистрация"],
  ["finance", "Финансы"],
  ["documents", "Документы"],
  ["photos", "Фото"],
  ["tasks", "Задачи"],
  ["history", "История"],
] as const;

function VehicleProfile({
  data,
  tab,
  setTab,
  canCreate,
  canFinance,
  canOperate,
  msg,
  onClose,
  onReload,
  onPost,
  headers,
  load,
}: {
  data: Rec;
  tab: string;
  setTab: (t: string) => void;
  canCreate: boolean;
  canFinance: boolean;
  canOperate: boolean;
  msg: string | null;
  onClose: () => void;
  onReload: () => void;
  onPost: (path: string, body: Rec) => Promise<boolean>;
  headers: Record<string, string>;
  load: () => Promise<void>;
}) {
  const item = (data.item || {}) as Rec;
  const lifecycle = asList(data.lifecycle || item.lifecycle, ["lifecycle"]) as Rec[];
  const finance = (data.finance || {}) as Rec;
  const photos = asList(data.photos) as Rec[];
  const docs = asList(data.documents) as Rec[];
  const tasks = asList(data.tasks) as Rec[];
  const audit = asList(data.audit) as Rec[];
  const salePack = (data.sale_package || null) as Rec | null;
  const regPack = (data.registration_package || null) as Rec | null;
  const vid = String(item.id || "");
  const [status, setStatus] = useState(String(item.status || "INTEREST"));
  const [salePrice, setSalePrice] = useState(String(item.sale_price_expected || ""));
  const cover = item.cover_file_id ? autoOpsFileUrl(String(item.cover_file_id)) : "";

  return (
    <div data-testid="auto-vehicle-profile">
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex gap-3">
          {cover ? <img src={cover} alt="" className="h-20 w-28 rounded object-cover" /> : <div className="flex h-20 w-28 items-center justify-center rounded border eds-type-caption">Нет фото</div>}
          <div>
            <h3 className="eds-type-title text-xl">{vehicleTitle(item)}</h3>
            <p className="eds-type-helper">VIN: {String(item.vin)}</p>
            <p className="eds-type-helper">Статус: {STATUS_RU[String(item.status)] || String(item.status)}</p>
            <p className="eds-type-helper">Менеджер: {String(item.assigned_manager_id || "—")} · Где: {String(item.location_current || "—")}</p>
          </div>
        </div>
        <Button variant="secondary" onClick={onClose}>Закрыть</Button>
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {PROFILE_TABS.map(([id, label]) => (
          <Button key={id} size="sm" variant={tab === id ? undefined : "secondary"} onClick={() => setTab(id)}>
            {label}
          </Button>
        ))}
      </div>
      <div className="mt-4 space-y-3">
        {tab === "overview" ? (
          <ol className="flex flex-wrap items-center gap-2" data-testid="auto-lifecycle">
            {lifecycle.map((step, i) => (
              <li key={String(step.id)} className="flex items-center gap-2">
                <span
                  className={
                    step.state === "current"
                      ? "rounded bg-[var(--eds-primary)] px-2 py-1 text-white"
                      : step.state === "done"
                        ? "rounded bg-[var(--eds-success-soft,#dcfce7)] px-2 py-1"
                        : "rounded border px-2 py-1 text-[var(--eds-text-muted)]"
                  }
                >
                  {String(step.label_ru)}
                </span>
                {i < lifecycle.length - 1 ? <span>↓</span> : null}
              </li>
            ))}
          </ol>
        ) : null}
        {tab === "purchase" ? (
          <dl className="grid gap-2 md:grid-cols-2">
            <Info k="Страна" v={item.purchase_country} />
            <Info k="Аукцион" v={item.auction_name} />
            <Info k="Лот" v={item.auction_lot} />
            <Info k="Ссылка" v={item.auction_url} />
            <Info k="Дата" v={item.purchase_date} />
            <Info k="Цена" v={money(item.purchase_price, String(item.purchase_currency || "USD"))} />
            <Info k="Комиссия" v={money(item.buyer_fee, String(item.purchase_currency || "USD"))} />
          </dl>
        ) : null}
        {tab === "logistics" ? (
          <VehicleLogisticsBlock logistics={(data.logistics || {}) as Rec} canFinance={canFinance} />
        ) : null}
        {tab === "customs" ? <VehicleCustomsBlock customs={(data.customs || {}) as Rec} canFinance={canFinance} /> : null}
        {tab === "sale" ? (
          <div className="space-y-2">
            <VehicleCrmBlock crm={(data.crm || {}) as Rec} />
            <Info k="Клиент" v={(data.client as Rec | undefined)?.name || item.client_name} />
            <Field label="Ожидаемая цена продажи">
              <Input value={salePrice} onChange={(e) => setSalePrice(e.target.value)} />
            </Field>
            {canCreate ? (
              <Button
                size="sm"
                onClick={() => void onPost(`/vehicles/${vid}`, { sale_price_expected: salePrice })}
              >
                Сохранить цену
              </Button>
            ) : null}
          </div>
        ) : null}
        {tab === "sale_package" ? <DocumentPackageCard title="Пакет продажи" pack={salePack} /> : null}
        {tab === "registration" ? <DocumentPackageCard title="Регистрация" pack={regPack} /> : null}
        {tab === "finance" ? (
          finance.restricted ? (
            <p className="eds-type-helper">Финансы доступны директору и бухгалтеру.</p>
          ) : (
            <div data-testid="auto-vehicle-finance">
              {(asList(finance.lines) as Rec[]).length ? (
                <ul className="space-y-1">
                  {(asList(finance.lines) as Rec[]).map((l) => (
                    <li key={String(l.id)} className="flex justify-between border-b py-1">
                      <span>{String(l.label_ru)} {l.has_document === false ? "⚠ Документ отсутствует" : ""}</span>
                      <span>{money(l.amount_base_currency)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="eds-type-helper">Расходов по этой машине ещё нет — себестоимость не считается.</p>
              )}
              <p className="mt-3 font-medium">Себестоимость {money(finance.cost)}</p>
              {finance.landed ? (
                <div className="mt-3" data-testid="auto-landed-cost">
                  <p className="font-medium">Landed cost {money((finance.landed as Rec).landed_cost)}</p>
                  <ul className="eds-type-caption">
                    {Object.entries(((finance.landed as Rec).lines || {}) as Rec).map(([k, v]) => (
                      <li key={k}>{k}: {money(v)}</li>
                    ))}
                  </ul>
                  <p>Продажные затраты {money((finance.landed as Rec).selling_costs)}</p>
                  {finance.actual_profit != null ? <p>Фактическая прибыль {money(finance.actual_profit)}</p> : <p className="eds-type-helper">Фактическая прибыль считается только для проданных авто.</p>}
                </div>
              ) : null}
              <p>Цена продажи {money(finance.sale_price_actual ?? finance.sale_price_expected)}</p>
              <p>Прибыль {money(finance.profit_actual ?? finance.profit_expected)}</p>
            </div>
          )
        ) : null}
        {tab === "documents" ? (
          <ul>
            {docs.map((d) => (
              <li key={String(d.id)}>{pick(d, "file_name", "title")} · {DOC_RU[String(d.document_type)] || String(d.document_type)}</li>
            ))}
            {!docs.length ? <p className="eds-type-helper">Документов нет.</p> : null}
          </ul>
        ) : null}
        {tab === "photos" ? (
          <PhotoGallery
            photos={photos}
            vehicleId={vid}
            headers={headers}
            canOperate={canOperate}
            onDone={async () => {
              await load();
              onReload();
            }}
          />
        ) : null}
        {tab === "tasks" ? (
          <ul>
            {tasks.map((t) => (
              <li key={String(t.id)}>{pick(t, "title")} · {pick(t, "status")}</li>
            ))}
            {!tasks.length ? <p className="eds-type-helper">Задач нет.</p> : null}
          </ul>
        ) : null}
        {tab === "history" ? (
          <ul data-testid="auto-vehicle-audit">
            {audit.map((a) => (
              <li key={String(a.id)} className="eds-type-helper">
                {pick(a, "created_at")} · {pick(a, "action")} · {pick(a, "actor_role")}
              </li>
            ))}
            {!audit.length ? <p className="eds-type-helper">История пуста.</p> : null}
          </ul>
        ) : null}
        {canCreate && tab === "overview" ? (
          <div className="flex flex-wrap items-end gap-2">
            <Field label="Сменить статус">
              <select className="eds-input w-full rounded border px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
                {Object.entries(STATUS_RU).map(([id, label]) => (
                  <option key={id} value={id}>{label}</option>
                ))}
              </select>
            </Field>
            <Button onClick={() => void onPost(`/vehicles/${vid}`, { status })}>Обновить статус</Button>
          </div>
        ) : null}
      </div>
      {msg ? <p className="mt-2 eds-type-helper">{msg}</p> : null}
    </Card>
    </div>
  );
}

function Info({ k, v }: { k: string; v: unknown }) {
  return (
    <div>
      <dt className="eds-type-caption text-[var(--eds-text-muted)]">{k}</dt>
      <dd>{v == null || v === "" ? "—" : String(v)}</dd>
    </div>
  );
}

function ClientForm({ onSubmit }: { onSubmit: (body: Rec) => Promise<boolean> }) {
  const [form, setForm] = useState({ name: "", phone: "", telegram: "", email: "", source: "", assigned_manager_id: "", tax_number: "", passport: "", address: "", representative: "" });
  return (
    <Card title="Добавить клиента">
      <form
        className="grid gap-3 md:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void onSubmit(form);
        }}
      >
        <Field label="Имя"><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></Field>
        <Field label="Телефон"><Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></Field>
        <Field label="Telegram"><Input value={form.telegram} onChange={(e) => setForm({ ...form, telegram: e.target.value })} /></Field>
        <Field label="Email"><Input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
        <Field label="Источник"><Input value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} /></Field>
        <Field label="ИНН"><Input value={form.tax_number} onChange={(e) => setForm({ ...form, tax_number: e.target.value })} /></Field>
        <Field label="Паспорт / ID"><Input value={form.passport} onChange={(e) => setForm({ ...form, passport: e.target.value })} /></Field>
        <Field label="Адрес"><Input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></Field>
        <Field label="Представитель"><Input value={form.representative} onChange={(e) => setForm({ ...form, representative: e.target.value })} /></Field>
        <Button type="submit">Сохранить</Button>
      </form>
    </Card>
  );
}

function ExpenseForm({ vehicles, onSubmit }: { vehicles: Rec[]; onSubmit: (body: Rec) => Promise<boolean> }) {
  const [form, setForm] = useState({ vehicle_id: "", category: "PURCHASE", amount: "", currency: "USD", description: "" });
  if (!vehicles.length) return <p className="eds-type-helper">Сначала добавьте автомобиль — расход без машины создать нельзя.</p>;
  return (
    <Card title="Добавить расход">
      <form
        className="grid gap-3 md:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void onSubmit({ ...form, amount: Number(form.amount) });
        }}
      >
        <Field label="Автомобиль">
          <select className="eds-input w-full rounded border px-2 py-1" value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} required>
            <option value="">Выберите</option>
            {vehicles.map((v) => (
              <option key={String(v.id)} value={String(v.id)}>{vehicleTitle(v)}</option>
            ))}
          </select>
        </Field>
        <Field label="Категория">
          <select className="eds-input w-full rounded border px-2 py-1" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {Object.entries(EXPENSE_RU).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </select>
        </Field>
        <Field label="Сумма"><Input value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} required /></Field>
        <Field label="Валюта"><Input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} /></Field>
        <Field label="Описание"><Input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
        <Button type="submit">Сохранить расход</Button>
      </form>
    </Card>
  );
}

function TaskForm({ vehicles, onSubmit }: { vehicles: Rec[]; onSubmit: (body: Rec) => Promise<boolean> }) {
  const [form, setForm] = useState({ title: "", vehicle_id: "", due_at: "" });
  return (
    <Card title="Новая задача">
      <form
        className="grid gap-3 md:grid-cols-3"
        onSubmit={(e) => {
          e.preventDefault();
          void onSubmit(form);
        }}
      >
        <Field label="Название"><Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required /></Field>
        <Field label="Автомобиль">
          <select className="eds-input w-full rounded border px-2 py-1" value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}>
            <option value="">Без привязки</option>
            {vehicles.map((v) => (
              <option key={String(v.id)} value={String(v.id)}>{vehicleTitle(v)}</option>
            ))}
          </select>
        </Field>
        <Field label="Срок"><Input type="date" value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} /></Field>
        <Button type="submit">Создать задачу</Button>
      </form>
    </Card>
  );
}

function DocumentUpload({
  vehicles,
  headers,
  onDone,
  setMsg,
}: {
  vehicles: Rec[];
  headers: Record<string, string>;
  onDone: () => Promise<void>;
  setMsg: (s: string | null) => void;
}) {
  const [vehicleId, setVehicleId] = useState("");
  const [docType, setDocType] = useState("auction_invoice");
  const [docNumber, setDocNumber] = useState("");
  const [issuedBy, setIssuedBy] = useState("");
  const [issuedDate, setIssuedDate] = useState("");
  const [validUntil, setValidUntil] = useState("");
  return (
    <Card title="Загрузить документ">
      <div className="grid gap-3 md:grid-cols-3">
        <Field label="Автомобиль">
          <select className="eds-input w-full rounded border px-2 py-1" value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
            <option value="">Выберите</option>
            {vehicles.map((v) => (
              <option key={String(v.id)} value={String(v.id)}>{vehicleTitle(v)}</option>
            ))}
          </select>
        </Field>
        <Field label="Тип">
          <select className="eds-input w-full rounded border px-2 py-1" value={docType} onChange={(e) => setDocType(e.target.value)}>
            {Object.entries(DOC_RU).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </select>
        </Field>
        <Field label="Номер"><Input value={docNumber} onChange={(e) => setDocNumber(e.target.value)} /></Field>
        <Field label="Кем выдан"><Input value={issuedBy} onChange={(e) => setIssuedBy(e.target.value)} /></Field>
        <Field label="Дата"><Input type="date" value={issuedDate} onChange={(e) => setIssuedDate(e.target.value)} /></Field>
        <Field label="Действует до"><Input type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} /></Field>
        <Field label="Файл">
          <input
            type="file"
            accept="image/*,application/pdf,.pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,application/msword"
            data-testid="auto-document-file"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              if (!vehicleId) {
                setMsg("Сначала выберите автомобиль");
                return;
              }
              const res = await autoOpsUpload("/files", file, { entity_type: "vehicle", entity_id: vehicleId, document_type: docType }, headers);
              const j = res.json as Rec;
              if (!res.ok || j.ok === false) setMsg(String(j.message_ru || "Загрузка не удалась"));
              else {
                const linked = (j.linked || {}) as Rec;
                if (linked.id && (docNumber || issuedBy || issuedDate || validUntil)) {
                  await autoOpsPost(`/documents/${String(linked.id)}`, {
                    document_number: docNumber,
                    issued_by: issuedBy,
                    issued_date: issuedDate,
                    valid_until: validUntil,
                  }, headers);
                }
                setMsg(j.warning ? String(j.message_ru) : "Документ загружен");
                await onDone();
              }
            }}
          />
        </Field>
      </div>
    </Card>
  );
}

function PhotoGallery({
  photos,
  vehicleId,
  headers,
  canOperate,
  onDone,
}: {
  photos: Rec[];
  vehicleId: string;
  headers: Record<string, string>;
  canOperate: boolean;
  onDone: () => Promise<void>;
}) {
  const [category, setCategory] = useState("AUCTION");
  const [progress, setProgress] = useState<number | null>(null);
  return (
    <div data-testid="auto-photo-gallery">
      <div className="flex flex-wrap gap-3">
        {photos.map((p) => (
          <div key={String(p.id)} className="w-36">
            <img
              src={autoOpsFileUrl(String(p.file_id))}
              alt=""
              className="h-24 w-36 rounded object-cover"
              loading="lazy"
              width={144}
              height={96}
            />
            <p className="eds-type-caption">{PHOTO_RU[String(p.category)] || String(p.category)}</p>
            {canOperate ? (
              <div className="flex gap-1">
                <Button size="sm" variant="secondary" onClick={() => void autoOpsPost(`/photos/${p.id}/cover`, {}, headers).then(onDone)}>
                  Обложка
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => void autoOpsDelete(`/photos/${p.id}`, headers).then(onDone)}
                >
                  Удалить
                </Button>
              </div>
            ) : null}
          </div>
        ))}
      </div>
      {!photos.length ? <p className="eds-type-helper">Фотографий нет.</p> : null}
      {progress != null ? (
        <p className="mt-2 eds-type-caption" data-testid="auto-upload-progress">
          Загрузка {progress}%
        </p>
      ) : null}
      {canOperate ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <select className="rounded border px-2 py-1" value={category} onChange={(e) => setCategory(e.target.value)}>
            {Object.entries(PHOTO_RU).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </select>
          <input
            type="file"
            accept="image/*"
            multiple
            data-testid="auto-photo-file"
            onChange={async (e) => {
              const files = Array.from(e.target.files || []);
              for (const file of files) {
                setProgress(0);
                await autoOpsUpload(
                  "/files",
                  file,
                  { entity_type: "vehicle", entity_id: vehicleId, as_photo: "1", photo_category: category },
                  headers,
                  setProgress,
                );
              }
              setProgress(null);
              await onDone();
            }}
          />
        </div>
      ) : null}
    </div>
  );
}

function TelegramBotStatusPanel({ headers, canAdmin }: { headers: Record<string, string>; canAdmin: boolean }) {
  const [status, setStatus] = useState<Rec | null>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    if (!canAdmin) return;
    void autoOpsGet("/telegram/status", headers).then((r) => {
      if (r.status === 403) {
        setDenied(true);
        return;
      }
      if (r.ok) setStatus((r.json || {}) as Rec);
    });
  }, [canAdmin, headers]);

  if (!canAdmin) {
    return <p className="eds-type-helper">Статус бота доступен администратору и директору.</p>;
  }
  if (denied) {
    return <p className="eds-type-helper">Недостаточно прав для статуса бота.</p>;
  }
  if (!status) {
    return <p className="eds-type-helper">Загрузка статуса бота…</p>;
  }
  const users = asList(status.authorized_users) as Rec[];
  return (
    <div className="mt-3 space-y-1" data-testid="auto-telegram-bot-status">
      <p>Режим: {String(status.mode || "polling")}</p>
      <p>Последнее успешное обновление: {String(status.last_successful_update || "—")}</p>
      <p>Последняя ошибка: {String(status.last_error || "нет")}</p>
      <p>Авторизованных сотрудников: {String(status.authorized_count ?? users.length)}</p>
      <p>Уведомлений сегодня: {String(status.notifications_sent_today ?? 0)}</p>
      {users.length ? (
        <ul className="eds-type-helper">
          {users.map((u) => (
            <li key={String(u.telegram_id)}>
              {String(u.label || u.telegram_id)} · {String(u.role || "")}
            </li>
          ))}
        </ul>
      ) : (
        <p className="eds-type-helper">Сотрудники ещё не привязаны.</p>
      )}
    </div>
  );
}

function SettingsPanel({ settings, catalogs, canAdmin, orgLabel, headers, canCreate }: { settings: Rec; catalogs: Rec; canAdmin: boolean; orgLabel: string; headers: Record<string, string>; canCreate: boolean }) {
  const statuses = asList(catalogs.vehicle_statuses) as Rec[];
  const expenses = asList(catalogs.expense_categories) as Rec[];
  return (
    <div className="space-y-4" data-testid="auto-settings">
      <Card title="Компания">
        <p>{orgLabel}</p>
        <p className="eds-type-helper">Рабочее пространство закрытое. Публичных VIN/клиентских маршрутов нет.</p>
      </Card>
      <Card title="Пользователи и роли">
        <ul>
          {(asList(settings.roles) as Rec[]).map((r) => (
            <li key={String(r.id)}>{String(r.label_ru)} · {String(r.id)}</li>
          ))}
        </ul>
      </Card>
      <Card title="Статусы автомобилей">
        <p className="eds-type-helper">Контролируемый справочник. Свободный текст запрещён.</p>
        <p>{statuses.map((s) => String(s.label_ru)).join(" · ")}</p>
      </Card>
      <Card title="Категории расходов">
        <p>{expenses.map((s) => String(s.label_ru)).join(" · ")}</p>
      </Card>
      <Card title="Документы / Логистика / Валюты / Справочники">
        <p className="eds-type-helper">Типы документов, порты и валюты задаются справочниками. Live AIS не подключён.</p>
        <p>Валюты: {(asList(catalogs.currencies) as unknown[]).join(", ") || "USD, EUR, UAH, GEL"}</p>
      </Card>
      <DocumentTemplatesSettings headers={headers} canAdmin={canAdmin} />
      <LogisticsSettingsPanel catalogs={catalogs} canAdmin={canAdmin} headers={headers} />
      <CustomsSettingsPanel catalogs={catalogs} canAdmin={canAdmin} headers={headers} canCreate={canCreate} />
      <CrmSettingsPanel headers={headers} canCreate={canCreate} />
      {canCreate ? (
        <>
        <Card title="Демо-сценарий AUTO 1.1">
          <p className="eds-type-helper">Создаёт явно помеченный DEMO BMW X5 USA → контейнер → судно → Одесса. Не смешивается с продакшен-записями без confirm_demo.</p>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void autoOpsPost("/logistics/demo", { confirm_demo: true }, headers)}
          >
            Создать демо-перевозку
          </Button>
        </Card>
        <Card title="Демо-сценарий AUTO 1.5">
          <p className="eds-type-helper">Создаёт 10 явно помеченных DEMO автомобилей по этапам цикла. Не смешивается с продакшеном без confirm_demo.</p>
          <Button size="sm" variant="secondary" onClick={() => void autoOpsPost("/analytics/demo", { confirm_demo: true }, headers)}>
            Создать DEMO аналитики
          </Button>
        </Card>
        </>
      ) : null}
      <Card title="Telegram">
        <p>Команды Авто включены в существующем боте ADOS. Новый бот не строится.</p>
        <TelegramBotStatusPanel headers={headers} canAdmin={canAdmin} />
      </Card>
      <Card title="Уведомления">
        <p className="eds-type-helper">Утренняя и вечерняя сводка, события по авто уходят авторизованным сотрудникам в существующий бот. Новый бот не строится.</p>
      </Card>
      <Card title="Интеграции">
        <p className="eds-type-helper">Аукционы, брокеры и трекинг не подключены. Статус не выдаётся за live.</p>
      </Card>
      {canAdmin ? (
        <div data-testid="auto-settings-tech">
        <AutoSystemStatus headers={headers} />
        <Card title="Техническое состояние">
          <p>API: /api/auto-ops/v1</p>
          <p>Persistence: postgres + memory fallback</p>
          <p>Public routes: нет</p>
        </Card>
        </div>
      ) : (
        <p className="eds-type-helper">Технический раздел доступен администратору.</p>
      )}
    </div>
  );
}
