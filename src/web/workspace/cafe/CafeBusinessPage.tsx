/**
 * Sprint 49.1 — Cafe venue cabinet: orders with event types, shifts, persistence via COS.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import {
  BusinessCabinetShell,
  type OpsNavItem,
  type OpsSection,
} from "../business-ops/BusinessCabinetShell";
import { asList, cosBootstrap, cosGet, cosPost, pick } from "../business-ops/opsApi";
import { resolveCabinetCaps } from "../business-ops/cabinetCapabilities";

const ORDER_TYPES = [
  "Обычный заказ",
  "Банкет",
  "День рождения",
  "Кейтеринг",
  "Караоке",
  "Закрытие заведения",
  "Beauty-мероприятие",
  "Корпоратив",
  "Другое мероприятие",
];

const NAV_BASE: OpsNavItem[] = [
  { id: "home", label: "Главная" },
  { id: "orders", label: "Заказы" },
  { id: "menu", label: "Меню" },
  { id: "shifts", label: "Смены" },
  { id: "clients", label: "Клиенты" },
  { id: "bookings", label: "Бронирования" },
  { id: "halls", label: "Залы и столы" },
  { id: "warehouse", label: "Склад" },
  { id: "cashier", label: "Касса" },
  { id: "staff", label: "Персонал" },
  { id: "marketing", label: "Маркетинг" },
  { id: "analytics", label: "Аналитика" },
  { id: "settings", label: "Настройки" },
];

type Bundle = {
  orders: Record<string, unknown>[];
  menu: Record<string, unknown>[];
  tables: Record<string, unknown>[];
  reservations: Record<string, unknown>[];
  staff: Record<string, unknown>[];
  customers: Record<string, unknown>[];
  shifts: Record<string, unknown>[];
  dashboard: Record<string, unknown>;
};

export function CafeBusinessPage() {
  const caps = resolveCabinetCaps("cafe");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderOpen, setOrderOpen] = useState(false);
  const [formMsg, setFormMsg] = useState<string | null>(null);
  const [bundle, setBundle] = useState<Bundle>({
    orders: [],
    menu: [],
    tables: [],
    reservations: [],
    staff: [],
    customers: [],
    shifts: [],
    dashboard: {},
  });
  const [orderForm, setOrderForm] = useState({
    order_type: "Обычный заказ",
    customer_id: "",
    table_id: "",
    item_id: "",
    guests: "2",
    comment: "",
    responsible: "",
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [o, m, t, r, s, c, sh, d] = await Promise.all([
        cosGet("/orders"),
        cosGet("/menu"),
        cosGet("/tables"),
        cosGet("/reservations"),
        cosGet("/staff"),
        cosGet("/customers"),
        cosGet("/shifts"),
        cosGet("/dashboard"),
      ]);
      if (![o, m, t, r, s, c, d].some((x) => x.ok || x.status === 404)) {
        setError("Cafe OS API недоступен. Запустите backend (:8080) или загрузите демо-данные.");
      }
      setBundle({
        orders: asList(o.json) as Record<string, unknown>[],
        menu: asList(m.json) as Record<string, unknown>[],
        tables: asList(t.json) as Record<string, unknown>[],
        reservations: asList(r.json) as Record<string, unknown>[],
        staff: asList(s.json) as Record<string, unknown>[],
        customers: asList(c.json) as Record<string, unknown>[],
        shifts: asList(sh.json) as Record<string, unknown>[],
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

  async function createOrder() {
    setFormMsg(null);
    const menuItem = bundle.menu.find(
      (x) => pick(x, "item_id", "id") === orderForm.item_id,
    );
    const items = menuItem
      ? [{ name: pick(menuItem, "name"), price: Number(menuItem.price || 0), qty: 1 }]
      : [{ name: "Позиция", price: 0, qty: 1 }];
    const res = await cosPost("/orders", {
      customer_id: orderForm.customer_id,
      table_id: orderForm.table_id,
      items,
      order_type: orderForm.order_type,
      guests: Number(orderForm.guests || 0),
      comment: orderForm.comment,
      responsible: orderForm.responsible,
    });
    if (!res.ok) {
      setFormMsg(String((res.json as { error?: string })?.error || "Не удалось создать заказ"));
      return;
    }
    setOrderOpen(false);
    setFormMsg("Заказ создан");
    await load();
  }

  async function openShift() {
    const staffId = pick(bundle.staff[0] || {}, "staff_id", "id");
    if (!staffId || staffId === "—") {
      setError("Сначала загрузите персонал (демо-данные).");
      return;
    }
    await cosPost("/shifts", { staff_id: staffId });
    await load();
  }

  async function closeShift(id: string) {
    await cosPost("/shifts", { shift_id: id, action: "close" });
    await load();
  }

  const nav = useMemo(
    () =>
      NAV_BASE.map((n) => ({
        ...n,
        hidden:
          (n.id === "analytics" && !caps.canSeeAnalytics) ||
          (n.id === "settings" && !caps.canConfigure) ||
          (n.id === "cashier" && !caps.canSeeFinance && !caps.canOperate) ||
          (caps.isCustomer && !["home", "menu", "bookings"].includes(n.id)),
      })),
    [caps],
  );

  const orderPanel = orderOpen && caps.canCreate ? (
    <Card title="Новый заказ">
      <div className="grid gap-2 sm:grid-cols-2" data-testid="cafe-order-form">
        <label className="eds-type-small">
          Тип заказа
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={orderForm.order_type}
            onChange={(e) => setOrderForm((f) => ({ ...f, order_type: e.target.value }))}
          >
            {ORDER_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Клиент
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={orderForm.customer_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, customer_id: e.target.value }))}
          >
            <option value="">Выберите</option>
            {bundle.customers.map((c) => (
              <option key={pick(c, "customer_id", "id")} value={pick(c, "customer_id", "id")}>
                {pick(c, "name")}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Стол
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={orderForm.table_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, table_id: e.target.value }))}
          >
            <option value="">Выберите</option>
            {bundle.tables.map((c) => (
              <option key={pick(c, "table_id", "id")} value={pick(c, "table_id", "id")}>
                {pick(c, "name")}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Позиция меню
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
            value={orderForm.item_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, item_id: e.target.value }))}
          >
            <option value="">Выберите</option>
            {bundle.menu.map((c) => (
              <option key={pick(c, "item_id", "id")} value={pick(c, "item_id", "id")}>
                {pick(c, "name")} · {pick(c, "price")}
              </option>
            ))}
          </select>
        </label>
        <Input
          placeholder="Гостей"
          value={orderForm.guests}
          onChange={(e) => setOrderForm((f) => ({ ...f, guests: e.target.value }))}
        />
        <Input
          placeholder="Ответственный"
          value={orderForm.responsible}
          onChange={(e) => setOrderForm((f) => ({ ...f, responsible: e.target.value }))}
        />
        <Input
          className="sm:col-span-2"
          placeholder="Комментарий"
          value={orderForm.comment}
          onChange={(e) => setOrderForm((f) => ({ ...f, comment: e.target.value }))}
        />
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="sm" className="ews-primary-cta" onClick={() => void createOrder()}>
          Создать заказ
        </Button>
        <Button size="sm" variant="secondary" onClick={() => setOrderOpen(false)}>
          Отмена
        </Button>
      </div>
      {formMsg ? <p className="mt-2 eds-type-caption">{formMsg}</p> : null}
    </Card>
  ) : null;

  const sections: Record<string, OpsSection> = useMemo(() => {
    const dash = bundle.dashboard;
    return {
      home: {
        id: "home",
        title: "Главная заведения",
        description: "Открытые заказы, брони, смена.",
        columns: [
          { key: "metric", label: "Показатель" },
          { key: "value", label: "Значение" },
        ],
        cards: [
          { label: "Заказы", value: String(bundle.orders.length) },
          { label: "Брони", value: String(bundle.reservations.length) },
          { label: "Смены", value: String(bundle.shifts.length) },
          { label: "Выручка", value: String(dash.revenue_today ?? "—") },
        ],
        rows: [{ metric: "Типы мероприятий", value: String(ORDER_TYPES.length) }],
        quickActions: caps.canCreate
          ? [
              { label: "+ Новый заказ", onClick: () => setOrderOpen(true) },
              { label: "Открыть смену", onClick: () => void openShift() },
              { label: "Меню", to: "/workspace/cafe?view=menu" },
            ]
          : [],
        panel: orderPanel,
      },
      orders: {
        id: "orders",
        title: "Заказы",
        description: `Типы: ${ORDER_TYPES.slice(0, 4).join(" · ")}…`,
        columns: [
          { key: "number", label: "Номер" },
          { key: "type", label: "Тип" },
          { key: "client", label: "Клиент" },
          { key: "table", label: "Стол" },
          { key: "owner", label: "Ответственный" },
          { key: "amount", label: "Сумма" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.orders.map((r, i) => ({
          id: pick(r, "order_id", "id") || String(i),
          number: pick(r, "order_id", "id"),
          type: pick(r, "order_type", "type") || "Обычный заказ",
          client: pick(r, "customer_id"),
          table: pick(r, "table_id"),
          owner: pick(r, "responsible") || "—",
          amount: pick(r, "total"),
          status: pick(r, "status"),
        })),
        statusFilterKey: "status",
        responsibleFilterKey: "owner",
        emptyTitle: "Пока нет заказов",
        emptyCtaLabel: "Создать первый заказ",
        emptyCtaOnClick: caps.canCreate ? () => setOrderOpen(true) : undefined,
        quickActions: caps.canCreate ? [{ label: "+ Новый заказ", onClick: () => setOrderOpen(true) }] : [],
        panel: orderPanel,
      },
      menu: {
        id: "menu",
        title: "Меню",
        description: "Кухня · бар · сеты.",
        columns: [
          { key: "name", label: "Название" },
          { key: "category", label: "Категория" },
          { key: "price", label: "Цена" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.menu.map((r, i) => ({
          id: pick(r, "item_id", "id") || String(i),
          name: pick(r, "name"),
          category: pick(r, "category"),
          price: pick(r, "price"),
          status: pick(r, "status") || "Доступно",
        })),
        statusFilterKey: "status",
        emptyTitle: "Пока нет позиций меню",
      },
      shifts: {
        id: "shifts",
        title: "Смены",
        description: "Открытие и закрытие смен персонала.",
        columns: [
          { key: "employee", label: "Сотрудник" },
          { key: "role", label: "Роль" },
          { key: "date", label: "Дата" },
          { key: "start", label: "Начало" },
          { key: "end", label: "Конец" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.shifts.map((r, i) => ({
          id: pick(r, "shift_id", "id") || String(i),
          employee: pick(r, "employee", "staff_id"),
          role: pick(r, "role"),
          date: pick(r, "date"),
          start: pick(r, "start"),
          end: pick(r, "end") || "—",
          status: pick(r, "status"),
        })),
        statusFilterKey: "status",
        emptyTitle: "Пока нет смен",
        emptyCtaLabel: "Открыть смену",
        emptyCtaOnClick: caps.canOperate ? () => void openShift() : undefined,
        quickActions: caps.canOperate ? [{ label: "Открыть смену", onClick: () => void openShift() }] : [],
        rowActions: caps.canOperate
          ? (row) =>
              String(row.status) === "Открыта" ? (
                <Button size="sm" variant="secondary" onClick={() => void closeShift(String(row.id))}>
                  Закрыть
                </Button>
              ) : null
          : undefined,
      },
      clients: {
        id: "clients",
        title: "Клиенты",
        description: "Общий CRM заведения.",
        columns: [
          { key: "name", label: "Имя" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.customers.map((r, i) => ({
          id: pick(r, "customer_id", "id") || String(i),
          name: pick(r, "name"),
          status: "Активен",
        })),
        emptyTitle: "Пока нет клиентов",
      },
      bookings: {
        id: "bookings",
        title: "Бронирования",
        description: "Столы и мероприятия.",
        columns: [
          { key: "when", label: "Дата/время" },
          { key: "client", label: "Клиент" },
          { key: "guests", label: "Гостей" },
          { key: "table", label: "Стол" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.reservations.map((r, i) => ({
          id: pick(r, "reservation_id", "id") || String(i),
          when: pick(r, "start"),
          client: pick(r, "customer_id"),
          guests: pick(r, "party_size", "covers"),
          table: pick(r, "table_id"),
          status: pick(r, "status"),
        })),
        statusFilterKey: "status",
        emptyTitle: "Пока нет бронирований",
      },
      halls: {
        id: "halls",
        title: "Залы и столы",
        description: "Список столов (без floorplan).",
        columns: [
          { key: "name", label: "Стол" },
          { key: "seats", label: "Мест" },
          { key: "zone", label: "Зона" },
        ],
        rows: bundle.tables.map((r, i) => ({
          id: pick(r, "table_id", "id") || String(i),
          name: pick(r, "name"),
          seats: pick(r, "seats"),
          zone: pick(r, "zone"),
        })),
        emptyTitle: "Пока нет столов",
      },
      warehouse: {
        id: "warehouse",
        title: "Склад",
        description: "Продукты и расходники.",
        columns: [
          { key: "name", label: "Название" },
          { key: "qty", label: "Остаток" },
        ],
        rows: [],
        emptyTitle: "Пока нет складских позиций",
      },
      cashier: {
        id: "cashier",
        title: "Касса",
        description: "Операционные чеки без платёжного шлюза.",
        columns: [
          { key: "id", label: "Чек" },
          { key: "amount", label: "Сумма" },
          { key: "status", label: "Статус" },
        ],
        rows: bundle.orders.map((r, i) => ({
          id: pick(r, "order_id", "id") || String(i),
          amount: pick(r, "total"),
          status: pick(r, "status"),
        })),
        emptyTitle: "Пока нет чеков",
      },
      staff: {
        id: "staff",
        title: "Персонал",
        description: "Роли заведения.",
        columns: [
          { key: "name", label: "Имя" },
          { key: "role", label: "Роль" },
        ],
        rows: bundle.staff.map((r, i) => ({
          id: pick(r, "staff_id", "id") || String(i),
          name: pick(r, "name"),
          role: pick(r, "role"),
        })),
        emptyTitle: "Пока нет персонала",
      },
      marketing: {
        id: "marketing",
        title: "Маркетинг",
        description: "Без внешней отправки без интеграции.",
        columns: [
          { key: "campaign", label: "Кампания" },
          { key: "status", label: "Статус" },
        ],
        rows: [{ campaign: "Постоянные гости", status: "Черновик" }],
      },
      analytics: {
        id: "analytics",
        title: "Аналитика",
        description: "Выручка и заказы.",
        columns: [
          { key: "metric", label: "Метрика" },
          { key: "value", label: "Значение" },
        ],
        cards: [
          { label: "Заказы", value: String(bundle.orders.length) },
          { label: "Брони", value: String(bundle.reservations.length) },
        ],
        rows: [{ metric: "Источник", value: "Cafe OS dashboard" }],
      },
      settings: {
        id: "settings",
        title: "Настройки",
        description: "Заведение и типы заказов.",
        columns: [
          { key: "item", label: "Параметр" },
          { key: "value", label: "Значение" },
        ],
        rows: [
          { item: "Cafe OS API", value: "/api/enterprise-cos/v1" },
          { item: "Типы заказов", value: String(ORDER_TYPES.length) },
        ],
      },
    };
  }, [bundle, caps, orderPanel]);

  return (
    <BusinessCabinetShell
      verticalId="cafe"
      title="Cafe"
      subtitle="Заказы · меню · смены · брони · касса"
      nav={nav}
      sections={sections}
      loading={loading}
      error={error}
      roleHint={caps.roleLabel}
      onRefresh={() => void load()}
      onBootstrap={
        caps.canConfigure
          ? () => {
              void cosBootstrap().then(() => load());
            }
          : undefined
      }
      testId="cafe-business-cabinet"
    />
  );
}
