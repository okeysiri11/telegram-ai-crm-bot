/**
 * Sprint 49.1 — Beauty business cabinet: appointments create/cancel + persistence via BOS.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import {
  BusinessCabinetShell,
  type OpsNavItem,
  type OpsSection,
} from "../business-ops/BusinessCabinetShell";
import { asList, bosBootstrap, bosGet, bosPost, pick } from "../business-ops/opsApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";

const NAV_BASE: OpsNavItem[] = [
  { id: "home", label: "Главная" },
  { id: "clients", label: "Клиенты" },
  { id: "services", label: "Услуги" },
  { id: "products", label: "Товары" },
  { id: "bookings", label: "Записи" },
  { id: "calendar", label: "Календарь" },
  { id: "staff", label: "Мастера" },
  { id: "shifts", label: "Смены" },
  { id: "sales", label: "Продажи" },
  { id: "analytics", label: "Аналитика" },
  { id: "marketing", label: "Маркетинг" },
  { id: "warehouse", label: "Склад" },
  { id: "finance", label: "Финансы" },
  { id: "settings", label: "Настройки" },
];

type Bundle = {
  customers: Record<string, unknown>[];
  services: Record<string, unknown>[];
  appointments: Record<string, unknown>[];
  employees: Record<string, unknown>[];
  branches: Record<string, unknown>[];
  dashboard: Record<string, unknown>;
};

function defaultEnd(start: string): string {
  if (!start) return "";
  const d = new Date(start);
  if (Number.isNaN(d.getTime())) return start;
  d.setMinutes(d.getMinutes() + 60);
  return d.toISOString().slice(0, 16);
}

export function BeautyBusinessPage() {
  const caps = resolveCabinetCaps("beauty");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [clientOpen, setClientOpen] = useState(false);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [bundle, setBundle] = useState<Bundle>({
    customers: [],
    services: [],
    appointments: [],
    employees: [],
    branches: [],
    dashboard: {},
  });

  const [apptForm, setApptForm] = useState({
    customer_id: "",
    service_id: "",
    employee_id: "",
    start: "",
    end: "",
  });
  const [clientForm, setClientForm] = useState({ name: "", preferences: "" });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [c, s, a, e, b, d] = await Promise.all([
        bosGet("/customers"),
        bosGet("/services"),
        bosGet("/appointments"),
        bosGet("/employees"),
        bosGet("/branches"),
        bosGet("/dashboard"),
      ]);
      if (![c, s, a, e, d].some((x) => x.ok || x.status === 404)) {
        setError("Beauty OS API недоступен. Запустите backend (:8080) или загрузите демо-данные.");
      }
      setBundle({
        customers: asList(c.json) as Record<string, unknown>[],
        services: asList(s.json) as Record<string, unknown>[],
        appointments: asList(a.json) as Record<string, unknown>[],
        employees: asList(e.json) as Record<string, unknown>[],
        branches: asList(b.json) as Record<string, unknown>[],
        dashboard: (d.json && typeof d.json === "object" ? d.json : {}) as Record<string, unknown>,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createAppointment() {
    setFormMsg(null);
    const start = apptForm.start;
    const end = apptForm.end || defaultEnd(start);
    const res = await bosPost("/appointments", {
      customer_id: apptForm.customer_id,
      service_id: apptForm.service_id,
      employee_id: apptForm.employee_id,
      start,
      end,
    });
    if (!res.ok) {
      setFormMsg(String((res.json as { error?: string })?.error || "Не удалось создать запись"));
      return;
    }
    setFormMsg("Запись создана");
    setFormOpen(false);
    await load();
  }

  async function cancelAppointment(id: string) {
    const res = await bosPost("/appointments", { appointment_id: id, status: "cancelled" });
    if (!res.ok) {
      setError(String((res.json as { error?: string })?.error || "Не удалось отменить"));
      return;
    }
    await load();
  }

  async function createClient() {
    setFormMsg(null);
    const res = await bosPost("/customers", {
      name: clientForm.name,
      preferences: clientForm.preferences ? [clientForm.preferences] : [],
    });
    if (!res.ok) {
      setFormMsg(String((res.json as { error?: string })?.error || "Ошибка создания клиента"));
      return;
    }
    setClientOpen(false);
    setClientForm({ name: "", preferences: "" });
    await load();
  }

  const nav = useMemo(
    () =>
      NAV_BASE.map((n) => ({
        ...n,
        hidden:
          (n.id === "analytics" && !caps.canSeeAnalytics) ||
          (n.id === "finance" && !caps.canSeeFinance) ||
          (n.id === "settings" && !caps.canConfigure) ||
          (caps.isCustomer && !["home", "bookings", "services"].includes(n.id)),
      })),
    [caps],
  );

  const appointmentPanel = formOpen && caps.canCreate ? (
    <Card title="Новая запись">
      <div className="grid gap-2 sm:grid-cols-2" data-testid="beauty-appointment-form">
        <label className="eds-type-small">
          Клиент
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={apptForm.customer_id}
            onChange={(e) => setApptForm((f) => ({ ...f, customer_id: e.target.value }))}
          >
            <option value="">Выберите</option>
            {bundle.customers.map((c) => (
              <option key={pick(c, "customer_id", "id")} value={pick(c, "customer_id", "id")}>
                {pick(c, "name", "full_name")}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Услуга
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={apptForm.service_id}
            onChange={(e) => setApptForm((f) => ({ ...f, service_id: e.target.value }))}
          >
            <option value="">Выберите</option>
            {bundle.services.map((c) => (
              <option key={pick(c, "service_id", "id")} value={pick(c, "service_id", "id")}>
                {pick(c, "name", "title")}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Мастер
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={apptForm.employee_id}
            onChange={(e) => setApptForm((f) => ({ ...f, employee_id: e.target.value }))}
          >
            <option value="">Выберите</option>
            {bundle.employees.map((c) => (
              <option key={pick(c, "employee_id", "id")} value={pick(c, "employee_id", "id")}>
                {pick(c, "name", "full_name")}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Начало
          <Input
            type="datetime-local"
            className="mt-1"
            value={apptForm.start}
            onChange={(e) =>
              setApptForm((f) => ({
                ...f,
                start: e.target.value,
                end: f.end || defaultEnd(e.target.value),
              }))
            }
          />
        </label>
        <label className="eds-type-small">
          Конец
          <Input
            type="datetime-local"
            className="mt-1"
            value={apptForm.end}
            onChange={(e) => setApptForm((f) => ({ ...f, end: e.target.value }))}
          />
        </label>
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="sm" className="ews-primary-cta" onClick={() => void createAppointment()}>
          Сохранить запись
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setFormOpen(false)}>
          Отмена
        </Button>
      </div>
      {formMsg ? <p className="mt-2 eds-type-caption">{formMsg}</p> : null}
    </Card>
  ) : null;

  const clientPanel = clientOpen && caps.canCreate ? (
    <Card title="Новый клиент">
      <div className="grid gap-2 sm:grid-cols-2" data-testid="beauty-client-form">
        <Input
          placeholder="Имя"
          value={clientForm.name}
          onChange={(e) => setClientForm((f) => ({ ...f, name: e.target.value }))}
        />
        <Input
          placeholder="Предпочтения"
          value={clientForm.preferences}
          onChange={(e) => setClientForm((f) => ({ ...f, preferences: e.target.value }))}
        />
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="sm" className="ews-primary-cta" onClick={() => void createClient()}>
          Сохранить
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setClientOpen(false)}>
          Отмена
        </Button>
      </div>
    </Card>
  ) : null;

  const sections: Record<string, OpsSection> = useMemo(() => {
    const dash = bundle.dashboard;
    return {
      home: {
        id: "home",
        title: "Главная салона",
        description: "Операционный обзор Beauty.",
        columns: [
          { key: "metric", label: "Показатель" },
          { key: "value", label: "Значение" },
        ],
        cards: [
          { label: "Записи", value: String(bundle.appointments.length) },
          { label: "Клиенты", value: String(bundle.customers.length) },
          { label: "Услуги", value: String(bundle.services.length) },
          { label: "Мастера", value: String(bundle.employees.length) },
        ],
        rows: [
          { metric: "Выручка сегодня", value: String(dash.revenue_today ?? "—") },
          { metric: "Отмены", value: String(dash.cancellations ?? "0") },
        ],
        quickActions: caps.canCreate
          ? [
              { label: "+ Новая запись", onClick: () => setFormOpen(true) },
              { label: "+ Клиент", onClick: () => setClientOpen(true) },
              { label: "Календарь", to: "/workspace/beauty?view=calendar" },
            ]
          : [{ label: "Мои записи", to: "/workspace/beauty?view=bookings" }],
        panel: (
          <>
            {appointmentPanel}
            {clientPanel}
          </>
        ),
      },
      clients: {
        id: "clients",
        title: "Клиенты",
        description: "CRM салона.",
        columns: [
          { key: "name", label: "Имя" },
          { key: "prefs", label: "Предпочтения" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.customers.map((r, i) => ({
          id: pick(r, "customer_id", "id") || String(i),
          name: pick(r, "name", "full_name"),
          prefs: Array.isArray(r.preferences) ? (r.preferences as string[]).join(", ") : pick(r, "preferences"),
          status: pick(r, "status") || "Активен",
        })),
        statusFilterKey: "status",
        emptyTitle: "Пока нет клиентов",
        emptyCtaLabel: "Создать первого клиента",
        emptyCtaOnClick: caps.canCreate ? () => setClientOpen(true) : undefined,
        quickActions: caps.canCreate ? [{ label: "+ Клиент", onClick: () => setClientOpen(true) }] : [],
        panel: clientPanel,
      },
      services: {
        id: "services",
        title: "Услуги",
        description: "Прайс салона.",
        columns: [
          { key: "name", label: "Название" },
          { key: "category", label: "Категория" },
          { key: "duration", label: "Длительность" },
          { key: "price", label: "Цена" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.services.map((r, i) => ({
          id: pick(r, "service_id", "id") || String(i),
          name: pick(r, "name"),
          category: pick(r, "category"),
          duration: pick(r, "duration_min", "duration"),
          price: pick(r, "price"),
          status: pick(r, "status") || "Активна",
        })),
        statusFilterKey: "status",
        emptyTitle: "Пока нет услуг",
      },
      products: {
        id: "products",
        title: "Товары",
        description: "Требуется наполнение склада.",
        columns: [
          { key: "name", label: "Название" },
          { key: "status", label: "Статус" },
        ],
        rows: [],
        emptyTitle: "Пока нет товаров",
        integrationNote: "Каталог товаров: требуется настройка склада.",
      },
      bookings: {
        id: "bookings",
        title: "Записи",
        description: "Создание, отмена и просмотр записей.",
        columns: [
          { key: "date", label: "Дата" },
          { key: "time", label: "Время" },
          { key: "client", label: "Клиент" },
          { key: "service", label: "Услуга" },
          { key: "master", label: "Мастер" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.appointments.map((r, i) => {
          const start = pick(r, "start");
          return {
            id: pick(r, "appointment_id", "id") || String(i),
            date: start.slice(0, 10),
            time: start.includes("T") ? start.slice(11, 16) : start,
            client: pick(r, "customer_id"),
            service: pick(r, "service_id"),
            master: pick(r, "employee_id"),
            status: pick(r, "status"),
          };
        }),
        statusFilterKey: "status",
        responsibleFilterKey: "master",
        dateFilterKey: "date",
        emptyTitle: "Пока нет записей",
        emptyCtaLabel: "Создать первую запись",
        emptyCtaOnClick: caps.canCreate ? () => setFormOpen(true) : undefined,
        quickActions: caps.canCreate ? [{ label: "+ Новая запись", onClick: () => setFormOpen(true) }] : [],
        panel: appointmentPanel,
        rowActions: caps.canOperate
          ? (row) =>
              String(row.status) !== "cancelled" ? (
                <Button size="sm" variant="secondary" onClick={() => void cancelAppointment(String(row.id))}>
                  Отменить
                </Button>
              ) : null
          : undefined,
      },
      calendar: {
        id: "calendar",
        title: "Календарь",
        description: "Список записей по дате (недельная сетка — следующий спринт).",
        columns: [
          { key: "when", label: "Когда" },
          { key: "master", label: "Мастер" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.appointments.map((r, i) => ({
          id: pick(r, "appointment_id", "id") || String(i),
          when: pick(r, "start"),
          master: pick(r, "employee_id"),
          status: pick(r, "status"),
        })),
        statusFilterKey: "status",
        dateFilterKey: "when",
        emptyTitle: "Пока нет записей в календаре",
        emptyCtaLabel: "Создать первую запись",
        emptyCtaOnClick: caps.canCreate ? () => setFormOpen(true) : undefined,
        panel: appointmentPanel,
      },
      staff: {
        id: "staff",
        title: "Мастера",
        description: "Сотрудники салона.",
        columns: [
          { key: "name", label: "Имя" },
          { key: "role", label: "Роль" },
          { key: "spec", label: "Специализация" },
        ],
        rows: bundle.employees.map((r, i) => ({
          id: pick(r, "employee_id", "id") || String(i),
          name: pick(r, "name"),
          role: pick(r, "role"),
          spec: pick(r, "specialization"),
        })),
        emptyTitle: "Пока нет мастеров",
      },
      shifts: {
        id: "shifts",
        title: "Смены",
        description: "Расписание смен мастеров.",
        columns: [
          { key: "employee", label: "Сотрудник" },
          { key: "role", label: "Роль" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.employees.map((r, i) => ({
          id: pick(r, "employee_id", "id") || String(i),
          employee: pick(r, "name"),
          role: pick(r, "role"),
          status: "По расписанию",
        })),
        emptyTitle: "Пока нет смен",
      },
      sales: {
        id: "sales",
        title: "Продажи",
        description: "Чеки и оплаты — без фейкового эквайринга.",
        columns: [
          { key: "date", label: "Дата" },
          { key: "amount", label: "Сумма" },
          { key: "method", label: "Способ оплаты" },
          { key: "status", label: "Статус" },
        ],
        rows: [],
        emptyTitle: "Пока нет продаж",
        integrationNote: "Наличные / Карта / Перевод — учёт после кассовой интеграции.",
      },
      analytics: {
        id: "analytics",
        title: "Аналитика",
        description: "Операционные метрики салона.",
        columns: [
          { key: "metric", label: "Метрика" },
          { key: "value", label: "Значение" },
        ],
        cards: [
          { label: "Записи", value: String(bundle.appointments.length) },
          { label: "Клиенты", value: String(bundle.customers.length) },
        ],
        rows: [{ metric: "Источник", value: "Beauty OS dashboard" }],
      },
      marketing: {
        id: "marketing",
        title: "Маркетинг",
        description: "Сегменты без внешней отправки без интеграции.",
        columns: [
          { key: "segment", label: "Сегмент" },
          { key: "status", label: "Статус" },
        ],
        rows: [
          { segment: "Дни рождения", status: "Требуется настройка" },
          { segment: "Не посещали 30 дней", status: "Требуется настройка" },
        ],
      },
      warehouse: {
        id: "warehouse",
        title: "Склад",
        description: "Остатки.",
        columns: [
          { key: "name", label: "Название" },
          { key: "qty", label: "Остаток" },
        ],
        rows: [],
        emptyTitle: "Пока нет позиций склада",
      },
      finance: {
        id: "finance",
        title: "Финансы",
        description: "Базовый обзор (не бухгалтерия).",
        columns: [
          { key: "metric", label: "Показатель" },
          { key: "value", label: "Значение" },
        ],
        rows: [
          { metric: "Выручка", value: String(dash.revenue_today ?? "—") },
          { metric: "Возвраты", value: "0" },
        ],
      },
      settings: {
        id: "settings",
        title: "Настройки",
        description: "Интеграции салона.",
        columns: [
          { key: "item", label: "Параметр" },
          { key: "value", label: "Значение" },
        ],
        rows: [
          { item: "Beauty OS API", value: "/api/enterprise-bos/v1" },
          { item: "Google Calendar", value: "Не подключено" },
          { item: "Филиалы", value: String(bundle.branches.length) },
        ],
      },
    };
  }, [bundle, caps, appointmentPanel, clientPanel]);

  return (
    <BusinessCabinetShell
      verticalId="beauty"
      title="Beauty"
      subtitle="Салон · записи · клиенты · продажи"
      nav={nav}
      sections={sections}
      loading={loading}
      error={error}
      roleHint={caps.roleLabel}
      onRefresh={() => void load()}
      onBootstrap={
        caps.canConfigure
          ? () => {
              void bosBootstrap().then(() => load());
            }
          : undefined
      }
      testId="beauty-business-cabinet"
    />
  );
}
