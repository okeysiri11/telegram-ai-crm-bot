/**
 * AGRO 2.0 — operational command center (home of /workspace/agro).
 * Compact cards + drill-down. Real values only; empty → 0 / Нет данных.
 */

import { useEffect, useState, type ReactNode } from "react";
import { Button, Card } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { QUICK_CREATE_ACTIONS } from "./AgroQuickCreateSheet";

export type CcSummary = {
  id: string;
  label_ru: string;
  value: number | string | null;
  unit?: string | null;
  hint_ru?: string;
  view?: string;
  filter?: string;
  empty?: boolean;
  masked?: boolean;
};

export type CcEvent = {
  id: string;
  severity: string;
  severity_ru: string;
  title: string;
  explanation: string;
  entity_type?: string;
  entity_id?: string;
  entity_label?: string;
  responsible?: string | null;
  deadline?: string | null;
  action_ru?: string;
  view?: string;
  is_demo?: boolean;
};

export type CommandCenterPayload = {
  version?: string;
  role?: string;
  blocks?: string[];
  can_create?: boolean;
  can_finance?: boolean;
  can_margins?: boolean;
  summary?: CcSummary[];
  today?: CcEvent[];
  deals?: { pipeline?: { id: string; label_ru: string; count: number; value?: number | null; pipeline?: string }[]; items?: Record<string, unknown>[] };
  shipments?: { stages?: { id: string; label_ru: string; count: number }[]; items?: Record<string, unknown>[] };
  warehouses?: { items?: Record<string, unknown>[]; receipt_today?: number; issue_today?: number; top_crops?: { name: string; quantity: number }[] };
  markets?: Record<string, unknown>[];
  weather?: { regions?: Record<string, unknown>[]; has_data?: boolean };
  intel?: Record<string, unknown>[];
  tasks?: { today?: Record<string, unknown>[]; overdue?: Record<string, unknown>[]; week?: Record<string, unknown>[]; meetings?: Record<string, unknown>[] };
  notifications?: { unread?: number; by_category?: { id: string; label_ru: string; count: number }[] };
  sources_status?: { ok?: boolean; label_ru?: string; href?: string; issues?: number };
  grain_today?: { id: string; label_ru: string; value: number; view?: string; filter?: string }[];
  agronomist_today?: { id: string; label_ru: string; value: number; view?: string; filter?: string }[];
  kpis_26?: { id: string; label_ru: string; value: number | null; view?: string; filter?: string }[];
  director_production?: {
    land_bank_ha?: number | null;
    sown_ha?: number | null;
    work_completion_pct?: number | null;
    fuel?: number | null;
    harvest_tonnes?: number | null;
    yield_t_ha?: number | null;
    cost_ha?: number | null;
    cost_t?: number | null;
    crop_structure?: { crop: string; pct: number }[];
    kpis_26?: { id: string; label_ru: string; value: number | null; view?: string; filter?: string }[];
  };
  grain_stock?: { by_crop?: { crop: string; quantity: number }[]; by_warehouse?: { warehouse_id: string; quantity: number }[]; lots?: Record<string, unknown>[] };
  ops_version?: string;
  production_version?: string;
  cash?: { empty?: boolean; empty_ru?: string; mixed?: boolean; by_currency?: { currency: string; amount: number }[]; forbidden?: boolean };
  harvest?: { empty?: boolean; empty_ru?: string };
  timezone?: string;
  currency?: string;
};

function fmt(value: number | string | null | undefined, empty: boolean | undefined, unit?: string | null) {
  if (value === null || value === undefined || empty) {
    if (typeof value === "number") return unit ? `0 ${unit}` : "0";
    return "Нет данных";
  }
  if (typeof value === "number") {
    const n = Number.isInteger(value) ? String(value) : value.toLocaleString("ru-RU");
    return unit ? `${n} ${unit}` : n;
  }
  const s = String(value).trim();
  return s || "Нет данных";
}

function nd(value: unknown): string {
  if (value === null || value === undefined || value === "" || value === false) return "Нет данных";
  const s = String(value).trim();
  return s || "Нет данных";
}

const SEV_CLASS: Record<string, string> = {
  CRITICAL: "text-[var(--ew-danger,#b91c1c)]",
  HIGH: "text-[#b45309]",
  MEDIUM: "text-[var(--ew-muted)]",
  INFO: "text-[var(--ew-muted)]",
};

