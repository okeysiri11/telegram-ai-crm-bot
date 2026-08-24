/**
 * AGRO Production 1.0 — practical agribusiness workspace.
 * Extends existing agro vertical via /api/agro-ops/v1. No fake market data.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { Button, Card, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { BusinessCabinetShell, type OpsNavItem, type OpsSection } from "../business-ops/BusinessCabinetShell";
import { asList, agroOpsBootstrap, agroOpsFileUrl, agroOpsGet, agroOpsPost, agroOpsUpload, pick } from "../business-ops/opsApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";
import { LawyerConfirm, LawyerRowMenu } from "../legal/LawyerRowMenu";
import { AgroDossierDrawer } from "./AgroDossierDrawer";
import { AgroCrmList } from "./AgroCrmList";
import { AgroCounterparty360 } from "./AgroCounterparty360";
import { AgroDeal360 } from "./AgroDeal360";
import { AgroOperationsList } from "./AgroOperationsList";
import { AgroOperation360 } from "./AgroOperation360";
import { AgroProductionPage } from "./AgroProductionPage";
import { AgroAnalyticsPanel } from "./AgroAnalyticsPanel";
import { AgroIntelPanel } from "./AgroIntelPanel";
import { AgroLogisticsPanel } from "./AgroLogisticsPanel";
import { AgroMarketsPanel } from "./AgroMarketsPanel";
import { AgroOpsDrawer } from "./AgroOpsDrawer";
import { AgroCalendarPanel } from "./AgroCalendarPanel";
import { AgroCropsPanel } from "./AgroCropsPanel";
import {
  AgroCropsCatalog26,
  AgroHarvestPage,
  AgroMachinery26Page,
  AgroSowingsPage,
  AgroWorksPage,
} from "./AgroOps26Modules";
import { AgroDeliveriesPanel } from "./AgroDeliveriesPanel";
import { AgroNotificationsPanel } from "./AgroNotificationsPanel";
import { AgroSettingsPanel } from "./AgroSettingsPanel";
import { AgroWarehousePanel } from "./AgroWarehousePanel";
import { AgroWeatherPanel } from "./AgroWeatherPanel";
import { AgroCommandCenter, AgroManagementReport, type CommandCenterPayload } from "./AgroCommandCenter";
import { AgroQuickCreateSheet } from "./AgroQuickCreateSheet";
import { AgroGlobalSearch } from "./AgroGlobalSearch";
import {
  CP_TYPES,
  DEAL_PIPELINE,
  DEAL_STATUSES,
  dealPipelineId,
  DOC_TYPES,
  ENTITY_TYPES,
  ROLE_RU,
  ru,
  ruStatus,
} from "./agroLabels";
import { AGRO_OPS_NAV } from "./agroOpsNav";

const NAV: OpsNavItem[] = AGRO_OPS_NAV;

function mapRole(roleId: string): string {
  const r = roleId.toLowerCase();
  if (r.includes("accountant") || r.includes("бухгалтер")) return "agro_accountant";
  if (r.includes("quality") || r.includes("качеств") || r.includes("лаборат")) return "agro_quality";
  if (r.includes("logistics") || r.includes("логист")) return "agro_logistics";
  if (r.includes("warehouse") || r.includes("склад")) return "agro_warehouse";
  if (r.includes("viewer") || r.includes("agro_viewer")) return "agro_viewer";
  if (r.includes("observer") || r.includes("наблюдатель")) return "agro_observer";
  if (r.includes("director") || r.includes("директор") || r.includes("owner") || r.includes("admin")) return "agro_director";
  return "agro_manager";
}

type Bundle = {
  counterparties: Record<string, unknown>[];
  contacts: Record<string, unknown>[];
  deals: Record<string, unknown>[];
  contracts: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  calculations: Record<string, unknown>[];
  invoices: Record<string, unknown>[];
  payments: Record<string, unknown>[];
  shipments: Record<string, unknown>[];
  warehouses: Record<string, unknown>[];
  crops: Record<string, unknown>[];
  tasks: Record<string, unknown>[];
  calendar: Record<string, unknown>[];
  markets: Record<string, unknown>[];
  notifications: Record<string, unknown>[];
  files: Record<string, unknown>[];
  dashboard: Record<string, unknown>;
  finance: Record<string, unknown>;
  providers: Record<string, unknown>[];
  channels: Record<string, unknown>;
  carriers: Record<string, unknown>[];
  vehicles: Record<string, unknown>[];
  trailers: Record<string, unknown>[];
  drivers: Record<string, unknown>[];
  trips: Record<string, unknown>[];
  marketPrices: Record<string, unknown>[];
  lots: Record<string, unknown>[];
  warehouseOps: Record<string, unknown>[];
  availabilities: Record<string, unknown>[];
  demands: Record<string, unknown>[];
  alertRules: Record<string, unknown>[];
  alerts: Record<string, unknown>[];
};

const VIEW_ENTITY_KINDS: Record<string, readonly string[]> = {
  home: [],
  command: [],
  report: [],
  counterparties: ["counterparty", "contact"],
  deals: ["deal", "counterparty"],
  contracts: ["contract", "counterparty"],
  documents: ["document"],
  calculations: ["calculation"],
  accounting: ["invoice", "payment"],
  shipments: ["shipment", "counterparty"],
  warehouses: ["warehouse", "inventory_lot", "warehouse_operation"],
  crops: ["crop"],
  calendar: ["calendar"],
  tasks: ["task"],
  notifications: ["notification"],
  markets: ["market", "market_price"],
  logistics: ["carrier", "vehicle", "trailer", "driver", "trip", "shipment"],
  settings: [],
  intel: [],
  weather: [],
  analytics: [],
  fields: [],
  machinery: [],
  operations: [],
};

const empty = (): Bundle => ({
  counterparties: [],
  contacts: [],
  deals: [],
  contracts: [],
  documents: [],
  calculations: [],
  invoices: [],
  payments: [],
  shipments: [],
  warehouses: [],
  crops: [],
  tasks: [],
  calendar: [],
  markets: [],
  notifications: [],
  files: [],
  dashboard: {},
  finance: {},
  providers: [],
  channels: {},
  carriers: [],
  vehicles: [],
  trailers: [],
  drivers: [],
  trips: [],
  marketPrices: [],
  lots: [],
  warehouseOps: [],
  availabilities: [],
  demands: [],
  alertRules: [],
  alerts: [],
});

export function AgroBusinessPage() {
  const caps = resolveCabinetCaps("agro");
  const organizationId = useOrgSelector((s) => s.organizationId);
  const orgLabel = useOrgSelector((s) => s.label());
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const roleLabel = useRoleSwitcher((s) => s.activeOption()?.label || activeRoleId);
  const agroRole = mapRole(activeRoleId);
  const canIntel = agroRole === "agro_director" || agroRole === "agro_manager" || agroRole === "platform_owner";
  const canCreateCore = caps.canCreate && agroRole !== "agro_accountant";
  const canFinance = caps.canSeeFinance || agroRole === "agro_accountant" || agroRole === "agro_director";

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [bundle, setBundle] = useState<Bundle>(empty);
  const [panel, setPanel] = useState<string | null>(null);
  const [drawer, setDrawer] = useState<{ kind: string; id: string } | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<{ kind: string; id: string } | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [quickSheet, setQuickSheet] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  const [cpForm, setCpForm] = useState({ name: "", types: "farmer,supplier", country: "UA", city: "", phone: "", email: "", responsible: "", notes: "", edrpou: "", tags: "", status: "lead" });
  const [contactForm, setContactForm] = useState({ full_name: "", position: "", phone: "", phone2: "", email: "", telegram: "", whatsapp: "", viber: "", comment: "", counterparty_id: "", primary: "true", pay_contact: "false", logistics_contact: "false", docs_contact: "false" });
  const [dealForm, setDealForm] = useState({
    title: "",
    counterparty_id: "",
    contact_id: "",
    crop: "Пшеница",
    quality_class: "",
    side: "buy",
    quantity: "100",
    unit: "т",
    price: "",
    currency: "UAH",
    vat: "",
    schedule_kind: "prepay",
    payment_defer_days: "",
    incoterms: "",
    load_place: "",
    dest_place: "",
    planned_at: "",
    responsible: "",
    notes: "",
  });
  const [dupMatches, setDupMatches] = useState<{ id: string; name?: string; reasons?: string[] }[]>([]);
  const [contractForm, setContractForm] = useState({ title: "", counterparty_id: "", deal_id: "" });
  const [calcForm, setCalcForm] = useState({
    title: "Расчёт сделки",
    counterparty_id: "",
    deal_id: "",
    contract_id: "",
    quantity: "100",
    purchase_price: "",
    sale_price: "",
    transport: "",
    storage: "",
    currency: "UAH",
    fx_rate: "",
  });
  const [calcPreview, setCalcPreview] = useState<Record<string, unknown> | null>(null);
  const [payForm, setPayForm] = useState({ title: "Оплата", amount: "", currency: "UAH", direction: "out", counterparty_id: "", deal_id: "", contract_id: "" });
  const [shipForm, setShipForm] = useState({ title: "Поставка", counterparty_id: "", deal_id: "", crop: "Пшеница", quantity: "100", deadline_at: "" });
  const [taskForm, setTaskForm] = useState({ title: "", due_at: "", owner: "", priority: "medium", counterparty_id: "", deal_id: "" });
  const [calForm, setCalForm] = useState({ title: "", starts_at: "", event_type: "meeting", counterparty_id: "", deal_id: "", remind_before_days: "1" });
  const [cropForm, setCropForm] = useState({ name: "", moisture: "", protein: "", gluten: "" });
  const [marketForm, setMarketForm] = useState({ name: "", group: "ЕС" });
  const [whOpForm, setWhOpForm] = useState({ type: "RECEIPT", warehouse_id: "", commodity: "Пшеница", quantity: "10", unit: "т" });
  const [opForm, setOpForm] = useState({ crop: "Пшеница", planned_qty: "500", price: "8500", currency: "UAH", unit: "т", load_place: "", dest_place: "", supplier_id: "", warehouse_id: "" });
  const [priceForm, setPriceForm] = useState({ commodity: "Пшеница", price: "", currency: "UAH", unit: "т", source_type: "MANUAL" });
  const [attachEntity, setAttachEntity] = useState({ entity_type: "counterparty", entity_id: "", doc_type: "contract" });

  const headers = useMemo(
    () => ({ "X-Organization-Id": organizationId, "X-Tenant-Id": organizationId, "X-Workspace-Id": "agro", "X-Role": agroRole }),
    [organizationId, agroRole],
  );
  const loadedKinds = useRef<Set<string>>(new Set());
  const viewKey = searchParams.get("view") || "home";

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const view = viewKey === "command" ? "home" : viewKey;
      const kinds = [...(VIEW_ENTITY_KINDS[view] || [])];
      const needKinds = kinds.filter((k) => !loadedKinds.current.has(k));
      const needProviders = view === "settings" || view === "intel";
      const [ccRes, finRes, filesRes, provRes, ...lists] = await Promise.all([
        agroOpsGet("/command-center", headers),
        view === "accounting" ? agroOpsGet("/finance/summary", headers) : Promise.resolve({ ok: true, status: 200, json: {} }),
        view === "documents" ? agroOpsGet("/files", headers) : Promise.resolve({ ok: true, status: 200, json: { items: [] } }),
        needProviders ? agroOpsGet("/providers", headers) : Promise.resolve({ ok: true, status: 200, json: { items: [] } }),
        ...needKinds.map((k) => agroOpsGet(`/entities/${k}`, headers)),
      ]);
      let ccJson = (ccRes.json && typeof ccRes.json === "object" ? ccRes.json : {}) as Record<string, unknown>;
      if (!ccJson.command_center && !ccJson.kpis) {
        const dash = await agroOpsGet("/dashboard", headers);
        ccJson = (dash.json && typeof dash.json === "object" ? dash.json : {}) as Record<string, unknown>;
      }
      if (!ccRes.ok && !(ccJson as { ok?: boolean }).ok) {
        setError("Сервис Агро временно недоступен. Обновите страницу или обратитесь к администратору.");
      }
      const kindMap: Record<string, Record<string, unknown>[]> = {};
      needKinds.forEach((k, i) => {
        kindMap[k] = asList(lists[i]?.json) as Record<string, unknown>[];
        loadedKinds.current.add(k);
      });
      setBundle((prev) => ({
        ...prev,
        counterparties: kindMap.counterparty ?? prev.counterparties,
        contacts: kindMap.contact ?? prev.contacts,
        deals: kindMap.deal ?? prev.deals,
        contracts: kindMap.contract ?? prev.contracts,
        documents: kindMap.document ?? prev.documents,
        calculations: kindMap.calculation ?? prev.calculations,
        invoices: kindMap.invoice ?? prev.invoices,
        payments: kindMap.payment ?? prev.payments,
        shipments: kindMap.shipment ?? prev.shipments,
        warehouses: kindMap.warehouse ?? prev.warehouses,
        crops: kindMap.crop ?? prev.crops,
        tasks: kindMap.task ?? prev.tasks,
        calendar: kindMap.calendar ?? prev.calendar,
        markets: kindMap.market ?? prev.markets,
        notifications: kindMap.notification ?? prev.notifications,
        files: view === "documents" ? (asList(filesRes.json) as Record<string, unknown>[]) : prev.files,
        dashboard: ccJson,
        finance: view === "accounting" && finRes.json && typeof finRes.json === "object" ? (finRes.json as Record<string, unknown>) : prev.finance,
        providers: needProviders ? (asList(provRes.json) as Record<string, unknown>[]) : prev.providers,
        channels: (ccJson.channels || prev.channels || {}) as Record<string, unknown>,
        carriers: kindMap.carrier ?? prev.carriers,
        vehicles: kindMap.vehicle ?? prev.vehicles,
        trailers: kindMap.trailer ?? prev.trailers,
        drivers: kindMap.driver ?? prev.drivers,
        trips: kindMap.trip ?? prev.trips,
        marketPrices: kindMap.market_price ?? prev.marketPrices,
        lots: kindMap.inventory_lot ?? prev.lots,
        warehouseOps: kindMap.warehouse_operation ?? prev.warehouseOps,
        availabilities: kindMap.availability ?? prev.availabilities,
        demands: kindMap.demand ?? prev.demands,
        alertRules: kindMap.alert_rule ?? prev.alertRules,
        alerts: kindMap.alert ?? prev.alerts,
      }));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [headers, viewKey]);

  useEffect(() => {
    void load();
  }, [load]);

  async function post(path: string, body: Record<string, unknown>) {
    setFormMsg(null);
    const res = await agroOpsPost(path, { ...body, organization_id: organizationId, role: agroRole }, headers);
    if (!res.ok) {
      const j = res.json as { message_ru?: string; error?: string };
      setFormMsg(j.message_ru || j.error || "Ошибка запроса");
      return null;
    }
    loadedKinds.current.clear();
    await load();
    return res.json;
  }

  function go(view: string, extra?: Record<string, string>) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (view === "home") next.delete("view");
      else next.set("view", view);
      ["pipeline", "tab", "q", "id", "filter", "overdue", "status", "from"].forEach((k) => {
        if (!extra || extra[k] === undefined) next.delete(k);
      });
      if (extra) {
        for (const [k, v] of Object.entries(extra)) next.set(k, v);
        if (extra.filter === "overdue") next.set("overdue", "true");
        if (extra.filter === "IN_TRANSIT") next.set("status", "IN_TRANSIT");
      }
      return next;
    });
  }

  const entityId = searchParams.get("id") || "";
  const currentView = searchParams.get("view") || "home";
  const opsFilter = searchParams.get("filter") || searchParams.get("status") || "";
  const overdueOnly = searchParams.get("overdue") === "true" || opsFilter === "overdue";

  function openEntity(kind: "counterparty" | "deal" | "agro_operation" | "agro_field" | "machine", id: string, from?: string) {
    const view =
      kind === "counterparty"
        ? "counterparties"
        : kind === "deal"
          ? "deals"
          : kind === "agro_field"
            ? "fields"
            : kind === "machine"
              ? "machinery"
              : "operations";
    go(view, { id, ...(from ? { from } : currentView && currentView !== view ? { from: currentView } : {}) });
  }

  function closeEntity() {
    const from = searchParams.get("from");
    if (from) {
      go(from);
      return;
    }
    go(currentView);
  }

  useEffect(() => {
    if (currentView === "counterparties" && entityId) {
      setDealForm((f) => ({ ...f, counterparty_id: entityId }));
      setContactForm((f) => ({ ...f, counterparty_id: entityId }));
      setContractForm((f) => ({ ...f, counterparty_id: entityId }));
      setPayForm((f) => ({ ...f, counterparty_id: entityId }));
      setShipForm((f) => ({ ...f, counterparty_id: entityId }));
      setTaskForm((f) => ({ ...f, counterparty_id: entityId }));
      setAttachEntity((f) => ({ ...f, entity_type: "counterparty", entity_id: entityId }));
    }
    if (currentView === "deals" && entityId) {
      setPayForm((f) => ({ ...f, deal_id: entityId }));
      setShipForm((f) => ({ ...f, deal_id: entityId }));
      setTaskForm((f) => ({ ...f, deal_id: entityId }));
      setContractForm((f) => ({ ...f, deal_id: entityId }));
      setAttachEntity((f) => ({ ...f, entity_type: "deal", entity_id: entityId }));
    }
    if (currentView === "operations" && entityId) {
      setAttachEntity((f) => ({ ...f, entity_type: "agro_operation", entity_id: entityId }));
      setTaskForm((f) => ({ ...f, deal_id: "" }));
    }
  }, [currentView, entityId]);

  const totals = (calcPreview?.totals || {}) as Record<string, number>;

  const formBlock = (title: string, children: ReactNode, onSave: () => void, show: boolean) =>
    show ? (
      <Card title={title}>
        {children}
        {formMsg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{formMsg}</p> : null}
        <div className="mt-2 flex gap-2">
          <Button size="sm" onClick={onSave}>
            Сохранить
          </Button>
          <Button size="sm" variant="ghost" onClick={() => { setPanel(null); setQuickSheet(false); }}>
            Закрыть
          </Button>
        </div>
      </Card>
    ) : null;

  const extra = (
    <>
      {drawer && (drawer.kind === "counterparty" || drawer.kind === "deal") ? (
        <AgroDossierDrawer
          kind={drawer.kind}
          itemId={drawer.id}
          headers={headers}
          canOperate={caps.canOperate}
          onClose={() => setDrawer(null)}
          onHandoff={(view, prefill) => {
            setDrawer(null);
            if (prefill) {
              if (view === "calculations") setCalcForm((f) => ({ ...f, ...prefill }));
              if (view === "documents") setAttachEntity((f) => ({ ...f, ...prefill }));
            }
            setPanel(view);
            go(view);
          }}
        />
      ) : null}
      {drawer && drawer.kind !== "counterparty" && drawer.kind !== "deal" ? (
        <AgroOpsDrawer
          kind={drawer.kind}
          itemId={drawer.id}
          headers={headers}
          canOperate={caps.canOperate}
          onClose={() => setDrawer(null)}
          onChanged={() => void load()}
        />
      ) : null}
      <LawyerConfirm
        open={Boolean(archiveTarget)}
        text={archiveTarget ? "Объект будет отправлен в архив." : "Удалить объект?"}
        confirmLabel="Да, удалить в архив"
        onYes={async () => {
          if (!archiveTarget) return;
          await post(`/entities/${archiveTarget.kind}/${archiveTarget.id}/archive`, {});
          setArchiveTarget(null);
        }}
        onNo={() => setArchiveTarget(null)}
      />
      {formBlock(
        "Операция — закупка зерна",
        <div className="grid gap-2 sm:grid-cols-2">
          <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2" value={opForm.crop} onChange={(e) => setOpForm((f) => ({ ...f, crop: e.target.value }))}>
            {["Пшеница", "Кукуруза", "Ячмень", "Подсолнечник", "Соя", "Рапс"].map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <Input placeholder="Своя культура" onBlur={(e) => e.target.value && setOpForm((f) => ({ ...f, crop: e.target.value }))} />
          <Input placeholder="План, т" value={opForm.planned_qty} onChange={(e) => setOpForm((f) => ({ ...f, planned_qty: e.target.value }))} />
          <Input placeholder="Цена закупки" value={opForm.price} onChange={(e) => setOpForm((f) => ({ ...f, price: e.target.value }))} />
          <Input placeholder="Пункт погрузки" value={opForm.load_place} onChange={(e) => setOpForm((f) => ({ ...f, load_place: e.target.value }))} />
          <Input placeholder="Пункт выгрузки" value={opForm.dest_place} onChange={(e) => setOpForm((f) => ({ ...f, dest_place: e.target.value }))} />
          <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2" value={opForm.supplier_id} onChange={(e) => setOpForm((f) => ({ ...f, supplier_id: e.target.value }))}>
            <option value="">Поставщик</option>
            {bundle.counterparties.map((c) => (
              <option key={pick(c, "id")} value={pick(c, "id")}>
                {pick(c, "name", "title")}
              </option>
            ))}
          </select>
          <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2" value={opForm.warehouse_id} onChange={(e) => setOpForm((f) => ({ ...f, warehouse_id: e.target.value }))}>
            <option value="">Склад</option>
            {bundle.warehouses.map((c) => (
              <option key={pick(c, "id")} value={pick(c, "id")}>
                {pick(c, "name", "title")}
              </option>
            ))}
          </select>
        </div>,
        async () => {
          const r = await post("/operations", { ...opForm, create_purchase: true });
          if (r) {
            setPanel(null);
            setQuickSheet(false);
            const id = pick((r as { item?: Record<string, unknown> }).item || {}, "id");
            if (id) openEntity("agro_operation", id);
          }
        },
        panel === "operation",
      )}
      {formBlock(
        "Новый контрагент",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={cpForm.name} onChange={(e) => setCpForm((f) => ({ ...f, name: e.target.value }))} />
          <Input placeholder="ЕДРПОУ / ИНН" value={cpForm.edrpou} onChange={(e) => setCpForm((f) => ({ ...f, edrpou: e.target.value }))} />
          <div className="sm:col-span-2">
            <p className="eds-type-small mb-1">Роли компании (можно несколько)</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(CP_TYPES).map(([id, label]) => {
                const selected = cpForm.types.split(",").map((t) => t.trim()).includes(id);
                return (
                  <label key={id} className="eds-type-small flex items-center gap-1">
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => {
                        const cur = cpForm.types.split(",").map((t) => t.trim()).filter(Boolean);
                        const next = selected ? cur.filter((t) => t !== id) : [...cur, id];
                        setCpForm((f) => ({ ...f, types: next.join(",") }));
                      }}
                    />
                    {label}
                  </label>
                );
              })}
            </div>
          </div>
          <Input placeholder="Страна" value={cpForm.country} onChange={(e) => setCpForm((f) => ({ ...f, country: e.target.value }))} />
          <Input placeholder="Город" value={cpForm.city} onChange={(e) => setCpForm((f) => ({ ...f, city: e.target.value }))} />
          <Input placeholder="Телефон" value={cpForm.phone} onChange={(e) => setCpForm((f) => ({ ...f, phone: e.target.value }))} />
          <Input placeholder="Эл. почта" value={cpForm.email} onChange={(e) => setCpForm((f) => ({ ...f, email: e.target.value }))} />
          <Input placeholder="Теги через запятую" value={cpForm.tags} onChange={(e) => setCpForm((f) => ({ ...f, tags: e.target.value }))} />
          {dupMatches.length ? (
            <div className="sm:col-span-2 rounded-md border border-[var(--ew-border)] p-2 eds-type-small" data-testid="agro-dup-warn">
              <p>Возможно, этот контрагент уже существует</p>
              {dupMatches.map((m) => (
                <button key={m.id} type="button" className="block text-[var(--eds-primary)]" onClick={() => openEntity("counterparty", m.id)}>
                  Открыть существующего: {m.name}
                </button>
              ))}
            </div>
          ) : null}
        </div>,
        async () => {
          const payload = { ...cpForm, types: cpForm.types.split(",").map((t) => t.trim()), tags: cpForm.tags.split(",").map((t) => t.trim()).filter(Boolean), force: dupMatches.length > 0 };
          const res = await agroOpsPost("/entities/counterparty", { ...payload, organization_id: organizationId, role: agroRole }, headers);
          const j = res.json as { item?: { id?: string }; matches?: { id: string; name?: string }[]; message_ru?: string };
          if (res.status === 409 && j.matches?.length) {
            setDupMatches(j.matches);
            setFormMsg(j.message_ru || "Возможно, этот контрагент уже существует");
            return;
          }
          if (!res.ok) {
            setFormMsg(j.message_ru || "Ошибка запроса");
            return;
          }
          setDupMatches([]);
          setPanel(null);
          await load();
          if (j.item?.id) openEntity("counterparty", String(j.item.id));
        },
        panel === "counterparty",
      )}
      {formBlock(
        "Контактное лицо",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="ФИО" value={contactForm.full_name} onChange={(e) => setContactForm((f) => ({ ...f, full_name: e.target.value }))} />
          <Input placeholder="Должность" value={contactForm.position} onChange={(e) => setContactForm((f) => ({ ...f, position: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={contactForm.counterparty_id} onChange={(e) => setContactForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
            <option value="">Контрагент</option>
            {bundle.counterparties.map((c) => (
              <option key={pick(c, "id")} value={pick(c, "id")}>
                {pick(c, "name")}
              </option>
            ))}
          </select>
          <Input placeholder="Телефон" value={contactForm.phone} onChange={(e) => setContactForm((f) => ({ ...f, phone: e.target.value }))} />
          <Input placeholder="Доп. телефон" value={contactForm.phone2} onChange={(e) => setContactForm((f) => ({ ...f, phone2: e.target.value }))} />
          <Input placeholder="Email" value={contactForm.email} onChange={(e) => setContactForm((f) => ({ ...f, email: e.target.value }))} />
          <Input placeholder="Telegram" value={contactForm.telegram} onChange={(e) => setContactForm((f) => ({ ...f, telegram: e.target.value }))} />
          <Input placeholder="WhatsApp" value={contactForm.whatsapp} onChange={(e) => setContactForm((f) => ({ ...f, whatsapp: e.target.value }))} />
          <Input placeholder="Viber" value={contactForm.viber} onChange={(e) => setContactForm((f) => ({ ...f, viber: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/entities/contact", { ...contactForm, primary: contactForm.primary === "true" });
          if (r) setPanel(null);
        },
        panel === "contact",
      )}
      {formBlock(
        "Новая сделка",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={dealForm.title} onChange={(e) => setDealForm((f) => ({ ...f, title: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={dealForm.counterparty_id} onChange={(e) => setDealForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
            <option value="">Контрагент</option>
            {bundle.counterparties.map((c) => (
              <option key={pick(c, "id")} value={pick(c, "id")}>
                {pick(c, "name")}
              </option>
            ))}
          </select>
          <Input placeholder="Культура" value={dealForm.crop} onChange={(e) => setDealForm((f) => ({ ...f, crop: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={dealForm.side} onChange={(e) => setDealForm((f) => ({ ...f, side: e.target.value }))}>
            <option value="buy">Покупка</option>
            <option value="sell">Продажа</option>
          </select>
          <Input placeholder="Класс / качество" value={dealForm.quality_class} onChange={(e) => setDealForm((f) => ({ ...f, quality_class: e.target.value }))} />
          <Input placeholder="Количество" value={dealForm.quantity} onChange={(e) => setDealForm((f) => ({ ...f, quantity: e.target.value }))} />
          <Input placeholder="Ед. изм." value={dealForm.unit} onChange={(e) => setDealForm((f) => ({ ...f, unit: e.target.value }))} />
          <Input placeholder="Цена" value={dealForm.price} onChange={(e) => setDealForm((f) => ({ ...f, price: e.target.value }))} />
          <Input placeholder="Валюта" value={dealForm.currency} onChange={(e) => setDealForm((f) => ({ ...f, currency: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={dealForm.schedule_kind} onChange={(e) => setDealForm((f) => ({ ...f, schedule_kind: e.target.value }))}>
            <option value="prepay">100% предоплата</option>
            <option value="30_70">30/70</option>
            <option value="50_50">50/50</option>
            <option value="after_delivery">Оплата после поставки</option>
            <option value="defer">Отсрочка N дней</option>
            <option value="custom">Произвольный график</option>
          </select>
          <Input placeholder="Отсрочка дней" value={dealForm.payment_defer_days} onChange={(e) => setDealForm((f) => ({ ...f, payment_defer_days: e.target.value }))} />
          <Input placeholder="Incoterms" value={dealForm.incoterms} onChange={(e) => setDealForm((f) => ({ ...f, incoterms: e.target.value }))} />
          <Input placeholder="Место загрузки" value={dealForm.load_place} onChange={(e) => setDealForm((f) => ({ ...f, load_place: e.target.value }))} />
          <Input placeholder="Место доставки" value={dealForm.dest_place} onChange={(e) => setDealForm((f) => ({ ...f, dest_place: e.target.value }))} />
          <Input placeholder="Плановая дата" value={dealForm.planned_at} onChange={(e) => setDealForm((f) => ({ ...f, planned_at: e.target.value }))} />
          <Input placeholder="Комментарий" value={dealForm.notes} onChange={(e) => setDealForm((f) => ({ ...f, notes: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/entities/deal", dealForm);
          if (r && typeof r === "object" && (r as { item?: { id?: string } }).item?.id) {
            setPanel(null);
            openEntity("deal", String((r as { item: { id: string } }).item.id));
          }
        },
        panel === "deal",
      )}
      {formBlock(
        "Договор",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={contractForm.title} onChange={(e) => setContractForm((f) => ({ ...f, title: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={contractForm.counterparty_id} onChange={(e) => setContractForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
            <option value="">Контрагент</option>
            {bundle.counterparties.map((c) => (
              <option key={pick(c, "id")} value={pick(c, "id")}>
                {pick(c, "name")}
              </option>
            ))}
          </select>
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={contractForm.deal_id} onChange={(e) => setContractForm((f) => ({ ...f, deal_id: e.target.value }))}>
            <option value="">Сделка</option>
            {bundle.deals.map((c) => (
              <option key={pick(c, "id")} value={pick(c, "id")}>
                {pick(c, "title")}
              </option>
            ))}
          </select>
        </div>,
        async () => {
          const r = await post("/entities/contract", contractForm);
          if (r) setPanel(null);
        },
        panel === "contract",
      )}
      {panel === "documents" ? (
        <Card title="Прикрепить файл">
          <div className="grid gap-2 sm:grid-cols-2">
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={attachEntity.entity_type} onChange={(e) => setAttachEntity((f) => ({ ...f, entity_type: e.target.value, entity_id: "" }))}>
              {["counterparty", "deal", "contract", "invoice", "calculation", "payment", "shipment", "task", "carrier", "vehicle", "trailer", "driver", "trip", "warehouse", "market", "inventory_lot"].map((k) => (
                <option key={k} value={k}>
                  {ENTITY_TYPES[k] || k}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={attachEntity.entity_id} onChange={(e) => setAttachEntity((f) => ({ ...f, entity_id: e.target.value }))}>
              <option value="">К какому объекту прикрепить</option>
              {(
                {
                  counterparty: bundle.counterparties,
                  deal: bundle.deals,
                  contract: bundle.contracts,
                  invoice: bundle.invoices,
                  calculation: bundle.calculations,
                  payment: bundle.payments,
                  shipment: bundle.shipments,
                  task: bundle.tasks,
                  carrier: bundle.carriers,
                  vehicle: bundle.vehicles,
                  trailer: bundle.trailers,
                  driver: bundle.drivers,
                  trip: bundle.trips,
                  warehouse: bundle.warehouses,
                  market: bundle.markets,
                  inventory_lot: bundle.lots,
                }[attachEntity.entity_type] || []
              ).map((row) => (
                <option key={pick(row, "id")} value={pick(row, "id")}>
                  {pick(row, "name", "title")}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={attachEntity.doc_type} onChange={(e) => setAttachEntity((f) => ({ ...f, doc_type: e.target.value }))}>
              {Object.entries(DOC_TYPES).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.jpg,.jpeg,.png,.heic,.heif,image/*"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const res = await agroOpsUpload("/files", file, attachEntity, headers);
                setFormMsg(res.ok ? "Файл прикреплён" : "Не удалось прикрепить файл");
                if (res.ok) await load();
              }}
            />
            <label className="eds-type-small">
              Фото / камера
              <input
                type="file"
                accept="image/*,.heic,.heif"
                capture="environment"
                className="mt-1 block min-h-11"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const res = await agroOpsUpload("/files", file, { ...attachEntity, doc_type: "photo" }, headers);
                  setFormMsg(res.ok ? "Фото прикреплено" : "Не удалось прикрепить файл");
                  if (res.ok) await load();
                }}
              />
            </label>
          </div>
          <Button className="mt-2" size="sm" variant="ghost" onClick={() => setPanel(null)}>
            Закрыть
          </Button>
        </Card>
      ) : null}
      {panel === "calculations" ? (
        <Card title="Расчёт экономики сделки">
          <div className="grid gap-2 sm:grid-cols-3">
            <Input placeholder="Название" value={calcForm.title} onChange={(e) => setCalcForm((f) => ({ ...f, title: e.target.value }))} />
            <Input placeholder="Количество, т" value={calcForm.quantity} onChange={(e) => setCalcForm((f) => ({ ...f, quantity: e.target.value }))} />
            <Input placeholder="Закупочная цена" value={calcForm.purchase_price} onChange={(e) => setCalcForm((f) => ({ ...f, purchase_price: e.target.value }))} />
            <Input placeholder="Цена продажи" value={calcForm.sale_price} onChange={(e) => setCalcForm((f) => ({ ...f, sale_price: e.target.value }))} />
            <Input placeholder="Транспорт" value={calcForm.transport} onChange={(e) => setCalcForm((f) => ({ ...f, transport: e.target.value }))} />
            <Input placeholder="Хранение" value={calcForm.storage} onChange={(e) => setCalcForm((f) => ({ ...f, storage: e.target.value }))} />
            <Input placeholder="Курс (вручную)" value={calcForm.fx_rate} onChange={(e) => setCalcForm((f) => ({ ...f, fx_rate: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={calcForm.deal_id} onChange={(e) => setCalcForm((f) => ({ ...f, deal_id: e.target.value }))}>
              <option value="">Сделка</option>
              {bundle.deals.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title")}
                </option>
              ))}
            </select>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={async () => {
                const r = await agroOpsPost("/calculations/preview", calcForm, headers);
                setCalcPreview((r.json as { item?: Record<string, unknown> }).item || null);
              }}
            >
              Посчитать
            </Button>
            <Button
              size="sm"
              disabled={!canFinance}
              onClick={async () => {
                const r = await post("/entities/calculation", calcForm);
                if (r) setPanel(null);
              }}
            >
              Сохранить расчёт
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setPanel(null)}>
              Закрыть
            </Button>
          </div>
          {calcPreview ? (
            <dl className="mt-3 grid gap-1 eds-type-small sm:grid-cols-2" data-testid="agro-calc-totals">
              <div>Себестоимость: {String(totals.total_cost ?? "—")}</div>
              <div>Выручка: {String(totals.sale_value ?? "—")}</div>
              <div>Валовая прибыль: {String(totals.gross_profit ?? "—")}</div>
              <div>Прибыль / т: {String(totals.profit_per_tonne ?? "—")}</div>
              <div>Маржа %: {String(totals.margin_pct ?? "—")}</div>
              <div>Наценка %: {String(totals.markup_pct ?? "—")}</div>
              <div>Курс: {String(calcPreview.fx_note_ru || "Курс не подключён")}</div>
            </dl>
          ) : null}
        </Card>
      ) : null}
      {formBlock(
        "Оплата",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Назначение" value={payForm.title} onChange={(e) => setPayForm((f) => ({ ...f, title: e.target.value }))} />
          <Input placeholder="Сумма" value={payForm.amount} onChange={(e) => setPayForm((f) => ({ ...f, amount: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={payForm.direction} onChange={(e) => setPayForm((f) => ({ ...f, direction: e.target.value }))}>
            <option value="out">Исходящая (мы должны)</option>
            <option value="in">Входящая (нам должны)</option>
          </select>
        </div>,
        async () => {
          const r = await post("/entities/payment", payForm);
          if (r) setPanel(null);
        },
        panel === "payment",
      )}
      {formBlock(
        "Поставка",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={shipForm.title} onChange={(e) => setShipForm((f) => ({ ...f, title: e.target.value }))} />
          <Input placeholder="Количество" value={shipForm.quantity} onChange={(e) => setShipForm((f) => ({ ...f, quantity: e.target.value }))} />
          <Input type="date" value={shipForm.deadline_at} onChange={(e) => setShipForm((f) => ({ ...f, deadline_at: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/entities/shipment", shipForm);
          if (r) setPanel(null);
        },
        panel === "shipment",
      )}
      {formBlock(
        "Задача",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={taskForm.title} onChange={(e) => setTaskForm((f) => ({ ...f, title: e.target.value }))} />
          <Input type="date" value={taskForm.due_at} onChange={(e) => setTaskForm((f) => ({ ...f, due_at: e.target.value }))} />
          <Input placeholder="Ответственный" value={taskForm.owner} onChange={(e) => setTaskForm((f) => ({ ...f, owner: e.target.value }))} />
          <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={taskForm.priority} onChange={(e) => setTaskForm((f) => ({ ...f, priority: e.target.value }))}>
            <option value="low">Низкий</option>
            <option value="medium">Средний</option>
            <option value="high">Высокий</option>
          </select>
        </div>,
        async () => {
          const r = await post("/entities/task", taskForm);
          if (r) setPanel(null);
        },
        panel === "task",
      )}
      {formBlock(
        "Событие календаря",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={calForm.title} onChange={(e) => setCalForm((f) => ({ ...f, title: e.target.value }))} />
          <Input type="datetime-local" value={calForm.starts_at} onChange={(e) => setCalForm((f) => ({ ...f, starts_at: e.target.value }))} />
          <Input placeholder="Напомнить за N дней" value={calForm.remind_before_days} onChange={(e) => setCalForm((f) => ({ ...f, remind_before_days: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/entities/calendar", calForm);
          if (r) setPanel(null);
        },
        panel === "calendar",
      )}
      {formBlock(
        "Культура / продукт",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={cropForm.name} onChange={(e) => setCropForm((f) => ({ ...f, name: e.target.value }))} />
          <Input placeholder="Влажность" value={cropForm.moisture} onChange={(e) => setCropForm((f) => ({ ...f, moisture: e.target.value }))} />
          <Input placeholder="Протеин" value={cropForm.protein} onChange={(e) => setCropForm((f) => ({ ...f, protein: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/entities/crop", {
            name: cropForm.name,
            quality_attributes: { moisture: cropForm.moisture, protein: cropForm.protein, gluten: cropForm.gluten },
          });
          if (r) setPanel(null);
        },
        panel === "crop",
      )}
      {formBlock(
        "Рынок / страна",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Название" value={marketForm.name} onChange={(e) => setMarketForm((f) => ({ ...f, name: e.target.value }))} />
          <Input placeholder="Группа (ЕС, Чёрное море…)" value={marketForm.group} onChange={(e) => setMarketForm((f) => ({ ...f, group: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/entities/market", marketForm);
          if (r) setPanel(null);
        },
        panel === "market",
      )}
      {formBlock(
        "Складская операция",
        <div className="grid gap-2 sm:grid-cols-2">
          <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={whOpForm.type} onChange={(e) => setWhOpForm((f) => ({ ...f, type: e.target.value }))}>
            <option value="RECEIPT">Приход</option>
            <option value="ISSUE">Расход</option>
            <option value="TRANSFER">Перемещение</option>
          </select>
          <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={whOpForm.warehouse_id} onChange={(e) => setWhOpForm((f) => ({ ...f, warehouse_id: e.target.value }))}>
            <option value="">Склад</option>
            {bundle.warehouses.map((w) => (
              <option key={pick(w, "id")} value={pick(w, "id")}>
                {pick(w, "name")}
              </option>
            ))}
          </select>
          <Input placeholder="Культура" value={whOpForm.commodity} onChange={(e) => setWhOpForm((f) => ({ ...f, commodity: e.target.value }))} />
          <Input placeholder="Количество" value={whOpForm.quantity} onChange={(e) => setWhOpForm((f) => ({ ...f, quantity: e.target.value }))} />
        </div>,
        async () => {
          const r = await post("/warehouses/operations", whOpForm);
          if (r) {
            setPanel(null);
            setQuickSheet(false);
          }
        },
        panel === "warehouse_op",
      )}
      {formBlock(
        "Цена",
        <div className="grid gap-2 sm:grid-cols-2">
          <Input placeholder="Культура" value={priceForm.commodity} onChange={(e) => setPriceForm((f) => ({ ...f, commodity: e.target.value }))} />
          <Input placeholder="Цена" value={priceForm.price} onChange={(e) => setPriceForm((f) => ({ ...f, price: e.target.value }))} />
          <select className="min-h-11 rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={priceForm.source_type} onChange={(e) => setPriceForm((f) => ({ ...f, source_type: e.target.value }))}>
            <option value="MANUAL">Ручная</option>
            <option value="COUNTERPARTY">Контрагент</option>
            <option value="OURS">Наша цена</option>
          </select>
        </div>,
        async () => {
          const r = await post("/entities/market_price", priceForm);
          if (r) {
            setPanel(null);
            setQuickSheet(false);
          }
        },
        panel === "price",
      )}
    </>
  );

  function rowsFor(kind: string, items: Record<string, unknown>[], cols: (r: Record<string, unknown>) => Record<string, string>) {
    return items.map((r, i) => ({ id: pick(r, "id") || String(i), ...cols(r) }));
  }

  const commandCenter = (bundle.dashboard.command_center || {}) as CommandCenterPayload;
  const pipelineFilter = searchParams.get("pipeline") || "";
  const dealItems = pipelineFilter
    ? bundle.deals.filter((d) => dealPipelineId(pick(d, "status")) === pipelineFilter)
    : bundle.deals;
  const transitFilter = opsFilter.toUpperCase() === "IN_TRANSIT" || searchParams.get("status") === "IN_TRANSIT";
  const logisticsTrips = transitFilter
    ? bundle.trips.filter((t) => ["in_transit", "loading", "loaded", "assigned"].includes(String(t.status || "").toLowerCase()))
    : bundle.trips;
  const logisticsShipments = transitFilter
    ? bundle.shipments.filter((s) => ["in_transit", "loading", "loaded", "assigned", "planned"].includes(String(s.status || "").toLowerCase()))
    : bundle.shipments;

  const sections: Record<string, OpsSection> = {
    home: {
      id: "home",
      title: "АГРО — ОПЕРАЦИОННЫЙ ЦЕНТР",
      description: "Что происходит сегодня: сделки, поставки, склады, цены, погода и решения директора.",
      columns: [],
      rows: [],
      panel: (
        <div data-testid="agro-home">
          <AgroCommandCenter
            payload={commandCenter}
            roleLabel={ROLE_RU[agroRole] || roleLabel}
            canCreate={canCreateCore}
            canFinance={canFinance}
            canOperate={caps.canOperate}
            onGo={go}
            onOpen={(kind, id) => {
              if (kind === "counterparty" || kind === "deal" || kind === "agro_operation" || kind === "agro_field") openEntity(kind, id);
              else setDrawer({ kind, id });
            }}
            onQuick={() => setQuickSheet(true)}
            onQuickKind={(id) => {
              setQuickSheet(true);
              setPanel(id);
            }}
            onSearch={() => setSearchOpen(true)}
            onNotify={() => undefined}
            onTask={async (id, action) => {
              if (action === "open") {
                setDrawer({ kind: "task", id });
                return;
              }
              if (action === "done") {
                await post(`/entities/task/${id}`, { status: "done" });
                return;
              }
              const due = new Date();
              due.setDate(due.getDate() + 1);
              await post(`/entities/task/${id}`, { due_at: due.toISOString().slice(0, 10) });
            }}
            onAttach={(kind, id) => {
              setAttachEntity((f) => ({ ...f, entity_type: kind, entity_id: id }));
              setPanel("documents");
              setQuickSheet(true);
            }}
          />
          {quickSheet ? null : extra}
        </div>
      ),
    },
    command: {
      id: "command",
      title: "АГРО — КОМАНДНЫЙ ЦЕНТР",
      description: "Агрегированный обзор. Источники — те же таблицы, без дублирования.",
      columns: [],
      rows: [],
      panel: (
        <div data-testid="agro-command-route">
          <AgroCommandCenter
            payload={commandCenter}
            roleLabel={ROLE_RU[agroRole] || roleLabel}
            canCreate={canCreateCore}
            canFinance={canFinance}
            canOperate={caps.canOperate}
            onGo={go}
            onOpen={(kind, id) => {
              if (kind === "counterparty" || kind === "deal" || kind === "agro_operation" || kind === "agro_field") openEntity(kind, id);
              else setDrawer({ kind, id });
            }}
            onQuick={() => setQuickSheet(true)}
            onQuickKind={(id) => {
              setQuickSheet(true);
              setPanel(id);
            }}
            onSearch={() => setSearchOpen(true)}
            onNotify={() => undefined}
            onTask={async (id, action) => {
              if (action === "open") {
                setDrawer({ kind: "task", id });
                return;
              }
              if (action === "done") {
                await post(`/entities/task/${id}`, { status: "done" });
                return;
              }
              const due = new Date();
              due.setDate(due.getDate() + 1);
              await post(`/entities/task/${id}`, { due_at: due.toISOString().slice(0, 10) });
            }}
            onAttach={(kind, id) => {
              setAttachEntity((f) => ({ ...f, entity_type: kind, entity_id: id }));
              setPanel("documents");
              setQuickSheet(true);
            }}
          />
        </div>
      ),
    },
    report: {
      id: "report",
      title: "АГРО — УПРАВЛЕНЧЕСКАЯ СВОДКА",
      description: "Печатная управленческая сводка. Цифры только из реальных записей.",
      columns: [],
      rows: [],
      emptyTitle: "Нет данных для сводки.",
      panel: <AgroManagementReport headers={headers} />,
      quickActions: canFinance
        ? [
            { label: "CSV P&L", to: "/api/agro-ops/v1/export/pnl" },
            { label: "Дебиторка", to: "/api/agro-ops/v1/export/receivables" },
            { label: "Кредиторка", to: "/api/agro-ops/v1/export/payables" },
            { label: "Склад", to: "/api/agro-ops/v1/export/inventory" },
            { label: "Культуры", to: "/api/agro-ops/v1/export/crop-economics" },
            { label: "Поля", to: "/api/agro-ops/v1/export/field-economics" },
          ]
        : [],
    },
    operations: {
      id: "operations",
      title: opsFilter ? `Операции — ${opsFilter}` : "Операции",
      description: "Закупка → логистика → вес → качество → склад → продажа → факт P&L.",
      columns: [],
      rows: [],
      panel: (
        <>
          {entityId && currentView === "operations" ? (
            <AgroOperation360
              itemId={entityId}
              headers={headers}
              canCreate={canCreateCore}
              canFinance={canFinance}
              canOperate={Boolean(caps.canOperate)}
              initialTab={searchParams.get("tab") || undefined}
              onBack={closeEntity}
              onQuick={(kind) => {
                const tabMap: Record<string, string> = {
                  weighing: "weighings",
                  quality: "quality",
                  expense: "expenses",
                  documents: "documents",
                  truck: "trucks",
                  task: "tasks",
                  sale: "sales",
                };
                go("operations", { id: entityId, tab: tabMap[kind] || kind });
                setQuickSheet(false);
              }}
              onChanged={() => void load()}
            />
          ) : (
            <AgroOperationsList
              headers={headers}
              canCreate={canCreateCore}
              filter={opsFilter}
              onOpen={(id) => openEntity("agro_operation", id)}
              onCreate={() => {
                setPanel("operation");
                setQuickSheet(true);
              }}
            />
          )}
          {extra}
        </>
      ),
      quickActions: canCreateCore ? [{ label: "Создать операцию", onClick: () => { setPanel("operation"); setQuickSheet(true); } }] : [],
    },
    fields: {
      id: "fields",
      title: "Поля",
      description: "Реестр полей, карта, Field 360, экономика.",
      columns: [],
      rows: [],
      panel: (
        <AgroProductionPage
          headers={headers}
          canCreate={canCreateCore}
          canFinance={canFinance}
          fieldId={currentView === "fields" ? entityId || null : null}
          tab={searchParams.get("tab") || undefined}
          onOpen={(id) => openEntity("agro_field", id)}
          onBack={closeEntity}
          onGo={go}
        />
      ),
    },
    sowing: {
      id: "sowing",
      title: "Посевы",
      description: "Операционный учёт посевов и затрат.",
      columns: [],
      rows: [],
      panel: (
        <AgroSowingsPage
          headers={headers}
          canCreate={canCreateCore}
          onOpenField={(id) => openEntity("agro_field", id)}
        />
      ),
    },
    works: {
      id: "works",
      title: "Работы",
      description: "Наряды: поле + техника + сотрудник.",
      columns: [],
      rows: [],
      panel: (
        <AgroWorksPage
          headers={headers}
          canCreate={canCreateCore}
          onOpenField={(id) => openEntity("agro_field", id)}
        />
      ),
    },
    harvest: {
      id: "harvest",
      title: "Урожай",
      description: "Уборка и оприходование на склад (AGRO 2.2).",
      columns: [],
      rows: [],
      panel: (
        <AgroHarvestPage
          headers={headers}
          canCreate={canCreateCore}
          onOpenField={(id) => openEntity("agro_field", id)}
        />
      ),
    },
    machinery: {
      id: "machinery",
      title: "Техника",
      description: "Реестр техники, статусы, ТО.",
      columns: [],
      rows: [],
      panel: (
        <AgroMachinery26Page
          headers={headers}
          canCreate={canCreateCore}
          machineId={currentView === "machinery" ? entityId || null : null}
          onOpen={(id) => openEntity("machine", id)}
          onBack={closeEntity}
        />
      ),
    },
    counterparties: {
      id: "counterparties",
      title: "Контрагенты",
      description: "Операционный CRM: один контрагент — несколько ролей, сделки, расчёты.",
      columns: [],
      rows: [],
      panel: (
        <>
          {entityId && currentView === "counterparties" ? (
            <AgroCounterparty360
              itemId={entityId}
              headers={headers}
              canCreate={canCreateCore}
              canFinance={canFinance}
              canOperate={Boolean(caps.canOperate)}
              onBack={closeEntity}
              onOpenDeal={(id) => openEntity("deal", id)}
              onQuick={(kind) => {
                setPanel(kind);
                setQuickSheet(true);
              }}
              onChanged={() => void load()}
            />
          ) : (
            <AgroCrmList
              headers={headers}
              canCreate={canCreateCore}
              canFinance={canFinance}
              canExport={canFinance || agroRole === "agro_director"}
              onOpen={(id) => openEntity("counterparty", id)}
              onCreate={() => setPanel("counterparty")}
            />
          )}
          {extra}
        </>
      ),
      quickActions: canCreateCore
        ? [
            { label: "Создать контрагента", onClick: () => setPanel("counterparty") },
            { label: "Добавить контакт", onClick: () => setPanel("contact") },
          ]
        : [],
    },
    deals: {
      id: "deals",
      title: pipelineFilter ? `Сделки — ${DEAL_PIPELINE.find((p) => p.id === pipelineFilter)?.label || pipelineFilter}` : "Сделки",
      description: "Закупка и продажа сельхозпродукции.",
      columns: entityId && currentView === "deals" ? [] : [
        { key: "title", label: "Сделка" },
        { key: "crop", label: "Культура" },
        { key: "qty", label: "Объём" },
        { key: "status", label: "Статус" },
      ],
      rows: entityId && currentView === "deals" ? [] : rowsFor("deal", dealItems, (r) => ({
        title: pick(r, "title"),
        crop: pick(r, "crop", "product"),
        qty: `${pick(r, "quantity")} ${pick(r, "unit")}`,
        status: ru(DEAL_STATUSES, pick(r, "status")),
      })),
      panel: (
        <>
          {entityId && currentView === "deals" ? (
            <AgroDeal360
              itemId={entityId}
              headers={headers}
              canCreate={canCreateCore}
              canFinance={canFinance}
              canOperate={Boolean(caps.canOperate)}
              onBack={closeEntity}
              onQuick={(kind) => {
                setPanel(kind);
                setQuickSheet(true);
              }}
              onChanged={() => void load()}
            />
          ) : null}
          {extra}
        </>
      ),
      emptyTitle: "Сделок пока нет",
      emptyCtaLabel: canCreateCore ? "Создать сделку" : undefined,
      emptyCtaOnClick: canCreateCore ? () => setPanel("deal") : undefined,
      quickActions: canCreateCore ? [{ label: "Создать сделку", onClick: () => setPanel("deal") }] : [],
      onRowOpen: (row) => openEntity("deal", String(row.id)),
      rowActions: caps.canOperate
        ? (row) => (
            <LawyerRowMenu
              row={row}
              onOpen={() => openEntity("deal", String(row.id))}
              onArchive={canCreateCore ? () => setArchiveTarget({ kind: "deal", id: String(row.id) }) : undefined}
            />
          )
        : undefined,
    },
    contracts: {
      id: "contracts",
      title: "Договоры",
      description: "Договоры, связанные со сделками и контрагентами.",
      columns: [
        { key: "title", label: "Договор" },
        { key: "status", label: "Статус" },
      ],
      rows: rowsFor("contract", bundle.contracts, (r) => ({ title: pick(r, "title"), status: ruStatus(pick(r, "status")) })),
      panel: extra,
      emptyTitle: "Договоров пока нет",
      emptyCtaLabel: canCreateCore ? "Создать договор" : undefined,
      emptyCtaOnClick: canCreateCore ? () => setPanel("contract") : undefined,
      quickActions: canCreateCore ? [{ label: "Создать договор", onClick: () => setPanel("contract") }] : [],
    },
    documents: {
      id: "documents",
      title: "Документы",
      description: "Вложения PDF, офисные файлы и фото. Файлы хранятся отдельно, не в базе.",
      columns: [
        { key: "filename", label: "Файл" },
        { key: "doc_type", label: "Тип" },
        { key: "entity", label: "Объект" },
      ],
      rows: rowsFor("file", bundle.files, (r) => ({
        filename: pick(r, "filename", "title"),
        doc_type: ru(DOC_TYPES, pick(r, "doc_type")),
        entity: ENTITY_TYPES[pick(r, "entity_type")] || pick(r, "entity_type") || "—",
      })),
      panel: extra,
      emptyTitle: "Файлов пока нет",
      emptyCtaLabel: caps.canOperate ? "📎 Прикрепить файл" : undefined,
      emptyCtaOnClick: caps.canOperate ? () => setPanel("documents") : undefined,
      quickActions: caps.canOperate ? [{ label: "📎 Прикрепить файл", onClick: () => setPanel("documents") }] : [],
      rowActions: (row) => (
        <a className="eds-type-small underline" href={agroOpsFileUrl(String(row.id))} target="_blank" rel="noreferrer">
          Открыть
        </a>
      ),
    },
    calculations: {
      id: "calculations",
      title: "Расчёты",
      description: "Экономика сделки: себестоимость, маржа, курс только вручную.",
      columns: [
        { key: "title", label: "Расчёт" },
        { key: "profit", label: "Прибыль" },
        { key: "margin", label: "Маржа %" },
      ],
      rows: rowsFor("calc", bundle.calculations, (r) => {
        const t = (r.totals || {}) as Record<string, unknown>;
        return { title: pick(r, "title"), profit: String(t.gross_profit ?? "—"), margin: String(t.margin_pct ?? "—") };
      }),
      panel: extra,
      emptyTitle: "Расчётов пока нет",
      emptyCtaLabel: canFinance ? "Сделать расчёт" : undefined,
      emptyCtaOnClick: canFinance ? () => setPanel("calculations") : undefined,
      quickActions: canFinance ? [{ label: "Сделать расчёт", onClick: () => setPanel("calculations") }] : [],
    },
    accounting: {
      id: "accounting",
      title: "Бухгалтерия",
      description: "Счета, оплаты, дебиторская и кредиторская задолженность.",
      columns: [
        { key: "title", label: "Документ" },
        { key: "amount", label: "Сумма" },
        { key: "status", label: "Статус" },
      ],
      rows: [
        ...rowsFor(
          "inv",
          overdueOnly
            ? bundle.invoices.filter((r) => {
                const due = String(r.due_at || "").slice(0, 10);
                const today = new Date().toISOString().slice(0, 10);
                return due && due < today && !["paid", "cancelled"].includes(String(r.status || ""));
              })
            : bundle.invoices,
          (r) => ({ title: `Счёт: ${pick(r, "title")}`, amount: `${pick(r, "amount")} ${pick(r, "currency")}`, status: ruStatus(pick(r, "status")) }),
        ),
        ...rowsFor("pay", overdueOnly ? [] : bundle.payments, (r) => ({ title: `Оплата: ${pick(r, "title")}`, amount: `${pick(r, "amount")} ${pick(r, "currency")}`, status: ruStatus(pick(r, "status")) })),
      ],
      cards: canFinance
        ? [
            { label: "Дебиторская задолженность", value: bundle.finance.receivables_total == null ? (bundle.finance.mixed_currencies ? "валюты раздельно" : "Нет данных") : String(bundle.finance.receivables_total) },
            { label: "Кредиторская задолженность", value: bundle.finance.payables_total == null ? (bundle.finance.mixed_currencies ? "валюты раздельно" : "Нет данных") : String(bundle.finance.payables_total) },
            { label: "Просрочено", value: bundle.finance.overdue_total == null ? (overdueOnly ? "Нет просроченных оплат" : "Нет данных") : String(bundle.finance.overdue_total) },
          ]
        : [],
      panel: extra,
      quickActions: canFinance
        ? [
            { label: "Создать оплату", onClick: () => setPanel("payment") },
            { label: "Скачать таблицу", to: "/api/agro-ops/v1/export/payments" },
          ]
        : [],
    },
    shipments: {
      id: "shipments",
      title: "Поставки",
      description: "Плановые и фактические поставки. Прогресс считается только из зафиксированных объёмов.",
      columns: [],
      rows: [],
      emptyTitle: "Поставок ещё нет.",
      panel: (
        <>
          <AgroDeliveriesPanel
            headers={headers}
            canCreate={canCreateCore}
            shipments={bundle.shipments}
            counterparties={bundle.counterparties}
            onChanged={() => void load()}
            onOpen={(id) => setDrawer({ kind: "shipment", id })}
            onAttach={(id) => {
              setAttachEntity((f) => ({ ...f, entity_type: "shipment", entity_id: id }));
              setPanel("documents");
              go("documents");
            }}
          />
          {extra}
        </>
      ),
      quickActions: canCreateCore ? [{ label: "Добавить поставку", onClick: () => setPanel("shipment") }] : [],
    },
    warehouses: {
      id: "warehouses",
      title: "Склады",
      description: "Остатки, приход, расход и партии. Инвентарь не меняется молча после рейса.",
      columns: [],
      rows: [],
      emptyTitle: "Склады ещё не добавлены.",
      emptyDescription: "Добавьте склад и оформите приход — остатки считаются только из операций.",
      panel: (
        <>
          <AgroWarehousePanel
            headers={headers}
            canCreate={canCreateCore}
            warehouses={bundle.warehouses}
            lots={bundle.lots}
            operations={bundle.warehouseOps}
            counterparties={bundle.counterparties}
            deals={bundle.deals}
            trips={bundle.trips}
            vehicles={bundle.vehicles}
            drivers={bundle.drivers}
            onChanged={() => void load()}
            onOpen={(kind, id) => setDrawer({ kind, id })}
            onAttach={(kind, id) => {
              setAttachEntity((f) => ({ ...f, entity_type: kind, entity_id: id }));
              setPanel("documents");
              go("documents");
            }}
          />
          {extra}
        </>
      ),
    },
    crops: {
      id: "crops",
      title: "Культуры",
      description: "Агрономический каталог и торговый справочник.",
      columns: [],
      rows: [],
      panel: (
        <div className="grid gap-4 min-w-0 overflow-x-hidden">
          <AgroCropsCatalog26 headers={headers} canCreate={canCreateCore} />
          <AgroCropsPanel
            headers={headers}
            canCreate={canCreateCore}
            counterparties={bundle.counterparties}
            onChanged={() => void load()}
            onOpen={(kind, id) => setDrawer({ kind, id })}
          />
          {extra}
        </div>
      ),
      quickActions: canCreateCore ? [{ label: "Добавить культуру", onClick: () => setPanel("crop") }] : [],
    },
    weather: {
      id: "weather",
      title: "Погода",
      description: "Карта Украины, области, прогноз и влияние на культуры — только по реальным наблюдениям.",
      columns: [],
      rows: [],
      panel: (
        <div className="min-w-0 overflow-x-hidden">
          <AgroWeatherPanel
            headers={headers}
            onOpenSettings={() => {
              setSearchParams((prev) => {
                const next = new URLSearchParams(prev);
                next.set("view", "settings");
                next.set("tab", "weather");
                return next;
              });
            }}
          />
        </div>
      ),
    },
    markets: {
      id: "markets",
      title: "Цены и рынки",
      description: "Ручные цены всегда. Автоматические — только после успешного опроса источника.",
      columns: [],
      rows: [],
      emptyTitle: "Рынки ещё не настроены.",
      emptyDescription: "Добавьте рынок и цену. Автокотировки не выдумываются.",
      panel: (
        <>
          <AgroMarketsPanel
            headers={headers}
            canCreate={canCreateCore}
            canFinance={canFinance}
            markets={bundle.markets}
            prices={bundle.marketPrices}
            onChanged={() => void load()}
            onOpen={(kind, id) => setDrawer({ kind, id })}
            onAttach={(kind, id) => {
              setAttachEntity((f) => ({ ...f, entity_type: kind, entity_id: id }));
              setPanel("documents");
              go("documents");
            }}
            onCreateCalc={(prefill) => {
              setCalcForm((f) => ({ ...f, ...prefill }));
              setPanel("calculations");
              go("calculations");
            }}
            onConnectSource={() => go("intel")}
          />
          {extra}
        </>
      ),
    },
    logistics: {
      id: "logistics",
      title: "Логистика",
      description: "Перевозчики, транспорт, водители и рейсы, связанные со сделками и складами.",
      columns: [],
      rows: [],
      emptyTitle: "Транспорт ещё не добавлен.",
      emptyDescription: "Добавьте перевозчика, автомобиль и рейс.",
      panel: (
        <>
          <AgroLogisticsPanel
            headers={headers}
            canCreate={canCreateCore}
            counterparties={bundle.counterparties}
            vehicles={bundle.vehicles}
            carriers={bundle.carriers}
            trailers={bundle.trailers}
            drivers={bundle.drivers}
            trips={logisticsTrips}
            shipments={logisticsShipments}
            deals={bundle.deals}
            warehouses={bundle.warehouses}
            onChanged={() => void load()}
            onOpen={(kind, id) => setDrawer({ kind, id })}
            onAttach={(kind, id) => {
              setAttachEntity((f) => ({ ...f, entity_type: kind, entity_id: id }));
              setPanel("documents");
              go("documents");
            }}
          />
          {extra}
        </>
      ),
    },
    intel: {
      id: "intel",
      title: "Агро-разведка",
      description: "Утренние и вечерние обзоры только по реальным и ручным источникам.",
      columns: [],
      rows: [],
      panel: <AgroIntelPanel headers={headers} canOperate={caps.canOperate} canIntel={canIntel} />,
    },
    analytics: {
      id: "analytics",
      title: "Аналитика",
      description: "Главное заключение, изменения, риски и пробелы только по реальным данным.",
      columns: [],
      rows: [],
      panel: <AgroAnalyticsPanel headers={headers} canIntel={canIntel} />,
    },
    calendar: {
      id: "calendar",
      title: "Календарь",
      description: "Платежи, поставки, договоры, встречи, задачи.",
      columns: [],
      rows: [],
      panel: (
        <>
          <AgroCalendarPanel
            headers={headers}
            canOperate={Boolean(caps.canOperate) || agroRole === "agro_accountant"}
            events={bundle.calendar}
            onChanged={() => void load()}
            onOpen={(id) => setDrawer({ kind: "calendar", id })}
          />
          {extra}
        </>
      ),
      quickActions: caps.canOperate || agroRole === "agro_accountant" ? [{ label: "+ Создать событие", onClick: () => setPanel("calendar") }] : [],
    },
    tasks: {
      id: "tasks",
      title: "Задачи",
      description: "Операционные задачи агрокоманды.",
      columns: [
        { key: "title", label: "Задача" },
        { key: "due", label: "Срок" },
        { key: "status", label: "Статус" },
      ],
      rows: rowsFor("task", bundle.tasks, (r) => ({ title: pick(r, "title"), due: pick(r, "due_at"), status: ruStatus(pick(r, "status")) })),
      panel: extra,
      quickActions: caps.canOperate ? [{ label: "Создать задачу", onClick: () => setPanel("task") }] : [],
    },
    notifications: {
      id: "notifications",
      title: "Уведомления",
      description: "В приложении всегда. Telegram и эл. почта — только если реально настроены.",
      columns: [],
      rows: [],
      emptyTitle: "Пока нет сигналов.",
      panel: (
        <AgroNotificationsPanel
          headers={headers}
          canOperate={Boolean(caps.canOperate)}
          notifications={bundle.notifications}
          onChanged={() => void load()}
          onOpenLinked={(kind, id) => {
            if (kind === "counterparty" || kind === "deal" || kind === "agro_operation" || kind === "agro_field") {
              openEntity(kind, id, "notifications");
              return;
            }
            setDrawer({ kind, id });
          }}
          onCreateRule={() => go("notifications")}
          onCreateReminder={() => {
            setPanel("calendar");
            go("calendar");
          }}
        />
      ),
    },
    settings: {
      id: "settings",
      title: "Настройки",
      description: "Роли, источники, каналы уведомлений.",
      columns: [],
      rows: [],
      panel: (
        <AgroSettingsPanel
          headers={headers}
          roleLabel={roleLabel}
          agroRole={agroRole}
          providers={bundle.providers}
          channels={bundle.channels}
          canAdmin={agroRole === "agro_director"}
          initialTab={searchParams.get("tab") || undefined}
        />
      ),
    },
  };

  return (
    <>
    <AgroGlobalSearch
      open={searchOpen}
      headers={headers}
      onClose={() => setSearchOpen(false)}
      onOpen={(view, kind, id) => {
        setSearchOpen(false);
        if (kind === "counterparty" || kind === "deal" || kind === "agro_operation" || kind === "agro_field") openEntity(kind, id);
        else {
          go(view, { id });
          setDrawer({ kind, id });
        }
      }}
    />
    <AgroQuickCreateSheet
      open={quickSheet}
      kind={panel}
      canCreate={canCreateCore}
      canFinance={canFinance}
      insideOperation={currentView === "operations" && Boolean(entityId)}
      onSelect={(id) => {
        const tabMap: Record<string, string> = {
          weighing: "weighings",
          quality: "quality",
          expense: "expenses",
          documents: "documents",
          truck: "trucks",
          task: "tasks",
          sale: "sales",
        };
        if (currentView === "operations" && entityId && tabMap[id]) {
          go("operations", { id: entityId, tab: tabMap[id] });
          setQuickSheet(false);
          return;
        }
        setPanel(id);
      }}
      onClose={() => {
        setQuickSheet(false);
        setPanel(null);
      }}
    >
      {quickSheet ? extra : null}
    </AgroQuickCreateSheet>
    <BusinessCabinetShell
      verticalId="agro"
      title="Агро"
      subtitle={`${orgLabel} · ${ROLE_RU[agroRole] || roleLabel}`}
      nav={NAV}
      sections={sections}
      defaultSection="home"
      loading={loading}
      error={error}
      headerExtra={
        <Button size="sm" variant="ghost" className="min-h-11 min-w-11" onClick={() => setSearchOpen(true)} data-testid="agro-search-icon" aria-label="Поиск">
          Поиск
        </Button>
      }
      onRefresh={() => {
        loadedKinds.current.clear();
        void load();
      }}
      onBootstrap={
        canCreateCore
          ? async () => {
              await agroOpsBootstrap(headers);
              await load();
            }
          : undefined
      }
      bootstrapLabel="Загрузить демо AGRO"
      banner={
        bundle.dashboard.demo_mode ? (
          <div>
            <p className="eds-type-small font-medium">РЕЖИМ DEMO</p>
            <p className="eds-type-small">
              {String(
                bundle.dashboard.demo_notice_ru ||
                  "Загруженные демо-строки помечены [DEMO] и не используются в производственном анализе и обзорах.",
              )}
            </p>
          </div>
        ) : null
      }
      testId="agro-business-page"
      roleHint={ROLE_RU[agroRole] || roleLabel}
    />
    </>
  );
}
