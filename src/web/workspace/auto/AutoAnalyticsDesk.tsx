/**
 * AUTO 1.5 — director analytics desk.
 * Business language only. Drill-down to vehicles. No technical chrome.
 */

import { useCallback, useEffect, useState } from "react";
import { Button, Card } from "@/ui";
import { asList, autoOpsGet, autoOpsPost, pick } from "../business-ops/opsApi";
import { money } from "./autoLabels";

type Rec = Record<string, unknown>;

const TABS = [
  { id: "economics", label: "Экономика авто" },
  { id: "ranking", label: "Рейтинг прибыльности" },
  { id: "sales", label: "Продажи" },
  { id: "managers", label: "Менеджеры" },
  { id: "logistics", label: "Логистика" },
  { id: "customs", label: "Таможня" },
  { id: "repair", label: "Ремонт" },
  { id: "documents", label: "Документы" },
  { id: "sale_ready", label: "Готовность к продаже" },
  { id: "registration_ready", label: "Готовность к регистрации" },
  { id: "funnel", label: "Воронка" },
  { id: "risks", label: "Риски" },
];

const FILTERS = [
  { id: "all", label: "Все" },
  { id: "profitable", label: "Прибыльные" },
  { id: "low_margin", label: "Низкая маржа" },
  { id: "loss", label: "Убыток" },
  { id: "unsold", label: "Не проданы" },
  { id: "sold", label: "Проданы" },
  { id: "age_30", label: "30+" },
  { id: "age_60", label: "60+" },
  { id: "age_90", label: "90+" },
  { id: "age_120", label: "120+" },
];

function num(v: unknown): string {
  if (v == null || v === "") return "—";
  return money(v);
}

