/**
 * AUTO 1.5 — finance desk: summary, cash flow, receivables, ledger accounts.
 */

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Button, Card, Input } from "@/ui";
import { asList, autoOpsDownload, autoOpsGet, autoOpsPost, pick } from "../business-ops/opsApi";
import { money } from "./autoLabels";

type Rec = Record<string, unknown>;

const PERIODS = [
  { id: "today", label: "Сегодня" },
  { id: "7d", label: "7 дней" },
  { id: "30d", label: "30 дней" },
  { id: "quarter", label: "Квартал" },
  { id: "year", label: "Год" },
  { id: "all", label: "Всё время" },
  { id: "custom", label: "Свои даты" },
];

const TABS = [
  { id: "summary", label: "Сводка" },
  { id: "cashflow", label: "Cash Flow" },
  { id: "receivables", label: "Дебиторка" },
  { id: "accounts", label: "Счета" },
];

export function AutoFinanceDesk({
  headers,
  canFinance,
  canWrite,
  onOpenVehicle,
}: {
  headers: Record<string, string>;
  canFinance: boolean;
  canWrite: boolean;
  onOpenVehicle: (id: string) => void;
}) {
  const [tab, setTab] = useState("summary");
  const [period, setPeriod] = useState("30d");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [data, setData] = useState<Rec>({});
  const [accounts, setAccounts] = useState<Rec[]>([]);
  const [balance, setBalance] = useState("");
  const [accountType, setAccountType] = useState("BANK_USD");

  const load = useCallback(async () => {
    if (!canFinance) return;
    const q = new URLSearchParams({ period, date_from: dateFrom, date_to: dateTo });
    if (tab === "summary") {
      const res = await autoOpsGet(`/analytics/finance?${q.toString()}`, headers);
      setData((res.json || {}) as Rec);
    } else if (tab === "cashflow") {
      const res = await autoOpsGet(`/analytics/cashflow?${q.toString()}`, headers);
      setData((res.json || {}) as Rec);
    } else if (tab === "receivables") {
      const res = await autoOpsGet("/analytics/receivables", headers);
      setData((res.json || {}) as Rec);
    } else {
      const res = await autoOpsGet("/finance/accounts", headers);
      setAccounts(asList(res.json) as Rec[]);
      setData((res.json || {}) as Rec);
    }
  }, [canFinance, headers, tab, period, dateFrom, dateTo]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!canFinance) {
    return <p className="eds-type-helper">Финансы доступны директору и бухгалтеру.</p>;
  }

  const cards = (data.cards || {}) as Rec;
  const labels = (data.labels_ru || {}) as Rec;
  const summary = (data.summary || {}) as Rec;
  const gap = data.gap as Rec | undefined;

  async function saveAccount(e: FormEvent) {
    e.preventDefault();
    await autoOpsPost("/finance/accounts", { account_type: accountType, balance: Number(balance), source: "WEB" }, headers);
    setBalance("");
    await load();
  }

  return (
    <div className="space-y-4" data-testid="auto-finance">
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "primary" : "secondary"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {tab === "summary" || tab === "cashflow" ? (
        <div className="flex flex-wrap gap-2" data-testid="auto-finance-periods">
          {PERIODS.map((p) => (
            <Button key={p.id} size="sm" variant={period === p.id ? "primary" : "ghost"} onClick={() => setPeriod(p.id)}>
              {p.label}
            </Button>
          ))}
          {period === "custom" ? (
            <>
              <Input value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} placeholder="с" aria-label="Дата с" />
              <Input value={dateTo} onChange={(e) => setDateTo(e.target.value)} placeholder="по" aria-label="Дата по" />
            </>
          ) : null}
        </div>
      ) : null}

      {tab === "summary" ? (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4" data-testid="auto-finance-summary">
          {Object.entries(labels).map(([k, label]) => (
            <Card key={k} className="p-3">
              <p className="eds-type-caption text-[var(--eds-text-muted)]">{String(label)}</p>
              <p className="mt-1 text-2xl">{money(cards[k])}</p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "cashflow" ? (
        <div data-testid="auto-cashflow">
          {data.opening_known ? (
            <p className="eds-type-helper">Стартовый остаток: {money(data.opening_balance)}</p>
          ) : (
            <p className="eds-type-helper">{String(data.note_ru || "Стартовый остаток не задан.")}</p>
          )}
          {gap ? (
            <Card title="⚠ Возможный кассовый разрыв">
              <div data-testid="auto-cash-gap">
              <p>{pick(gap, "message_ru")}</p>
              <p>Ожидаемые поступления: {money(gap.incoming)}</p>
              <p>Ожидаемые расходы: {money(gap.outgoing)}</p>
              <p>Разрыв: {money(gap.gap)}</p>
              </div>
            </Card>
          ) : null}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="text-[var(--eds-text-muted)]">
                  {["Date", "Incoming", "Outgoing", "Net", "Running balance"].map((h) => (
                    <th key={h} className="py-2 pr-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(asList(data) as Rec[]).map((r) => (
                  <tr key={String(r.date)} className="border-t border-[var(--eds-border)]">
                    <td className="py-2 pr-3">{pick(r, "date")}</td>
                    <td className="py-2 pr-3">{money(r.incoming)}</td>
                    <td className="py-2 pr-3">{money(r.outgoing)}</td>
                    <td className="py-2 pr-3">{money(r.net)}</td>
                    <td className="py-2 pr-3">{r.running_balance == null ? "—" : money(r.running_balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === "receivables" ? (
        <div data-testid="auto-receivables">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card className="p-3"><p className="eds-type-caption">Всего должны</p><p className="text-xl">{money(summary.total_owed)}</p></Card>
            <button className="text-left" onClick={() => undefined}>
              <Card className="p-3">
                <div data-testid="auto-overdue-total">
                  <p className="eds-type-caption">Просрочено</p>
                  <p className="text-xl">{money(summary.overdue)}</p>
                </div>
              </Card>
            </button>
            <Card className="p-3"><p className="eds-type-caption">Ожидается 7 дней</p><p className="text-xl">{money(summary.due_7d)}</p></Card>
            <Card className="p-3"><p className="eds-type-caption">Ожидается 30 дней</p><p className="text-xl">{money(summary.due_30d)}</p></Card>
          </div>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead>
                <tr className="text-[var(--eds-text-muted)]">
                  {["Клиент", "Автомобиль", "VIN", "Цена сделки", "Получено", "Остаток", "Срок оплаты", "Просрочка", "Менеджер"].map((h) => (
                    <th key={h} className="py-2 pr-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(asList(data) as Rec[]).map((r) => (
                  <tr key={String(r.deal_id)} className="border-t border-[var(--eds-border)]">
                    <td className="py-2 pr-3">{pick(r, "client")}</td>
                    <td className="py-2 pr-3">
                      <button className="underline" onClick={() => r.vehicle_id && onOpenVehicle(String(r.vehicle_id))}>{pick(r, "vehicle")}</button>
                    </td>
                    <td className="py-2 pr-3">{pick(r, "vin")}</td>
                    <td className="py-2 pr-3">{money(r.sale_price)}</td>
                    <td className="py-2 pr-3">{money(r.paid)}</td>
                    <td className="py-2 pr-3">{money(r.outstanding)}</td>
                    <td className="py-2 pr-3">{pick(r, "due_at")}</td>
                    <td className="py-2 pr-3">{r.overdue_days ? String(r.overdue_days) : "—"}</td>
                    <td className="py-2 pr-3">{pick(r, "manager")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {tab === "accounts" ? (
        <div data-testid="auto-accounts">
          <p className="eds-type-helper">{String(data.note_ru || "Только учёт остатков. Crypto custody не строится.")}</p>
          {accounts.map((a) => (
            <p key={String(a.id)}>{pick(a, "label")} · {pick(a, "currency")} · {a.balance == null ? "остаток не задан" : money(a.balance, String(a.currency || "USD"))}</p>
          ))}
          {canWrite ? (
            <form className="mt-3 flex flex-wrap gap-2" onSubmit={(e) => void saveAccount(e)}>
              <select className="eds-input h-10" value={accountType} onChange={(e) => setAccountType(e.target.value)} aria-label="Тип счёта">
                <option value="BANK_UAH">Банк UAH</option>
                <option value="BANK_USD">Банк USD</option>
                <option value="CASH_UAH">Касса UAH</option>
                <option value="CASH_USD">Касса USD</option>
                <option value="GEORGIA">Georgia account</option>
                <option value="USDT_LEDGER">USDT wallet (учёт)</option>
                <option value="OTHER">Другое</option>
              </select>
              <Input value={balance} onChange={(e) => setBalance(e.target.value)} placeholder="Остаток" aria-label="Остаток" />
              <Button type="submit" size="sm">Сохранить остаток</Button>
            </form>
          ) : null}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {["economics", "receivables", "receipts", "expenses", "cashflow"].map((kind) => (
          <Button key={kind} size="sm" variant="secondary" onClick={() => void autoOpsDownload(`/analytics/export?kind=${kind}&format=csv`, headers)}>
            CSV {kind}
          </Button>
        ))}
      </div>
    </div>
  );
}