function Block(props: { id: string; title: string; mobile: boolean; defaultOpen?: boolean; children: ReactNode; testId: string }) {
  if (!props.mobile) {
    return (
      <section data-testid={props.testId} className="min-w-0">
        <h3 className="mb-2 font-semibold">{props.title}</h3>
        {props.children}
      </section>
    );
  }
  return (
    <details open={props.defaultOpen} data-testid={props.testId} className="rounded-lg border border-[var(--ew-border)] p-3">
      <summary className="min-h-11 cursor-pointer font-semibold">{props.title}</summary>
      <div className="mt-3">{props.children}</div>
    </details>
  );
}

export function AgroCommandCenter(props: {
  payload: CommandCenterPayload;
  roleLabel: string;
  canCreate: boolean;
  canFinance: boolean;
  canOperate: boolean;
  onGo: (view: string, extra?: Record<string, string>) => void;
  onOpen: (kind: string, id: string) => void;
  onQuick: () => void;
  onQuickKind: (id: string) => void;
  onSearch: () => void;
  onNotify: () => void;
  onTask: (id: string, action: "done" | "reschedule" | "open") => void;
  onAttach: (kind: string, id: string) => void;
}) {
  const mobile = useIsMobile();
  const cc = props.payload || {};
  const summary = cc.summary || [];
  const today = cc.today || [];
  const [bellOpen, setBellOpen] = useState(false);
  const unread = cc.notifications?.unread || 0;

  return (
    <div data-testid="agro-command-center" className={mobile ? "grid gap-4 overflow-x-hidden" : "grid gap-5"}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="eds-type-caption text-[var(--ew-muted)]">АГРО</p>
          <h2 className="eds-type-title text-xl" data-testid="agro-cc-title">
            АГРО — ОПЕРАЦИОННЫЙ ЦЕНТР
          </h2>
          <p className="eds-type-small text-[var(--ew-muted)]">{props.roleLabel}</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" className="min-h-11 min-w-11" onClick={props.onSearch} data-testid="agro-cc-search" aria-label="Поиск">
            Поиск
          </Button>
          <Button
            size="sm"
            variant="ghost"
            className="min-h-11 min-w-11"
            onClick={() => {
              setBellOpen((v) => !v);
              props.onNotify();
            }}
            data-testid="agro-cc-bell"
            aria-label="Уведомления"
          >
            🔔{unread ? ` ${unread}` : ""}
          </Button>
        </div>
      </div>

      {bellOpen ? (
        <Card title="Уведомления" data-testid="agro-cc-bell-panel">
          {(cc.notifications?.by_category || []).length ? (
            <ul className="eds-type-small">
              {(cc.notifications?.by_category || []).map((c) => (
                <li key={c.id}>
                  {c.label_ru}: {c.count}
                </li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">Нет данных</p>
          )}
          <Button className="mt-2 min-h-11" size="sm" variant="ghost" onClick={() => props.onGo("notifications")}>
            Открыть центр уведомлений
          </Button>
        </Card>
      ) : null}

      <div
        data-testid="agro-cc-summary"
        className={mobile ? "flex gap-2 overflow-x-auto pb-1" : "grid gap-3 sm:grid-cols-3 xl:grid-cols-6"}
      >
        {summary.map((card) => (
          <button
            key={card.id}
            type="button"
            data-testid={`agro-cc-summary-${card.id}`}
            className={`min-h-11 rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-3 text-left ${mobile ? "min-w-[160px] shrink-0" : ""}`}
            onClick={() => props.onGo(card.view || "home", card.filter ? { filter: card.filter } : undefined)}
          >
            <p className="eds-type-caption text-[var(--ew-muted)]">{card.label_ru}</p>
            <p className="text-xl font-semibold">{card.masked ? "—" : fmt(card.value, card.empty && card.value === 0 && card.id !== "deals" && card.id !== "shipments" && card.id !== "overdue" && card.id !== "critical" ? false : card.empty && card.value == null, card.unit)}</p>
            <p className="eds-type-small text-[var(--ew-muted)]">{card.hint_ru || "Нет данных"}</p>
          </button>
        ))}
      </div>

      <section data-testid="agro-cc-today">
        <h3 className="mb-2 font-semibold">ВАЖНО СЕГОДНЯ</h3>
        {!today.length ? (
          <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p>
        ) : (
          <ul className="grid gap-2">
            {today.map((ev) => (
              <li key={ev.id} className="rounded-lg border border-[var(--ew-border)] p-3" data-testid="agro-cc-today-item">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className={`eds-type-caption ${SEV_CLASS[ev.severity] || ""}`}>{ev.severity_ru}</p>
                    <p className="font-medium">
                      {ev.is_demo ? "[DEMO] " : ""}
                      {ev.title}
                    </p>
                    <p className="eds-type-small">{ev.explanation}</p>
                    <p className="eds-type-caption text-[var(--ew-muted)]">
                      {ev.entity_label || "Нет данных"} · {ev.responsible || "Нет данных"} · {ev.deadline ? String(ev.deadline).slice(0, 10) : "Нет данных"}
                    </p>
                  </div>
                  <Button size="sm" className="min-h-11" onClick={() => (ev.entity_id && ev.entity_type && ev.entity_type !== "weather" ? props.onOpen(ev.entity_type, String(ev.entity_id)) : props.onGo(ev.view || "home"))}>
                    {ev.action_ru || "Открыть"}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {(cc.grain_today || []).length ? (
        <section data-testid="agro-cc-grain-today">
          <h3 className="mb-2 font-semibold">{mobile ? "ОПЕРАЦИИ СЕГОДНЯ" : "СЕГОДНЯ"}</h3>
          <div className={mobile ? "grid grid-cols-2 gap-2" : "grid gap-2 sm:grid-cols-5"}>
            {(cc.grain_today || []).map((m) => (
              <button
                key={m.id}
                type="button"
                className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
                data-testid={`agro-grain-${m.id}`}
                onClick={() => props.onGo(m.view || "operations", m.filter ? { filter: m.filter } : undefined)}
              >
                <p className="eds-type-caption text-[var(--ew-muted)]">{m.label_ru}</p>
                <p className="text-lg font-semibold">{m.value ?? 0}</p>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {(cc.agronomist_today || []).length ? (
        <section data-testid="agro-cc-agronomist-today">
          <h3 className="mb-2 font-semibold">Сегодня</h3>
          <div className={mobile ? "grid grid-cols-2 gap-2" : "grid gap-2 sm:grid-cols-4"}>
            {(cc.agronomist_today || []).map((m) => (
              <button
                key={m.id}
                type="button"
                className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
                data-testid={`agro-prod-${m.id}`}
                onClick={() => props.onGo(m.view || "fields", m.filter ? { filter: m.filter } : undefined)}
              >
                <p className="eds-type-caption text-[var(--ew-muted)]">{m.label_ru}</p>
                <p className="text-lg font-semibold">{m.value ?? 0}</p>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {(cc.kpis_26 || cc.director_production?.kpis_26 || []).length ? (
        <section data-testid="agro-cc-kpis-26">
          <h3 className="mb-2 font-semibold">Производство 2.6</h3>
          <div className={mobile ? "grid grid-cols-2 gap-2" : "grid gap-2 sm:grid-cols-5"}>
            {(cc.kpis_26 || cc.director_production?.kpis_26 || []).map((m) => (
              <button
                key={m.id}
                type="button"
                className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
                data-testid={`agro-kpi26-${m.id}`}
                onClick={() => props.onGo(m.view || "fields", m.filter ? { filter: m.filter } : undefined)}
              >
                <p className="eds-type-caption text-[var(--ew-muted)]">{m.label_ru}</p>
                <p className="text-lg font-semibold">{m.value == null ? "Нет данных" : m.value}</p>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {cc.director_production ? (
        <section data-testid="agro-cc-director-prod">
          <h3 className="mb-2 font-semibold">Директор</h3>
          <div className={mobile ? "grid grid-cols-2 gap-2" : "grid gap-2 sm:grid-cols-4"}>
            {[
              ["land", "Земельный банк", cc.director_production.land_bank_ha, "ha"],
              ["sown", "Посеяно", cc.director_production.sown_ha, "ha"],
              ["work", "Работы %", cc.director_production.work_completion_pct, "%"],
              ["fuel", "Топливо", cc.director_production.fuel, null],
              ["harvest", "Урожай", cc.director_production.harvest_tonnes, "т"],
              ["yield", "Урожайность", cc.director_production.yield_t_ha, "т/га"],
              ["costha", "Себестоимость /га", cc.director_production.cost_ha, "грн"],
              ["costt", "Себестоимость /т", cc.director_production.cost_t, "грн"],
            ].map(([id, label, value, unit]) => (
              <button key={String(id)} type="button" className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left" onClick={() => props.onGo("fields")}>
                <p className="eds-type-caption">{label}</p>
                <p className="font-semibold">{value == null ? "нет данных" : `${value}${unit ? ` ${unit}` : ""}`}</p>
              </button>
            ))}
          </div>
          {(cc.director_production.crop_structure || []).length ? (
            <ul className="mt-2" data-testid="agro-crop-structure">
              {cc.director_production.crop_structure!.map((c) => (
                <li key={c.crop} className="eds-type-small">{c.crop} {c.pct}%</li>
              ))}
            </ul>
          ) : (
            <p className="eds-type-small">нет данных</p>
          )}
        </section>
      ) : null}

      <section data-testid="agro-cc-quick">
        <h3 className="mb-2 font-semibold">БЫСТРЫЕ ДЕЙСТВИЯ</h3>
        <div className={mobile ? "grid grid-cols-2 gap-2" : "flex flex-wrap gap-2"}>
          {QUICK_CREATE_ACTIONS.filter((a) => {
            if (a.finance && !props.canFinance) return false;
            if (a.create && !props.canCreate) return a.id === "documents" || a.id === "task" || a.id === "calendar";
            return true;
          }).map((a) => (
            <Button key={a.id} size="sm" variant="secondary" className="min-h-11" onClick={() => props.onQuickKind(a.id)}>
              {a.label}
            </Button>
          ))}
        </div>
      </section>

      {cc.sources_status ? (
        <p className="eds-type-small" data-testid="agro-cc-sources">
          {cc.sources_status.label_ru || "Нет данных"}{" "}
          <button type="button" className="underline" onClick={() => props.onGo("settings", { tab: cc.sources_status?.ok ? "sources" : "diagnostics" })}>
            Подробнее
          </button>
        </p>
      ) : null}

      <Block id="deals" title="СДЕЛКИ" mobile={mobile} defaultOpen={!mobile} testId="agro-cc-deals">
        <div className={mobile ? "grid gap-2" : "grid grid-cols-4 gap-2 xl:grid-cols-8"} data-testid="agro-cc-pipeline">
          {(cc.deals?.pipeline || []).map((st) => (
            <button
              key={st.id}
              type="button"
              className="min-h-11 rounded-md border border-[var(--ew-border)] p-2 text-left"
              onClick={() => props.onGo("deals", { pipeline: st.id })}
            >
              <p className="eds-type-caption">{st.label_ru}</p>
              <p className="font-semibold">{st.count}</p>
              <p className="eds-type-caption text-[var(--ew-muted)]">{st.value != null ? st.value.toLocaleString("ru-RU") : "Нет данных"}</p>
            </button>
          ))}
        </div>
        {(cc.deals?.items || []).length ? (
          <ul className="mt-2 eds-type-small">
            {(cc.deals?.items || []).map((d) => (
              <li key={String(d.id)} className="flex items-center justify-between gap-2 border-b border-[var(--ew-border)] py-2">
                <button type="button" className="min-h-11 text-left underline" onClick={() => props.onOpen("deal", String(d.id))}>
                  {Boolean(d.is_demo) ? "[DEMO] " : ""}
                  {String(d.title)} · {nd(d.counterparty)} · {nd(d.crop)} · {d.volume != null ? `${d.volume} ${d.unit || "т"}` : "Нет данных"}
                </button>
                <Button size="sm" variant="ghost" className="min-h-11" onClick={() => props.onAttach("deal", String(d.id))}>
                  📎
                </Button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small mt-2 text-[var(--ew-muted)]">Нет данных</p>
        )}
      </Block>

      <Block id="shipments" title="ЛОГИСТИКА И ПОСТАВКИ" mobile={mobile} testId="agro-cc-shipments">
        <div className="flex flex-wrap gap-2">
          {(cc.shipments?.stages || []).map((st) => (
            <button
              key={st.id}
              type="button"
              className="min-h-11 rounded-md border border-[var(--ew-border)] px-2 py-1 eds-type-small"
              onClick={() => props.onGo("logistics", { filter: st.id === "in_transit" ? "IN_TRANSIT" : st.id })}
            >
              {st.label_ru}: {st.count}
            </button>
          ))}
        </div>
        {(cc.shipments?.items || []).length ? (
          <ul className="mt-2 grid gap-2">
            {(cc.shipments?.items || []).map((s) => (
              <li key={String(s.id)} className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small">
                <button type="button" className="min-h-11 text-left underline" onClick={() => props.onOpen("shipment", String(s.id))}>
                  {String(s.number || s.title || s.id)} · {nd(s.counterparty)} · {nd(s.crop)} · {s.volume != null ? String(s.volume) : "Нет данных"}
                </button>
                <p className="text-[var(--ew-muted)]">
                  Маршрут: {nd(s.route)} · Транспорт: {nd(s.transport)} · ETA: {s.eta ? String(s.eta).slice(0, 10) : "Нет данных"}
                  {s.days_remaining != null ? ` · ${s.days_remaining} дн.` : ""}
                  {s.delay_reason ? ` · ${String(s.delay_reason)}` : ""}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small mt-2 text-[var(--ew-muted)]">Нет активных перевозок</p>
        )}
      </Block>

      <Block id="warehouses" title="СКЛАДЫ" mobile={mobile} testId="agro-cc-warehouses">
        <p className="eds-type-small">
          Приход сегодня: {cc.warehouses?.receipt_today ?? 0} т · Расход сегодня: {cc.warehouses?.issue_today ?? 0} т
        </p>
        {(cc.warehouses?.top_crops || []).length ? (
          <p className="eds-type-small mt-1">
            {(cc.warehouses?.top_crops || []).map((c) => `${c.name} ${c.quantity} т`).join(" · ")}
          </p>
        ) : (
          <p className="eds-type-small mt-1 text-[var(--ew-muted)]">Нет данных</p>
        )}
        <ul className="mt-2 grid gap-2 sm:grid-cols-2">
          {(cc.warehouses?.items || []).map((w) => (
            <li key={String(w.id)}>
              <button type="button" className="min-h-11 w-full rounded-md border border-[var(--ew-border)] p-2 text-left" onClick={() => props.onOpen("warehouse", String(w.id))}>
                <p className="font-medium">{String(w.name)}</p>
                <p className="eds-type-small text-[var(--ew-muted)]">
                  {nd(w.owner)} · {nd(w.location)} · {w.stock != null ? `${w.stock} т` : "Нет данных"} / {w.capacity != null ? `${w.capacity} т` : "Нет данных"}
                </p>
              </button>
            </li>
          ))}
        </ul>
        {!(cc.warehouses?.items || []).length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        {cc.grain_stock ? (
          <div className="mt-3 eds-type-small" data-testid="agro-cc-grain-stock">
            <p className="font-medium">Остатки (ledger)</p>
            {(cc.grain_stock.by_crop || []).length ? (
              <p>{(cc.grain_stock.by_crop || []).map((c) => `${c.crop} ${c.quantity} т`).join(" · ")}</p>
            ) : (
              <p className="text-[var(--ew-muted)]">Нет данных</p>
            )}
            {(cc.grain_stock.lots || []).slice(0, 8).map((l) => (
              <p key={String(l.id)}>
                {String(l.lot_number || l.id)} · физ. {String(l.physical ?? "Нет данных")} · доступно {String(l.available ?? "Нет данных")}
              </p>
            ))}
          </div>
        ) : null}
      </Block>

      <Block id="markets" title="ЦЕНЫ И РЫНКИ" mobile={mobile} testId="agro-cc-markets">
        {(cc.markets || []).length ? (
          <ul className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {(cc.markets || []).map((m) => (
              <li key={String(m.crop)} className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small">
                <p className="font-medium">{String(m.crop)}</p>
                <p>
                  {m.price != null ? `${m.price} ${m.currency || ""} / ${m.unit || "т"}` : "Нет данных"} · {String(m.source_label_ru || "Ручная")}
                </p>
                <p className="text-[var(--ew-muted)]">
                  {nd(m.market)} · {m.change != null ? String(m.change) : "Нет данных"} · {m.updated_at ? String(m.updated_at).slice(0, 10) : "Нет данных"}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p>
        )}
        <div className="mt-2 flex flex-wrap gap-2">
          <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onQuickKind("price")}>
            Добавить цену
          </Button>
          <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("settings", { tab: "sources" })}>
            Добавить источник
          </Button>
          <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("notifications")}>
            Создать ценовой сигнал
          </Button>
        </div>
      </Block>

      <Block id="weather" title="ПОГОДА И АГРО-РИСКИ" mobile={mobile} testId="agro-cc-weather">
        <div className={mobile ? "grid gap-2" : "grid gap-2 sm:grid-cols-5"}>
          {(cc.weather?.regions || []).map((r) => (
            <div key={String(r.macro_id)} className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small">
              <p className="font-medium">{String(r.title_ru)}</p>
              {r.missing ? (
                <p>Нет данных</p>
              ) : (
                <>
                  <p>{r.tmax != null ? `+${Math.round(Number(r.tmax))}°C` : "Нет данных"}</p>
                  <p>Осадки: {String(r.precip_label_ru || "Нет данных")}</p>
                  <p>Риск: {nd(r.risk_ru)}</p>
                  <p>Рекомендация: {nd(r.recommendation_ru)}</p>
                </>
              )}
            </div>
          ))}
        </div>
        {!(cc.weather?.regions || []).length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        <Button className="mt-2 min-h-11" size="sm" onClick={() => props.onGo("weather")}>
          Открыть карту
        </Button>
      </Block>

      <Block id="intel" title="АГРО-РАЗВЕДКА" mobile={mobile} testId="agro-cc-intel">
        <div className="grid gap-2 sm:grid-cols-2">
          {(cc.intel || []).map((card) => (
            <div key={String(card.id)} className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small">
              <p className="font-medium">{String(card.label_ru)}</p>
              <p>{card.missing ? "Нет данных" : String(card.summary_ru || "Нет данных")}</p>
              <p className="text-[var(--ew-muted)]">
                Уверенность: {card.confidence != null ? String(card.confidence) : "Нет данных"} · Источников: {Number(card.sources_count || 0)} ·{" "}
                {card.updated_at ? String(card.updated_at).slice(0, 16).replace("T", " ") : "Нет данных"}
              </p>
            </div>
          ))}
        </div>
        {!(cc.intel || []).length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
        <div className="mt-2 flex gap-2">
          <Button size="sm" className="min-h-11" onClick={() => props.onGo("intel")}>
            Подробнее
          </Button>
          <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("intel")}>
            Источники
          </Button>
        </div>
      </Block>

      <Block id="tasks" title="ЗАДАЧИ И КАЛЕНДАРЬ" mobile={mobile} defaultOpen={!mobile} testId="agro-cc-tasks">
        <TaskGroup title="Сегодня" rows={cc.tasks?.today} onTask={props.onTask} mobile={mobile} />
        <TaskGroup title="Просрочено" rows={cc.tasks?.overdue} onTask={props.onTask} mobile={mobile} />
        <TaskGroup title="На этой неделе" rows={cc.tasks?.week} onTask={props.onTask} mobile={mobile} />
        <p className="eds-type-caption mt-2">Ближайшие встречи</p>
        {(cc.tasks?.meetings || []).length ? (
          <ul className="eds-type-small">
            {(cc.tasks?.meetings || []).map((m) => (
              <li key={String(m.id)}>
                {String(m.title)} · {m.starts_at ? String(m.starts_at).slice(0, 16).replace("T", " ") : "Нет данных"}
              </li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p>
        )}
        <Button className="mt-2 min-h-11" size="sm" onClick={() => props.onQuickKind("task")}>
          + Задача
        </Button>
      </Block>

      <Block id="cash" title="ДЕНЕЖНЫЕ СРЕДСТВА" mobile={mobile} testId="agro-cc-cash">
        {cc.cash?.forbidden ? (
          <p className="eds-type-small text-[var(--ew-muted)]">Нет доступа</p>
        ) : cc.cash?.empty || !(cc.cash?.by_currency || []).length ? (
          <p className="eds-type-small text-[var(--ew-muted)]">{cc.cash?.empty_ru || "Остаток денежных средств не задан"}</p>
        ) : cc.cash?.mixed ? (
          <ul>
            {(cc.cash.by_currency || []).map((row) => (
              <li key={row.currency} className="eds-type-small">
                {row.currency}: {Number(row.amount).toLocaleString("ru-RU")}
              </li>
            ))}
            <li className="eds-type-caption text-[var(--ew-muted)]">Валюты не суммируются — курс не подключён</li>
          </ul>
        ) : (
          <button type="button" className="min-h-11 text-left underline" onClick={() => props.onGo("accounting")}>
            {(cc.cash.by_currency || []).map((row) => `${row.currency} ${Number(row.amount).toLocaleString("ru-RU")}`).join(" · ")}
          </button>
        )}
      </Block>

      <Block id="harvest" title="УРОЖАЙ" mobile={mobile} testId="agro-cc-harvest">
        {cc.harvest?.empty || cc.director_production?.harvest_tonnes == null ? (
          <p className="eds-type-small text-[var(--ew-muted)]">{cc.harvest?.empty_ru || "Нет данных об урожае"}</p>
        ) : (
          <button type="button" className="min-h-11 text-left underline" onClick={() => props.onGo("fields")}>
            {cc.director_production?.harvest_tonnes} т
          </button>
        )}
      </Block>

      <div className="flex flex-wrap gap-2" data-testid="agro-cc-exports">
        <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("report")}>
          Управленческая сводка
        </Button>
        <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("accounting", { filter: "overdue" })}>
          Просроченные оплаты
        </Button>
      </div>
    </div>
  );
}

function TaskGroup(props: {
  title: string;
  rows?: Record<string, unknown>[];
  onTask: (id: string, action: "done" | "reschedule" | "open") => void;
  mobile: boolean;
}) {
  return (
    <div className="mt-2">
      <p className="eds-type-caption">{props.title}</p>
      {!(props.rows || []).length ? (
        <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p>
      ) : (
        <ul>
          {(props.rows || []).map((t) => (
            <li key={String(t.id)} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--ew-border)] py-2 eds-type-small">
              <button type="button" className="min-h-11 text-left underline" onClick={() => props.onTask(String(t.id), "open")}>
                {Boolean(t.is_demo) ? "[DEMO] " : ""}
                {String(t.title)} {t.due_at ? `· ${String(t.due_at).slice(0, 10)}` : ""}
              </button>
              {props.mobile ? (
                <span className="flex gap-1">
                  <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onTask(String(t.id), "done")}>
                    Выполнено
                  </Button>
                  <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onTask(String(t.id), "reschedule")}>
                    Перенести
                  </Button>
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AgroManagementReport(props: { headers: Record<string, string> }) {
  const [text, setText] = useState("");
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const res = await fetch("/api/agro-ops/v1/command-center/report", { credentials: "include", headers: props.headers });
      const body = (await res.json().catch(() => ({}))) as { ok?: boolean; text?: string; message_ru?: string };
      if (cancelled) return;
      if (!res.ok || !body.ok) {
        setErr(body.message_ru || "Нет данных");
        return;
      }
      setText(body.text || "");
    })();
    return () => {
      cancelled = true;
    };
  }, [props.headers]);
  if (err) return <p className="eds-type-small text-[var(--ew-muted)]">{err}</p>;
  if (!text) return <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p>;
  return (
    <div data-testid="agro-management-report" className="print:bg-white">
      <pre className="whitespace-pre-wrap eds-type-small">{text}</pre>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button size="sm" className="min-h-11" onClick={() => window.print()}>
          Печать
        </Button>
        <a className="min-h-11 inline-flex items-center rounded-md border border-[var(--ew-border)] px-3 eds-type-small" href="/api/agro-ops/v1/command-center/report?format=html" target="_blank" rel="noreferrer">
          Открыть для печати
        </a>
        <a className="min-h-11 inline-flex items-center rounded-md border border-[var(--ew-border)] px-3 eds-type-small" href="/api/agro-ops/v1/export/management-report">
          CSV
        </a>
      </div>
    </div>
  );
}