export function AutoAnalyticsDesk({
  headers,
  canFinance,
  onOpenVehicle,
  onOpenVehicles,
}: {
  headers: Record<string, string>;
  canFinance: boolean;
  onOpenVehicle: (id: string) => void;
  onOpenVehicles?: (ids: string[]) => void;
}) {
  const [tab, setTab] = useState("economics");
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("days_in_cycle");
  const [data, setData] = useState<Rec>({});
  const [ai, setAi] = useState<Rec | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    const q = new URLSearchParams({ filter, sort, dir: "desc" });
    const path =
      tab === "economics"
        ? `/analytics/economics?${q.toString()}`
        : tab === "sale_ready" || tab === "registration_ready"
          ? `/analytics/documents`
          : `/analytics/${tab}`;
    const res = await autoOpsGet(path, headers);
    setData((res.json || {}) as Rec);
  }, [headers, tab, filter, sort]);

  useEffect(() => {
    void load();
  }, [load]);

  const items = asList(data) as Rec[];
  const ranking = data as Rec;

  function drill(ids: unknown) {
    const list = Array.isArray(ids) ? ids.map(String).filter(Boolean) : [];
    if (list.length === 1) onOpenVehicle(list[0]);
    else if (list.length > 1 && onOpenVehicles) onOpenVehicles(list);
    else if (list[0]) onOpenVehicle(list[0]);
  }

  return (
    <div className="space-y-4" data-testid="auto-analytics">
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "primary" : "secondary"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {tab === "economics" ? (
        <div className="flex flex-wrap gap-2" data-testid="auto-economics-filters">
          {FILTERS.map((f) => (
            <Button key={f.id} size="sm" variant={filter === f.id ? "primary" : "ghost"} onClick={() => setFilter(f.id)}>
              {f.label}
            </Button>
          ))}
          <select className="eds-input h-8" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Сортировка">
            <option value="days_in_cycle">Дней в цикле</option>
            <option value="profit">Прибыль</option>
            <option value="margin_pct">Маржа</option>
            <option value="cost">Себестоимость</option>
            <option value="title">Автомобиль</option>
          </select>
        </div>
      ) : null}

      {tab === "economics" ? (
        <div className="overflow-x-auto" data-testid="auto-economics-table">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead>
              <tr className="text-[var(--eds-text-muted)]">
                {["Автомобиль", "VIN", "Дата покупки", "Статус", "Дней в цикле", "Покупка", "Логистика", "Таможня", "Ремонт", "Себестоимость", "Цена продажи", "Прибыль", "Маржа", "Менеджер"].map((h) => (
                  <th key={h} className="py-2 pr-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={String(r.vehicle_id)} className="border-t border-[var(--eds-border)]">
                  <td className="py-2 pr-3">
                    <button className="underline" onClick={() => onOpenVehicle(String(r.vehicle_id))}>{pick(r, "title")}</button>
                    {r.quality && r.quality !== "KNOWN" ? (
                      <p className="eds-type-caption text-[var(--eds-text-muted)]">{String(r.completeness_note_ru || r.profit_kind_ru)}</p>
                    ) : null}
                  </td>
                  <td className="py-2 pr-3">{pick(r, "vin")}</td>
                  <td className="py-2 pr-3">{pick(r, "purchase_date")}</td>
                  <td className="py-2 pr-3">{pick(r, "status_ru")}</td>
                  <td className="py-2 pr-3">{r.days_in_cycle == null ? "—" : String(r.days_in_cycle)}</td>
                  <td className="py-2 pr-3">{r.finance_restricted ? "скрыто" : num(r.purchase)}</td>
                  <td className="py-2 pr-3">{r.finance_restricted ? "скрыто" : num(r.logistics)}</td>
                  <td className="py-2 pr-3">{r.finance_restricted ? "скрыто" : num(r.customs)}</td>
                  <td className="py-2 pr-3">{r.finance_restricted ? "скрыто" : num(r.repair)}</td>
                  <td className="py-2 pr-3">{r.finance_restricted ? "скрыто" : num(r.cost)}</td>
                  <td className="py-2 pr-3">{r.finance_restricted ? "скрыто" : num(r.sale_price)}</td>
                  <td className="py-2 pr-3">
                    {r.finance_restricted ? "скрыто" : r.sold ? num(r.profit) : ((r.forecast as Rec | undefined)?.forecast_profit != null ? `ПРОГНОЗ ${num((r.forecast as Rec).forecast_profit)}` : "—")}
                  </td>
                  <td className="py-2 pr-3">
                    {r.finance_restricted ? "скрыто" : r.sold ? (r.margin_pct == null ? "—" : `${r.margin_pct}%`) : ((r.forecast as Rec | undefined)?.forecast_margin != null ? `ПРОГНОЗ ${(r.forecast as Rec).forecast_margin}%` : "—")}
                  </td>
                  <td className="py-2 pr-3">{pick(r, "manager")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length ? <p className="eds-type-helper mt-3">Нет автомобилей по фильтру.</p> : null}
        </div>
      ) : null}

      {tab === "ranking" && canFinance ? (
        <div className="grid gap-4 md:grid-cols-2" data-testid="auto-ranking">
          <Card title="Самые прибыльные автомобили">
            {(asList(ranking.strongest) as Rec[]).map((r) => (
              <button key={String(r.vehicle_id)} className="block py-1 underline" onClick={() => onOpenVehicle(String(r.vehicle_id))}>
                {String(pick(r, "title"))} · {num(r.profit)} · {String(r.margin_pct)}% · {String(r.days_in_cycle)} дн.
              </button>
            ))}
          </Card>
          <Card title="Самые слабые автомобили">
            {(asList(ranking.weakest) as Rec[]).map((r) => (
              <button key={String(r.vehicle_id)} className="block py-1 underline" onClick={() => onOpenVehicle(String(r.vehicle_id))}>
                {String(pick(r, "title"))} · {num(r.profit)} · {String(r.margin_pct)}%
              </button>
            ))}
          </Card>
          <Card title="ПРОГНОЗ — непроданные">
            <p className="eds-type-caption mb-2 text-[var(--eds-text-muted)]">Не ранжируются как фактическая прибыль.</p>
            {(asList(ranking.unsold_forecast) as Rec[]).map((r) => (
              <button key={String(r.vehicle_id)} className="block py-1 underline" onClick={() => onOpenVehicle(String(r.vehicle_id))}>
                {pick(r, "title")} · ПРОГНОЗ {num(r.profit)}
              </button>
            ))}
          </Card>
        </div>
      ) : null}

      {tab === "sales" && canFinance ? (
        <div data-testid="auto-sales-analytics">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {Object.entries((data.metrics || {}) as Rec).map(([k, v]) => (
              <Card key={k} className="p-3">
                <p className="eds-type-caption text-[var(--eds-text-muted)]">{k.replaceAll("_", " ")}</p>
                <p className="mt-1 text-xl">{String(v ?? "—")}</p>
              </Card>
            ))}
          </div>
          <div className="mt-4 space-y-1" data-testid="auto-sales-chart">
            {(asList(data.chart) as Rec[]).map((row) => (
              <p key={String(row.month)} className="eds-type-body">
                {pick(row, "month")}: продажи {String(row.sales)} · выручка {num(row.revenue)} · прибыль {num(row.profit)}
              </p>
            ))}
          </div>
        </div>
      ) : null}

      {tab === "managers" ? (
        <div data-testid="auto-managers-analytics">
          <p className="eds-type-helper">{String(data.note_ru || "Сбалансированные счётчики. Рейтинга по выручке нет.")}</p>
          {(asList(data) as Rec[]).map((m) => (
            <Card key={String(m.manager_id || m.id)} className="p-3">
              <p className="font-medium">{pick(m, "manager_id", "label")}</p>
              <p className="eds-type-caption">Клиенты {String(m.active_clients ?? "—")} · Сделки {String(m.deals ?? m.deal_count ?? "—")} · Авто {String(m.vehicles_assigned ?? "—")} · Резервы {String(m.reservations ?? "—")} · Продажи {String(m.sales ?? "—")} · Просроченные задачи {String(m.overdue_tasks ?? "—")}</p>
              {canFinance && !data.company_profit_hidden ? (
                <p className="eds-type-caption">Выручка {num(m.revenue)} · Прибыль {num(m.profit)} · Маржа {m.avg_margin == null ? "—" : `${m.avg_margin}%`} · Дней до продажи {String(m.avg_days_to_sale ?? "—")}</p>
              ) : (
                <p className="eds-type-caption">Компания-wide прибыль скрыта</p>
              )}
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "logistics" ? (
        <div data-testid="auto-logistics-analytics">
          {data.note_ru ? <p className="eds-type-helper">{String(data.note_ru)}</p> : null}
          <p>Среднее в пути: {String((data.metrics as Rec | undefined)?.avg_transit_days ?? "—")} дн.</p>
          <p>Средняя задержка: {String((data.metrics as Rec | undefined)?.avg_delay_days ?? "—")} дн.</p>
          <p>Средние дни в порту: {String((data.metrics as Rec | undefined)?.avg_port_days ?? "—")} дн.</p>
          <p>Средние дни таможни: {String((data.metrics as Rec | undefined)?.avg_customs_days ?? "—")} дн.</p>
          {canFinance && (data.metrics as Rec | undefined)?.avg_logistics_cost != null ? (
            <p>Средняя стоимость логистики: {money((data.metrics as Rec).avg_logistics_cost)}</p>
          ) : null}
          <p>Задержки: {String((data.metrics as Rec | undefined)?.delayed_shipments ?? 0)}</p>
          {Number((data.metrics as Rec | undefined)?.delayed_shipments || 0) > 0 ? (
            <button className="underline" onClick={() => drill((asList(data.delayed) as Rec[]).map((s) => s.vehicle_id))}>
              {String((data.metrics as Rec).delayed_shipments)} задержки
            </button>
          ) : null}
        </div>
      ) : null}

      {tab === "customs" ? (
        <div data-testid="auto-customs-analytics">
          {data.note_ru ? <p className="eds-type-helper">{String(data.note_ru)}</p> : null}
          <p>Средняя длительность: {String((data.metrics as Rec | undefined)?.avg_customs_duration ?? (data.metrics as Rec | undefined)?.avg_customs_days ?? "—")} дн.</p>
          {canFinance ? (
            <>
              <p>Среднее мито: {num((data.metrics as Rec | undefined)?.avg_duty)}</p>
              <p>Средний акциз: {num((data.metrics as Rec | undefined)?.avg_excise)}</p>
              <p>Средний НДС: {num((data.metrics as Rec | undefined)?.avg_vat)}</p>
              <p>Средний таможенный итог: {num((data.metrics as Rec | undefined)?.avg_customs_total)}</p>
              <p>Средняя сертификация: {num((data.metrics as Rec | undefined)?.avg_certification_cost)}</p>
              <p>Средняя регистрация: {num((data.metrics as Rec | undefined)?.avg_registration_cost)}</p>
              <p>Средний landed cost: {num((data.metrics as Rec | undefined)?.avg_landed_cost)}</p>
            </>
          ) : null}
          <p>Задержанные: {String((data.metrics as Rec | undefined)?.vehicles_delayed ?? (data.metrics as Rec | undefined)?.delayed ?? 0)}</p>
          <p>Заблокированные: {String((data.metrics as Rec | undefined)?.blocked_vehicles ?? (data.metrics as Rec | undefined)?.blocked ?? 0)}</p>
        </div>
      ) : null}

      {tab === "repair" ? (
        <div>
          {(asList(data) as Rec[]).slice(0, 20).map((r) => (
            <button key={String(r.vehicle_id || r.id)} className="block py-1 underline" onClick={() => r.vehicle_id && onOpenVehicle(String(r.vehicle_id))}>
              {pick(r, "title", "vin")} {r.budget_exceeded ? "· бюджет превышен" : ""} {r.variance != null ? `· отклонение ${num(r.variance)}` : ""}
            </button>
          ))}
        </div>
      ) : null}

      {tab === "documents" || tab === "sale_ready" || tab === "registration_ready" ? (
        <div data-testid="auto-docs-attention">
        <Card title={tab === "sale_ready" ? `Готовность к продаже: ${String(data.sale_ready_count ?? 0)}` : tab === "registration_ready" ? `Готовность к регистрации: ${String(data.registration_ready_count ?? 0)}` : `Документы требуют внимания: ${String(data.attention_count ?? 0)}`}>
          {(asList(data) as Rec[]).map((r) => (
            <button key={String(r.vehicle_id)} className="block py-1 underline" onClick={() => onOpenVehicle(String(r.vehicle_id))}>
              {pick(r, "title")} · {String(r.percent)}% {tab === "sale_ready" && r.sale_ready ? "· готово" : ""} {tab === "registration_ready" && r.registration_ready ? "· готово" : ""}
            </button>
          ))}
        </Card>
        </div>
      ) : null}

      {tab === "funnel" ? (
        <div className="space-y-2" data-testid="auto-funnel">
          {(asList(data) as Rec[]).map((s) => (
            <button key={String(s.id)} className="block w-full text-left" onClick={() => drill(s.vehicle_ids)}>
              <Card className="p-3">
                <p className="font-medium">{pick(s, "label_ru")}</p>
                <p className="eds-type-caption">Авто: {String(s.count)} · Капитал: {num(s.capital)} · Средние дни: {String(s.avg_days ?? "—")}</p>
              </Card>
            </button>
          ))}
        </div>
      ) : null}

      {tab === "risks" ? (
        <div data-testid="auto-risks">
          {(asList(data) as Rec[]).map((r, i) => (
            <button key={`${r.id}-${i}`} className="block py-1 underline" onClick={() => r.vehicle_id && onOpenVehicle(String(r.vehicle_id))}>
              {pick(r, "message_ru")}
            </button>
          ))}
          {!items.length ? <p className="eds-type-helper">Открытых рисков по записям нет.</p> : null}
        </div>
      ) : null}

      {canFinance ? (
        <div>
          <Button
            size="sm"
            variant="secondary"
            onClick={async () => {
              const res = await autoOpsPost("/analytics/ai", {}, headers);
              setAi((res.json || {}) as Rec);
              setMsg("Расчёт выполнен на бэкенде. LLM только поясняет поданные цифры.");
            }}
          >
            Проанализировать бизнес
          </Button>
          {msg ? <p className="eds-type-helper mt-2">{msg}</p> : null}
          {ai ? (
            <Card title="Рекомендации (расчёт бэкенда)" className="mt-3">
              {(asList(ai.recommendations) as Rec[]).map((r) => (
                <p key={String(r.vehicle_id)}>{pick(r, "message_ru")}</p>
              ))}
              {ai.explanation_ru ? <p className="eds-type-helper mt-2">{String(ai.explanation_ru)}</p> : null}
            </Card>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
