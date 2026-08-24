/**
 * AGRO 1.1 — prices and markets. Manual prices always; automatic only if ingested.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

const TABS = [
  { id: "overview", label: "Обзор рынка" },
  { id: "markets", label: "Мои рынки" },
  { id: "quotes", label: "Котировки" },
  { id: "pricelists", label: "Прайс-листы" },
  { id: "history", label: "История цен" },
  { id: "compare", label: "Сравнение" },
  { id: "trade", label: "Импорт/Экспорт" },
  { id: "settings", label: "Настройки" },
] as const;

const SOURCE_RU: Record<string, string> = {
  AUTOMATIC: "АВТО (внешний источник)",
  MANUAL: "MANUAL DATA",
  COUNTERPARTY: "MANUAL DATA",
  CONTRACT: "MANUAL DATA",
  MARKET_PROVIDER: "ПРОВАЙДЕР",
};

const PRICE_KINDS: { id: string; label: string }[] = [
  { id: "local_price", label: "Местная цена" },
  { id: "buyer_bid", label: "Заявка покупателя" },
  { id: "seller_offer", label: "Предложение продавца" },
  { id: "freight", label: "Фрахт" },
  { id: "warehouse", label: "Складская цена" },
  { id: "contract", label: "Контрактная цена" },
];

export function AgroMarketsPanel(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  markets: Row[];
  prices: Row[];
  onChanged: () => void;
  onOpen: (kind: string, id: string) => void;
  onAttach: (kind: string, id: string) => void;
  onCreateCalc: (prefill: Record<string, string>) => void;
  onConnectSource?: () => void;
}) {
  const [tab, setTab] = useState<(typeof TABS)[number]["id"]>("overview");
  const [dash, setDash] = useState<{ current?: Row[]; automatic_available?: boolean }>({});
  const [hist, setHist] = useState<Row[]>([]);
  const [span, setSpan] = useState("30D");
  const [crop, setCrop] = useState("Пшеница");
  const [form, setForm] = useState<Row>({ commodity: "Пшеница", currency: "UAH", unit: "т", source_type: "MANUAL", price_kind: "local_price", manual_status: "CONFIRMED" });
  const [landed, setLanded] = useState<Row | null>(null);
  const [msg, setMsg] = useState("");

  async function reload() {
    const d = await agroOpsGet(`/markets/dashboard?crop=${encodeURIComponent(crop)}`, props.headers);
    setDash((d.json || {}) as { current?: Row[]; automatic_available?: boolean });
    const h = await agroOpsGet(`/markets/history?crop=${encodeURIComponent(crop)}&span=${span}`, props.headers);
    setHist(((h.json as { points?: Row[] })?.points || []) as Row[]);
  }

  useEffect(() => {
    void reload();
  }, [props.headers, crop, span, props.prices.length, props.markets.length]);

  async function saveMarket() {
    const res = await agroOpsPost("/entities/market", { name: form.market_name, market_type: form.market_type || "manual", country: form.country || "UA" }, props.headers);
    const j = res.json as { ok?: boolean; message_ru?: string };
    setMsg(j.ok ? "Рынок сохранён" : j.message_ru || "Ошибка");
    if (j.ok) props.onChanged();
  }

  async function savePrice() {
    const res = await agroOpsPost(
      "/entities/market_price",
      {
        market_id: form.market_id,
        commodity: form.commodity,
        price: form.price,
        currency: form.currency,
        unit: form.unit,
        vat_included: form.vat_included === "true",
        incoterms: form.incoterms,
        source: form.source || form.comment,
        source_type: "MANUAL",
        price_kind: form.price_kind || "local_price",
        data_class: "manual",
        manual_status: form.manual_status || "CONFIRMED",
        valid_from: form.valid_from,
      },
      props.headers,
    );
    const j = res.json as { ok?: boolean; message_ru?: string };
    setMsg(j.ok ? "Цена сохранена в историю" : j.message_ru || "Ошибка");
    if (j.ok) props.onChanged();
  }

  return (
    <div className="grid gap-3" data-testid="agro-markets-panel">
      <div className="flex flex-wrap gap-1">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <Input placeholder="Культура" value={crop} onChange={(e) => setCrop(e.target.value)} />
        {!dash.automatic_available ? <p className="eds-type-small text-[var(--ew-muted)]">Автоматические котировки появятся только после успешного опроса источника.</p> : null}
      </div>
      {!props.markets.length ? (
        <Card title="Рынки ещё не настроены.">
          <div className="flex flex-wrap gap-2">
            {props.canCreate ? <Button size="sm" onClick={() => setTab("markets")}>Добавить рынок</Button> : null}
            {props.canCreate ? <Button size="sm" variant="ghost" onClick={() => setTab("quotes")}>Добавить цену</Button> : null}
            {props.onConnectSource ? <Button size="sm" variant="ghost" onClick={props.onConnectSource}>Подключить источник</Button> : null}
          </div>
        </Card>
      ) : null}
      {tab === "overview" || tab === "quotes" || tab === "pricelists" ? (
        <Card title={`Котировки: ${crop}`}>
          <p className="eds-type-small mb-2 text-[var(--ew-muted)]">Ручные вводы помечены <strong>MANUAL DATA</strong> и никогда не выдаются за внешний ряд.</p>
          <table className="w-full eds-type-small" data-testid="agro-market-quotes">
            <thead>
              <tr>
                <th className="text-left">Рынок</th>
                <th>Цена</th>
                <th>Валюта</th>
                <th>Изменение</th>
                <th>Источник</th>
              </tr>
            </thead>
            <tbody>
              {(dash.current || []).map((r) => (
                <tr key={pick(r, "id")}>
                  <td>
                    <button type="button" className="underline" onClick={() => props.onOpen("market_price", pick(r, "id"))}>
                      {String(r.market_name || "—")}
                    </button>
                  </td>
                  <td>{String(r.price ?? "—")}</td>
                  <td>{String(r.currency || "")}</td>
                  <td>{r.change == null ? "—" : String(r.change)}</td>
                  <td>
                    <span data-testid="agro-manual-data-badge">{SOURCE_RU[String(r.source_type || "MANUAL")] || "MANUAL DATA"}</span>
                    {String(r.source_type || "MANUAL") !== "AUTOMATIC" && String(r.source_type || "") !== "MARKET_PROVIDER" ? " · не внешние данные" : ""}
                    {" · "}
                    <span data-testid="agro-manual-trust">{String(r.manual_status || "CONFIRMED")}</span>
                    {" · "}
                    {String(r.updated_at || "").slice(0, 16)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
      {tab === "markets" ? (
        <>
          <ul className="eds-type-small">
            {props.markets.map((m) => (
              <li key={pick(m, "id")} className="flex justify-between border-b border-[var(--ew-border)] py-1">
                <button type="button" className="underline" onClick={() => props.onOpen("market", pick(m, "id"))}>
                  {pick(m, "name")}
                </button>
                <Button size="sm" variant="ghost" onClick={() => props.onAttach("market", pick(m, "id"))}>
                  📎
                </Button>
              </li>
            ))}
          </ul>
          {props.canCreate ? (
            <Card title="Добавить рынок">
              <div className="grid gap-2 sm:grid-cols-2">
                <Input placeholder="Название" value={String(form.market_name || "")} onChange={(e) => setForm((f) => ({ ...f, market_name: e.target.value }))} />
                <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.market_type || "manual")} onChange={(e) => setForm((f) => ({ ...f, market_type: e.target.value }))}>
                  <option value="manual">Ручной рынок</option>
                  <option value="port">Порт</option>
                  <option value="elevator">Элеватор</option>
                  <option value="export">Экспортный рынок</option>
                  <option value="local">Местный рынок</option>
                </select>
              </div>
              <Button className="mt-2" size="sm" onClick={() => void saveMarket()}>
                Сохранить рынок
              </Button>
            </Card>
          ) : null}
        </>
      ) : null}
      {tab === "quotes" && props.canCreate ? (
        <Card title="Добавить цену">
          <div className="grid gap-2 sm:grid-cols-2">
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.market_id || "")} onChange={(e) => setForm((f) => ({ ...f, market_id: e.target.value }))}>
              <option value="">Рынок</option>
              {props.markets.map((m) => (
                <option key={pick(m, "id")} value={pick(m, "id")}>
                  {pick(m, "name")}
                </option>
              ))}
            </select>
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.price_kind || "local_price")} onChange={(e) => setForm((f) => ({ ...f, price_kind: e.target.value }))}>
              {PRICE_KINDS.map((k) => (
                <option key={k.id} value={k.id}>{k.label}</option>
              ))}
            </select>
            <Input placeholder="Культура" value={String(form.commodity || "")} onChange={(e) => setForm((f) => ({ ...f, commodity: e.target.value }))} />
            <Input placeholder="Цена" value={String(form.price || "")} onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))} />
            <Input placeholder="Валюта" value={String(form.currency || "UAH")} onChange={(e) => setForm((f) => ({ ...f, currency: e.target.value }))} />
            <Input placeholder="Единица" value={String(form.unit || "т")} onChange={(e) => setForm((f) => ({ ...f, unit: e.target.value }))} />
            <Input placeholder="Условия поставки" value={String(form.incoterms || "")} onChange={(e) => setForm((f) => ({ ...f, incoterms: e.target.value }))} />
            <Input type="date" value={String(form.valid_from || "")} onChange={(e) => setForm((f) => ({ ...f, valid_from: e.target.value }))} />
            <Input placeholder="Источник / комментарий" value={String(form.comment || "")} onChange={(e) => setForm((f) => ({ ...f, comment: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.manual_status || "CONFIRMED")} onChange={(e) => setForm((f) => ({ ...f, manual_status: e.target.value }))} data-testid="agro-manual-status">
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="UNCONFIRMED">UNCONFIRMED</option>
            </select>
          </div>
          <Button className="mt-2" size="sm" onClick={() => void savePrice()}>
            Сохранить цену
          </Button>
        </Card>
      ) : null}
      {tab === "history" ? (
        <Card title="История цен">
          <div className="mb-2 flex flex-wrap gap-1">
            {["7D", "30D", "3M", "6M", "1Y"].map((s) => (
              <Button key={s} size="sm" variant={span === s ? "secondary" : "ghost"} onClick={() => setSpan(s)}>
                {s}
              </Button>
            ))}
          </div>
          <ul className="eds-type-small" data-testid="agro-price-history">
            {hist.length ? hist.map((p, i) => (
              <li key={`${p.date}-${i}`}>
                {String(p.date)} · {String(p.price)} {String(p.currency || "")} · {SOURCE_RU[String(p.source_type || "MANUAL")]}
              </li>
            )) : <li>История появится после сохранённых цен. Синтетический график не строится.</li>}
          </ul>
        </Card>
      ) : null}
      {tab === "trade" ? (
        <Card title="Импорт / экспорт">
          <p className="eds-type-small">
            Ряды таможни и FAO появятся только после успешного опроса источника. Объёмы и цены не выдумываются.
          </p>
          {props.onConnectSource ? (
            <Button className="mt-2" size="sm" onClick={props.onConnectSource}>
              Открыть источники
            </Button>
          ) : null}
        </Card>
      ) : null}
      {tab === "settings" ? (
        <Card title="Настройки рынков">
          <p className="eds-type-small mb-2">Ручные цены всегда доступны. Автокотировки — только CONNECTED после реальной загрузки.</p>
          {props.onConnectSource ? <Button size="sm" onClick={props.onConnectSource}>Подключить источник</Button> : null}
        </Card>
      ) : null}
      {tab === "compare" ? (
        <Card title="Доставленная себестоимость">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Закупка" value={String(form.purchase_price || "")} onChange={(e) => setForm((f) => ({ ...f, purchase_price: e.target.value }))} />
            <Input placeholder="Продажа" value={String(form.sale_price || "")} onChange={(e) => setForm((f) => ({ ...f, sale_price: e.target.value }))} />
            <Input placeholder="Транспорт" value={String(form.transport || "")} onChange={(e) => setForm((f) => ({ ...f, transport: e.target.value }))} />
            <Input placeholder="Хранение" value={String(form.storage || "")} onChange={(e) => setForm((f) => ({ ...f, storage: e.target.value }))} />
            <Input placeholder="Количество, т" value={String(form.quantity || "100")} onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))} />
          </div>
          <div className="mt-2 flex gap-2">
            <Button
              size="sm"
              disabled={!props.canFinance}
              onClick={async () => {
                const r = await agroOpsPost("/markets/landed-cost", { ...form, quantity: form.quantity || 100 }, props.headers);
                setLanded((r.json as { item?: Row }).item || null);
              }}
            >
              Посчитать
            </Button>
            <Button size="sm" variant="ghost" disabled={!props.canFinance} onClick={() => props.onCreateCalc({ purchase_price: String(form.purchase_price || ""), sale_price: String(form.sale_price || ""), transport: String(form.transport || ""), storage: String(form.storage || ""), quantity: String(form.quantity || "100") })}>
              Создать расчёт
            </Button>
          </div>
          {landed ? (
            <dl className="mt-2 eds-type-small" data-testid="agro-landed-cost">
              <div>Доставленная себестоимость: {String(landed.delivered_cost ?? "—")}</div>
              <div>Маржа / т: {String(landed.margin_per_tonne ?? "—")}</div>
              <div>Маржа всего: {String(landed.total_margin ?? "—")}</div>
              <div>Маржа %: {String(landed.margin_pct ?? "—")}</div>
            </dl>
          ) : null}
        </Card>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
