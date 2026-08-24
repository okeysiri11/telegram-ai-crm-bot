/**
 * AGRO 2.1 Counterparty 360 — same data for desktop tabs and compact mobile sections.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { agroOpsGet, agroOpsPost } from "../business-ops/opsApi";
import { CP_STATUSES, ru, typesRu } from "./agroLabels";

type Row = Record<string, unknown>;

const DESKTOP_TABS = [
  { id: "overview", label: "ОБЗОР" },
  { id: "contacts", label: "КОНТАКТЫ" },
  { id: "deals", label: "СДЕЛКИ" },
  { id: "contracts", label: "ДОГОВОРЫ" },
  { id: "documents", label: "ДОКУМЕНТЫ" },
  { id: "payments", label: "РАСЧЁТЫ" },
  { id: "shipments", label: "ПОСТАВКИ" },
  { id: "tasks", label: "ЗАДАЧИ" },
  { id: "communications", label: "КОММУНИКАЦИИ" },
  { id: "notes", label: "ЗАМЕТКИ" },
  { id: "activity", label: "ИСТОРИЯ" },
] as const;

const MOBILE_SECTIONS = [
  { id: "overview", label: "Обзор" },
  { id: "deals", label: "Сделки" },
  { id: "payments", label: "Деньги" },
  { id: "documents", label: "Документы" },
  { id: "more", label: "Ещё" },
] as const;

function money(buckets: unknown): string {
  if (!buckets || typeof buckets !== "object") return "Нет данных";
  const entries = Object.entries(buckets as Record<string, number>).filter(([, v]) => v != null && Number(v) !== 0);
  if (!entries.length) return "Нет данных";
  return entries.map(([ccy, v]) => `${ccy} ${Number(v).toLocaleString("ru-RU")}`).join(" · ");
}

function titleOf(r: Row): string {
  return String(r.title || r.name || r.full_name || r.summary || r.id || "—");
}

export function AgroCounterparty360(props: {
  itemId: string;
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  canOperate: boolean;
  onBack: () => void;
  onOpenDeal: (id: string) => void;
  onQuick: (kind: string) => void;
  onChanged: () => void;
}) {
  const mobile = useIsMobile();
  const [tab, setTab] = useState("overview");
  const [data, setData] = useState<Row | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [contact, setContact] = useState({ full_name: "", position: "", phone: "", email: "", telegram: "", whatsapp: "" });
  const [menu, setMenu] = useState(false);

  async function reload() {
    const res = await agroOpsGet(`/crm/counterparty/${props.itemId}?tab=${tab === "more" ? "contacts" : tab}&limit=20`, props.headers);
    if (!res.ok) {
      setError("Не удалось загрузить карточку");
      return;
    }
    setData(res.json as Row);
    setError(null);
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.itemId, tab, props.headers]);

  const item = (data?.item || {}) as Row;
  const tabs = mobile ? MOBILE_SECTIONS : DESKTOP_TABS;
  const listTab = tab === "more" ? "contacts" : tab;
  const rows = ((tab === "overview" ? [] : data?.items) as Row[] | undefined) || [];

  async function addContact() {
    const res = await agroOpsPost("/entities/contact", { ...contact, counterparty_id: props.itemId }, props.headers);
    if (res.ok) {
      setContact({ full_name: "", position: "", phone: "", email: "", telegram: "", whatsapp: "" });
      props.onChanged();
      await reload();
    }
  }

  async function addNote() {
    await agroOpsPost("/crm/note", { text: note, title: note.slice(0, 80), counterparty_id: props.itemId }, props.headers);
    setNote("");
    await reload();
  }

  async function addCall() {
    await agroOpsPost("/crm/communication", { comm_type: "call", title: "Звонок", text: "Ручная запись звонка", counterparty_id: props.itemId, source: "USER" }, props.headers);
    await reload();
  }

  async function followUp() {
    await agroOpsPost("/crm/follow-up", { title: "Позвонить завтра", counterparty_id: props.itemId, due_at: new Date(Date.now() + 86400000).toISOString().slice(0, 10) }, props.headers);
    await reload();
  }

  return (
    <div className="space-y-3" data-testid="agro-cp-360">
      <header className="sticky top-0 z-10 flex items-start justify-between gap-2 bg-[var(--eds-surface)] py-1">
        <div>
          <Button size="sm" variant="ghost" className="min-h-11 min-w-11" onClick={props.onBack} aria-label="Назад">
            ←
          </Button>
          <h3 className="font-semibold">{String(item.name || "Загрузка…")}</h3>
          <p className="eds-type-small text-[var(--ew-muted)]">
            {typesRu(item.types)} · {ru(CP_STATUSES, String(item.status || ""))} · {String(item.responsible || "—")}
          </p>
          {item.is_demo ? <p className="eds-type-small">[DEMO]</p> : null}
        </div>
        {mobile ? (
          <Button size="sm" variant="ghost" className="min-h-11 min-w-11" onClick={() => setMenu((v) => !v)} aria-label="Ещё">
            ⋮
          </Button>
        ) : null}
      </header>
      <div className="eds-type-small grid gap-1 sm:grid-cols-2">
        <div>Телефон: {item.phone ? <a href={`tel:${String(item.phone)}`}>{String(item.phone)}</a> : "Нет данных"}</div>
        <div>Email: {item.email ? <a href={`mailto:${String(item.email)}`}>{String(item.email)}</a> : "Нет данных"}</div>
        <div>Город / регион: {String(item.city || item.region || "Нет данных")}</div>
        <div>Статус: {ru(CP_STATUSES, String(item.status || ""))}{item.status_reason ? ` · ${String(item.status_reason)}` : ""}</div>
        <div>Риск: {String(item.risk_level || "Нет данных")}</div>
        <div>Менеджер: {String(item.responsible || "Нет данных")}</div>
      </div>
      {props.canFinance && data?.aging ? (
        <p className="eds-type-small">
          Просрочено: {String((data.aging as Row).overdue_count || 0)} · самая старая: {String((data.aging as Row).oldest_days || "—")} дн.
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2" data-testid="agro-cp-quick">
        {item.phone ? (
          <a className="min-h-11 rounded-md border border-[var(--ew-border)] px-3 py-2 eds-type-small" href={`tel:${String(item.phone)}`}>
            📞
          </a>
        ) : null}
        {item.email ? (
          <a className="min-h-11 rounded-md border border-[var(--ew-border)] px-3 py-2 eds-type-small" href={`mailto:${String(item.email)}`}>
            💬
          </a>
        ) : null}
        {props.canCreate ? (
          <>
            <Button size="sm" onClick={() => props.onQuick("deal")}>
              Сделка
            </Button>
            <Button size="sm" variant="secondary" onClick={() => props.onQuick("task")}>
              Задача
            </Button>
            <Button size="sm" variant="secondary" onClick={() => props.onQuick("payment")}>
              Платёж
            </Button>
            <Button size="sm" variant="secondary" onClick={() => props.onQuick("shipment")}>
              Поставка
            </Button>
            <Button size="sm" variant="secondary" onClick={() => props.onQuick("contract")}>
              Договор
            </Button>
            <Button size="sm" variant="secondary" onClick={() => props.onQuick("documents")}>
              Документ
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setTab("notes")}>
              Заметка
            </Button>
          </>
        ) : null}
      </div>
      {menu ? (
        <div className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small">
          ЕДРПОУ: {String(item.edrpou || "Нет данных")}
        </div>
      ) : null}
      <div className={`flex gap-1 ${mobile ? "overflow-x-auto" : "flex-wrap"}`} data-testid="agro-cp-tabs">
        {tabs.map((t) => (
          <Button key={t.id} size="sm" variant={tab === t.id ? "secondary" : "ghost"} onClick={() => setTab(t.id)}>
            {t.label}
          </Button>
        ))}
      </div>
      {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}
      {tab === "overview" ? (
        <div className="grid gap-3 sm:grid-cols-2" data-testid="agro-cp-overview">
          <Card title="Компания">
            <p className="eds-type-small">Полное: {String(item.legal_name || item.name || "Нет данных")}</p>
            <p className="eds-type-small">Краткое: {String(item.short_name || "Нет данных")}</p>
            <p className="eds-type-small">ЕДРПОУ / ИНН: {String(item.edrpou || item.tax_id || "Нет данных")}</p>
            <p className="eds-type-small">НДС: {String(item.vat_status || "Нет данных")}</p>
            <p className="eds-type-small">Адрес: {String(item.address || item.legal_address || "Нет данных")}</p>
            {props.canFinance ? (
              <>
                <p className="eds-type-small">IBAN: {String(item.iban || "Нет данных")}</p>
                <p className="eds-type-small">Банк: {String(item.bank || "Нет данных")}</p>
              </>
            ) : (
              <p className="eds-type-small">Банковские реквизиты скрыты</p>
            )}
          </Card>
          <Card title="Расчёты">
            {props.canFinance ? (
              <>
                <p className="eds-type-small">Нам должны: {money((data?.settlement as Row | undefined)?.receivable)}</p>
                <p className="eds-type-small">Мы должны: {money((data?.settlement as Row | undefined)?.payable)}</p>
              </>
            ) : (
              <p className="eds-type-small">Нет доступа к финансам</p>
            )}
            {data?.margin ? <p className="eds-type-small">Маржа: {String((data.margin as Row).margin_pct ?? "не рассчитана")}</p> : <p className="eds-type-small">Маржа: нет данных</p>}
          </Card>
          <Card title="Культуры">
            {Array.isArray(data?.crops) && (data?.crops as Row[]).length ? (
              (data?.crops as Row[]).map((c) => (
                <p key={String(c.crop)} className="eds-type-small">
                  {String(c.crop)} · {String(c.direction_ru)} · объём {String(c.volume ?? "Нет данных")}
                  {c.avg_price != null ? ` · ср. цена ${String(c.avg_price)}` : ""}
                </p>
              ))
            ) : (
              <p className="eds-type-small">Нет данных</p>
            )}
          </Card>
          <Card title="Теги">
            <p className="eds-type-small">{Array.isArray(item.tags) && item.tags.length ? (item.tags as string[]).join(", ") : "Нет данных"}</p>
          </Card>
        </div>
      ) : null}
      {tab !== "overview" ? (
        <Card title={tabs.find((t) => t.id === tab)?.label || listTab}>
          {tab === "contacts" || tab === "more" ? (
            <div className="mb-3 grid gap-2 sm:grid-cols-2">
              <Input placeholder="ФИО" value={contact.full_name} onChange={(e) => setContact((f) => ({ ...f, full_name: e.target.value }))} />
              <Input placeholder="Должность" value={contact.position} onChange={(e) => setContact((f) => ({ ...f, position: e.target.value }))} />
              <Input placeholder="Телефон" value={contact.phone} onChange={(e) => setContact((f) => ({ ...f, phone: e.target.value }))} />
              <Input placeholder="Email" value={contact.email} onChange={(e) => setContact((f) => ({ ...f, email: e.target.value }))} />
              <Input placeholder="Telegram" value={contact.telegram} onChange={(e) => setContact((f) => ({ ...f, telegram: e.target.value }))} />
              <Input placeholder="WhatsApp" value={contact.whatsapp} onChange={(e) => setContact((f) => ({ ...f, whatsapp: e.target.value }))} />
              {props.canCreate ? (
                <Button size="sm" onClick={() => void addContact()}>
                  Добавить контакт
                </Button>
              ) : null}
            </div>
          ) : null}
          {tab === "notes" ? (
            <div className="mb-3 flex gap-2">
              <Input placeholder="Заметка" value={note} onChange={(e) => setNote(e.target.value)} />
              <Button size="sm" onClick={() => void addNote()}>
                Сохранить
              </Button>
            </div>
          ) : null}
          {tab === "communications" ? (
            <div className="mb-3 flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => void addCall()}>
                Добавить звонок
              </Button>
              <Button size="sm" variant="secondary" onClick={() => void followUp()}>
                Follow-up
              </Button>
            </div>
          ) : null}
          {rows.length === 0 ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
          <ul>
            {rows.map((r) => (
              <li key={String(r.id)} className="border-b border-[var(--ew-border)] py-2 eds-type-small">
                {listTab === "deals" ? (
                  <button type="button" className="text-left text-[var(--eds-primary)]" onClick={() => props.onOpenDeal(String(r.id))}>
                    {titleOf(r)}
                  </button>
                ) : (
                  titleOf(r)
                )}
                {r.phone ? (
                  <>
                    {" "}
                    <a href={`tel:${String(r.phone)}`}>{String(r.phone)}</a>
                  </>
                ) : null}
                {r.email ? (
                  <>
                    {" "}
                    <a href={`mailto:${String(r.email)}`}>{String(r.email)}</a>
                  </>
                ) : null}
                {r.telegram ? (
                  <>
                    {" "}
                    <a href={`https://t.me/${String(r.telegram).replace("@", "")}`}>Telegram</a>
                  </>
                ) : null}
                {r.whatsapp ? (
                  <>
                    {" "}
                    <a href={`https://wa.me/${String(r.whatsapp).replace(/\D/g, "")}`}>WhatsApp</a>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </div>
  );
}
