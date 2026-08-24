/**
 * AUTO 1.2 — customs operating desk.
 * Organization rates only. Not a live Гостаможня / НБУ calculator.
 */

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Button, Card, Input } from "@/ui";
import { asList, autoOpsDownload, autoOpsFileUrl, autoOpsGet, autoOpsPost, autoOpsUpload, pick } from "../business-ops/opsApi";
import { CASE_STATUS_RU, EXPENSE_RU, money } from "./autoLabels";

type Rec = Record<string, unknown>;

const TABS = [
  { id: "all", label: "Все дела" },
  { id: "docs", label: "Ожидают документы" },
  { id: "calc", label: "На расчёте" },
  { id: "pay", label: "К оплате" },
  { id: "release", label: "Оплачено / выпуск" },
  { id: "cert", label: "Сертификация" },
  { id: "reg", label: "Подготовка к регистрации" },
  { id: "done", label: "Завершённые" },
  { id: "problems", label: "Проблемные" },
];

const DESKS = [
  { id: "cases", label: "Дела" },
  { id: "brokers", label: "Брокеры" },
] as const;

const STATUSES = Object.keys(CASE_STATUS_RU);

export function AutoCustomsDesk({
  headers,
  canCreate,
  canFinance,
  canAdmin,
  vehicles,
  onOpenVehicle,
}: {
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  canAdmin?: boolean;
  vehicles: Rec[];
  onOpenVehicle: (id: string) => void;
}) {
  const [desk, setDesk] = useState<(typeof DESKS)[number]["id"]>("cases");
  const [tab, setTab] = useState("all");
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Rec[]>([]);
  const [counts, setCounts] = useState<Rec>({});
  const [selected, setSelected] = useState<Rec | null>(null);
  const [brokers, setBrokers] = useState<Rec[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  const loadCases = useCallback(async () => {
    const params = new URLSearchParams({ tab, q });
    const res = await autoOpsGet(`/customs/cases?${params.toString()}`, headers);
    const json = res.json as Rec;
    setItems(asList(json) as Rec[]);
    setCounts((json.counts || {}) as Rec);
  }, [headers, tab, q]);

  const loadBrokers = useCallback(async () => {
    const res = await autoOpsGet("/customs/brokers", headers);
    setBrokers(asList(res.json) as Rec[]);
  }, [headers]);

  useEffect(() => {
    void loadCases();
    void loadBrokers();
  }, [loadCases, loadBrokers]);

  async function post(path: string, body: Rec): Promise<boolean> {
    const res = await autoOpsPost(path, body, headers);
    const j = res.json as Rec;
    if (!res.ok || j.ok === false) {
      setMsg(String(j.message_ru || j.error || "Операция не выполнена"));
      return false;
    }
    setMsg("Сохранено");
    await loadCases();
    await loadBrokers();
    if (selected && path.includes(String(selected.id || ""))) {
      const det = await autoOpsGet(`/customs/cases/${String(selected.id)}`, headers);
      if (det.ok) setSelected({ ...(det.json as Rec), ...((det.json as Rec).item as Rec) });
    }
    return true;
  }

  async function openCase(id: string) {
    const det = await autoOpsGet(`/customs/cases/${id}`, headers);
    if (det.ok) setSelected({ ...(det.json as Rec), ...((det.json as Rec).item as Rec) });
  }

  return (
    <div className="space-y-4" data-testid="auto-customs-desk">
      <div className="flex flex-wrap gap-1">
        {DESKS.map((d) => (
          <Button key={d.id} size="sm" variant={desk === d.id ? undefined : "secondary"} onClick={() => setDesk(d.id)}>
            {d.label}
          </Button>
        ))}
      </div>
      {msg ? <p className="eds-type-helper">{msg}</p> : null}
      {desk === "cases" ? (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-1" data-testid="auto-customs-tabs">
            {TABS.map((t) => (
              <Button key={t.id} size="sm" variant={tab === t.id ? undefined : "secondary"} onClick={() => setTab(t.id)}>
                {t.label}
                {counts[t.id] != null ? ` (${String(counts[t.id])})` : ""}
              </Button>
            ))}
          </div>
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="VIN, брокер, декларация, номер, клиент" />
          {canFinance ? (
            <div className="flex flex-wrap gap-2" data-testid="auto-customs-export">
              {["customs_cases", "tax_breakdown", "customs_payments", "outstanding", "readiness", "registration"].map((kind) => (
                <Button key={kind} size="sm" variant="secondary" onClick={() => void autoOpsDownload(`/analytics/export?kind=${kind}&format=csv`, headers)}>
                  CSV {kind}
                </Button>
              ))}
            </div>
          ) : null}
          {canCreate ? (
            <CreateCaseForm vehicles={vehicles} brokers={brokers} onSubmit={(body) => post("/customs/cases", body)} />
          ) : null}
          <div className="grid gap-4 lg:grid-cols-2">
            <ul className="space-y-2">
              {items.length ? (
                items.map((c) => (
                  <li key={String(c.id)}>
                    <button className="w-full rounded border p-3 text-left" onClick={() => void openCase(String(c.id))}>
                      <strong>{pick(c, "vehicle_title")}</strong>
                      <p className="eds-type-helper">
                        {CASE_STATUS_RU[String(c.status)] || pick(c, "status_ru")} · {pick(c, "vin")}
                      </p>
                      <p className="eds-type-caption">{pick((c.answers as Rec) || {}, "where")}</p>
                    </button>
                  </li>
                ))
              ) : (
                <p className="eds-type-helper">Дел растаможки пока нет. Пустой список — это отсутствие записей, не ошибка.</p>
              )}
            </ul>
            {selected ? (
              <CasePanel
                selected={selected}
                canCreate={canCreate}
                canFinance={canFinance}
                canAdmin={Boolean(canAdmin)}
                headers={headers}
                post={post}
                onOpenVehicle={onOpenVehicle}
              />
            ) : (
              <p className="eds-type-helper">Откройте дело, чтобы увидеть где автомобиль, платежи и документы.</p>
            )}
          </div>
        </div>
      ) : (
        <BrokerDesk items={brokers} canCreate={canCreate} post={post} />
      )}
    </div>
  );
}

function CreateCaseForm({ vehicles, brokers, onSubmit }: { vehicles: Rec[]; brokers: Rec[]; onSubmit: (body: Rec) => Promise<boolean> }) {
  const [vehicleId, setVehicleId] = useState("");
  const [brokerId, setBrokerId] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!vehicleId) return;
    await onSubmit({ vehicle_id: vehicleId, broker_id: brokerId || undefined, status: "DOCUMENTS_PREP" });
  }
  return (
    <form onSubmit={(e) => void submit(e)} className="flex flex-wrap gap-2">
      <select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} className="rounded border px-2 py-1">
        <option value="">Автомобиль</option>
        {vehicles.map((v) => (
          <option key={String(v.id)} value={String(v.id)}>
            {pick(v, "title") || pick(v, "vin")}
          </option>
        ))}
      </select>
      <select value={brokerId} onChange={(e) => setBrokerId(e.target.value)} className="rounded border px-2 py-1">
        <option value="">Брокер (необязательно)</option>
        {brokers.map((b) => (
          <option key={String(b.id)} value={String(b.id)}>
            {pick(b, "company_name")}
          </option>
        ))}
      </select>
      <Button type="submit" size="sm">Создать дело</Button>
    </form>
  );
}

function CasePanel({
  selected,
  canCreate,
  canFinance,
  canAdmin,
  headers,
  post,
  onOpenVehicle,
}: {
  selected: Rec;
  canCreate: boolean;
  canFinance: boolean;
  canAdmin: boolean;
  headers: Record<string, string>;
  post: (path: string, body: Rec) => Promise<boolean>;
  onOpenVehicle: (id: string) => void;
}) {
  const answers = (selected.answers || {}) as Rec;
  const checklist = (selected.checklist || {}) as Rec;
  const calc = (selected.calculation || {}) as Rec;
  const payments = (selected.payments || {}) as Rec;
  const cert = (selected.certification || {}) as Rec;
  const reg = (selected.registration || {}) as Rec;
  const pipeline = asList(selected.pipeline, ["pipeline"]) as Rec[];
  const timeline = asList(selected.timeline, ["timeline"]) as Rec[];
  const missing = asList(checklist.missing) as Rec[];
  const cid = String(selected.id || "");
  const [status, setStatus] = useState(String(selected.status || "DOCUMENTS_PREP"));
  const [fx, setFx] = useState(String(selected.fx_rate_to_uah || ""));
  const [value, setValue] = useState(String(selected.customs_value || ""));
  const [cc, setCc] = useState(String(selected.engine_cc || ""));
  const [expCat, setExpCat] = useState("DUTY");
  const [expAmt, setExpAmt] = useState("");
  const [corrReason, setCorrReason] = useState("");
  const [corrAt, setCorrAt] = useState("");
  const summary = (selected.summary || {}) as Rec;

  const todo = asList(answers.todo) as unknown as string[];

  return (
    <div className="space-y-3" data-testid="auto-customs-case">
      <Card title={pick(selected, "vehicle_title")}>
        <p className="eds-type-helper">{CASE_STATUS_RU[String(selected.status)] || pick(selected, "status_ru")}</p>
        {selected.vehicle_id ? (
          <Button size="sm" variant="secondary" onClick={() => onOpenVehicle(String(selected.vehicle_id))}>
            Карточка автомобиля
          </Button>
        ) : null}
        {selected.is_demo ? <p className="eds-type-caption">DEMO — не продакшен</p> : null}
      </Card>
      <Card title="Сводка по растаможке">
        <dl className="grid gap-2 md:grid-cols-2" data-testid="auto-customs-summary">
          <QA q="Автомобиль" a={String(summary.vehicle || pick(selected, "vehicle_title") || "—")} />
          <QA q="VIN" a={String(summary.vin || pick(selected, "vin") || "—")} />
          <QA q="Брокер" a={String(summary.broker || pick(selected, "broker_name") || "—")} />
          <QA q="Декларация" a={String(summary.declaration || selected.declaration_number || "—")} />
        </dl>
      </Card>
      <Card title="Операционные вопросы">
        <dl className="grid gap-2" data-testid="auto-customs-answers">
          <QA q="Где автомобиль?" a={String(answers.where || "—")} />
          <QA q="Что сейчас происходит?" a={String(answers.happening || "—")} />
          <QA q="Что нужно сделать?" a={todo.length ? todo.join(" · ") : "—"} />
          <QA q="Каких документов не хватает?" a={missing.length ? missing.map((m) => String(m.label_ru)).join(" · ") : "Все обязательные загружены"} />
          <QA q="Сколько нужно заплатить?" a={canFinance && !payments.restricted ? money(answers.to_pay, "UAH") : "Суммы видит директор и бухгалтер"} />
          <QA q="Сколько уже заплачено?" a={canFinance && !payments.restricted ? money(answers.paid, "UAH") : "Суммы видит директор и бухгалтер"} />
          <QA q="Кто ответственный?" a={String(answers.responsible || "—")} />
          <QA q="Что является следующим этапом?" a={String(answers.next_stage || "—")} />
        </dl>
      </Card>
      <ol className="flex flex-wrap gap-2">
        {pipeline.map((s) => (
          <li key={String(s.id)} className={s.state === "current" ? "rounded bg-[var(--eds-primary)] px-2 py-1 text-white" : "rounded border px-2 py-1"}>
            {String(s.label_ru)}
          </li>
        ))}
      </ol>
      {canCreate ? (
        <div className="flex flex-wrap gap-2">
          <select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded border px-2 py-1">
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {CASE_STATUS_RU[s]}
              </option>
            ))}
          </select>
          <Button size="sm" onClick={() => void post(`/customs/cases/${cid}`, { status })}>
            Сменить статус
          </Button>
        </div>
      ) : null}
      {canAdmin ? (
        <div className="flex flex-wrap gap-2" data-testid="auto-customs-correction">
          <Input value={corrReason} onChange={(e) => setCorrReason(e.target.value)} placeholder="Причина коррекции" />
          <Input value={corrAt} onChange={(e) => setCorrAt(e.target.value)} placeholder="Дата коррекции" />
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void post(`/customs/cases/${cid}`, { status, correction_reason: corrReason, correction_at: corrAt })}
          >
            Коррекция статуса
          </Button>
        </div>
      ) : null}
      <Card title="Документы">
        <ul className="space-y-1" data-testid="auto-customs-checklist">
          {(asList(checklist.items) as Rec[]).map((row) => (
            <li key={String(row.id)} className="flex items-center justify-between gap-2">
              <span>
                {row.present ? "✓" : "○"} {pick(row, "label_ru")}
              </span>
              {row.preview && (row.preview as Rec).file_id ? (
                <a className="underline" href={autoOpsFileUrl(String((row.preview as Rec).file_id))} target="_blank" rel="noreferrer">
                  Просмотр
                </a>
              ) : null}
            </li>
          ))}
        </ul>
        {canCreate ? (
          <label className="mt-2 block eds-type-helper">
            Загрузить документ
            <input
              type="file"
              accept="image/*,application/pdf,.pdf,.doc,.docx,.jpg,.jpeg,.png,.webp"
              className="block"
              data-testid="auto-customs-file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                void (async () => {
                  const up = await autoOpsUpload("/files", file, { entity_type: "customs", entity_id: String(cid) }, headers);
                  const fileId = ((up.json as Rec).item as Rec | undefined)?.id || (up.json as Rec).id;
                  await post("/documents", {
                    owner_type: "customs",
                    customs_id: cid,
                    vehicle_id: selected.vehicle_id,
                    document_type: "invoice",
                    file_name: file.name,
                    file_id: fileId,
                  });
                })();
              }}
            />
          </label>
        ) : null}
      </Card>
      {canFinance && !calc.restricted ? (
        <Card title="Расчёт платежей">
          <p className="eds-type-helper">{String(calc.disclaimer_ru || "Расчёт по ставкам организации. Это не официальный калькулятор Гостаможни.")}</p>
          {calc.ok ? (
            <ul>
              {(asList(calc.lines) as Rec[]).map((line) => (
                <li key={String(line.id)}>
                  {pick(line, "label_ru")}: {money(line.amount_uah, "UAH")}
                </li>
              ))}
              <li>Итого: {money(calc.grand_total_uah, "UAH")}</li>
            </ul>
          ) : (
            <p>Не хватает данных: {(asList(calc.incomplete) as unknown as string[]).join(", ") || "стоимость / курс / двигатель"}</p>
          )}
          {canCreate ? (
            <div className="mt-2 flex flex-wrap gap-2">
              <Input value={value} onChange={(e) => setValue(e.target.value)} placeholder="Таможенная стоимость" />
              <Input value={fx} onChange={(e) => setFx(e.target.value)} placeholder="Курс к UAH (вручную)" />
              <Input value={cc} onChange={(e) => setCc(e.target.value)} placeholder="Объём, см³" />
              <Button
                size="sm"
                onClick={() => void post(`/customs/cases/${cid}/calculate`, { customs_value: value, fx_rate_to_uah: fx, engine_cc: cc })}
              >
                Пересчитать
              </Button>
            </div>
          ) : null}
        </Card>
      ) : null}
      {canFinance && !payments.restricted ? (
        <Card title="Платежи и НДС">
          <p>Заплачено: {money(payments.paid, "UAH")} · К оплате: {money(payments.due, "UAH")}</p>
          <p>НДС на импорт (учтено): {money(payments.import_vat_paid, "UAH")}</p>
          <p className="eds-type-caption">Курс введён вручную. Live НБУ не подключён.</p>
          {canCreate || canFinance ? (
            <div className="mt-2 flex flex-wrap gap-2">
              <select value={expCat} onChange={(e) => setExpCat(e.target.value)} className="rounded border px-2 py-1">
                {["DUTY", "EXCISE", "IMPORT_VAT", "BROKER", "CERTIFICATION", "REGISTRATION", "MREO"].map((c) => (
                  <option key={c} value={c}>
                    {EXPENSE_RU[c] || c}
                  </option>
                ))}
              </select>
              <Input value={expAmt} onChange={(e) => setExpAmt(e.target.value)} placeholder="Сумма UAH" />
              <Button
                size="sm"
                onClick={() =>
                  void post(`/customs/cases/${cid}/payments`, {
                    category: expCat,
                    amount: expAmt,
                    currency: "UAH",
                    comment: "desk",
                  })
                }
              >
                Добавить платёж
              </Button>
            </div>
          ) : null}
          <ul className="mt-2 space-y-1">
            {(asList(payments.lines) as Rec[]).map((line) => (
              <li key={String(line.id)} className="flex justify-between gap-2">
                <span>
                  {EXPENSE_RU[String(line.category)] || String(line.category)} · {money(line.amount, String(line.currency || "UAH"))} · {String(line.payment_status || "")}
                </span>
                {String(line.payment_status) === "planned" ? (
                  <Button size="sm" variant="secondary" onClick={() => void post(`/customs/cases/${cid}/payments/${String(line.id)}/confirm`, {})}>
                    Подтвердить
                  </Button>
                ) : null}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
      <Card title="Сертификация">
        <p>{String(cert.status_ru || "Не начата")}</p>
        <p className="eds-type-helper">{pick(cert, "body") || "Орган не указан"} {pick(cert, "number")}</p>
        {canCreate ? (
          <Button size="sm" variant="secondary" onClick={() => void post(`/customs/cases/${cid}`, { cert_status: "IN_PROGRESS", status: "CERTIFICATION" })}>
            В работу
          </Button>
        ) : null}
      </Card>
      <Card title="Подготовка к регистрации">
        <p>{String(reg.status_ru || "Пакет не готов")}</p>
        <p className="eds-type-helper">МРЕО: {pick(reg, "mreo_office") || "—"} · Номер: {pick(reg, "plate_expected") || "—"}</p>
        {canCreate ? (
          <Button size="sm" variant="secondary" onClick={() => void post(`/customs/cases/${cid}`, { reg_status: "DOCS_READY", status: "REGISTRATION_PREP" })}>
            Документы собраны
          </Button>
        ) : null}
      </Card>
      <Card title="История автомобиля на таможне">
        {timeline.length ? (
          <ul className="space-y-1">
            {timeline.map((ev) => (
              <li key={String(ev.id)} className="eds-type-helper">
                {pick(ev, "at")} · {pick(ev, "summary")}
              </li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-helper">Пока нет событий.</p>
        )}
      </Card>
    </div>
  );
}

function QA({ q, a }: { q: string; a: string }) {
  return (
    <div>
      <dt className="eds-type-caption">{q}</dt>
      <dd>{a}</dd>
    </div>
  );
}

function BrokerDesk({ items, canCreate, post }: { items: Rec[]; canCreate: boolean; post: (path: string, body: Rec) => Promise<boolean> }) {
  const [name, setName] = useState("");
  return (
    <div>
      {canCreate ? (
        <form
          className="mb-3 flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (name) void post("/customs/brokers", { company_name: name, type: "customs_broker" });
          }}
        >
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название брокера" />
          <Button type="submit" size="sm">Добавить</Button>
        </form>
      ) : null}
      <ul>
        {items.map((b) => (
          <li key={String(b.id)}>
            {pick(b, "company_name")} · {pick(b, "country") || "—"}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function VehicleCustomsBlock({ customs, canFinance }: { customs: Rec; canFinance: boolean }) {
  const cse = (customs.case || null) as Rec | null;
  if (!cse) return <p className="eds-type-helper">{String(customs.message_ru || "Дело растаможки ещё не создано.")}</p>;
  const answers = (cse.answers || {}) as Rec;
  const calc = (cse.calculation || {}) as Rec;
  const summary = (customs.summary || cse.summary || {}) as Rec;
  return (
    <div data-testid="auto-vehicle-customs">
      <Card title="Сводка по растаможке">
        <dl className="grid gap-2 md:grid-cols-2" data-testid="auto-customs-summary">
          <div><dt className="eds-type-caption">Автомобиль</dt><dd>{String(summary.vehicle || pick(cse, "vehicle_title") || "—")}</dd></div>
          <div><dt className="eds-type-caption">VIN</dt><dd>{String(summary.vin || pick(cse, "vin") || "—")}</dd></div>
          <div><dt className="eds-type-caption">Брокер</dt><dd>{String(summary.broker || pick(cse, "broker_name") || "—")}</dd></div>
          <div><dt className="eds-type-caption">Декларация</dt><dd>{String(summary.declaration || cse.declaration_number || "—")}</dd></div>
        </dl>
      </Card>
      <dl className="grid gap-2 md:grid-cols-2">
        <div><dt className="eds-type-caption">Статус</dt><dd>{CASE_STATUS_RU[String(cse.status)] || pick(cse, "status_ru")}</dd></div>
        <div><dt className="eds-type-caption">Где</dt><dd>{String(answers.where || "—")}</dd></div>
        <div><dt className="eds-type-caption">Брокер</dt><dd>{pick(cse, "broker_name") || "—"}</dd></div>
        <div><dt className="eds-type-caption">Следующий этап</dt><dd>{String(answers.next_stage || "—")}</dd></div>
      </dl>
      {canFinance && !calc.restricted && calc.ok ? <p className="mt-2">К оплате (расчёт): {money(calc.grand_total_uah, "UAH")}</p> : null}
      <p className="eds-type-caption mt-2">Расчёт по ставкам организации. Не официальный калькулятор Гостаможни.</p>
    </div>
  );
}

export function CustomsSettingsPanel({ catalogs, canAdmin, headers, canCreate }: { catalogs: Rec; canAdmin: boolean; headers: Record<string, string>; canCreate: boolean }) {
  const [duty, setDuty] = useState("0.10");
  const [vat, setVat] = useState("0.20");
  const [msg, setMsg] = useState<string | null>(null);
  return (
    <Card title="Растаможка">
      <p className="eds-type-helper">Ставки организации. Live-курс НБУ и калькулятор Гостаможни не подключены.</p>
      <p>Статусы: {(asList(catalogs.customs_case_statuses) as Rec[]).map((s) => String(s.label_ru)).join(" · ")}</p>
      {canAdmin ? (
        <div className="mt-3 flex gap-2">
          <Input value={duty} onChange={(e) => setDuty(e.target.value)} placeholder="Мито" />
          <Input value={vat} onChange={(e) => setVat(e.target.value)} placeholder="НДС" />
          <Button
            size="sm"
            onClick={() => {
              void autoOpsPost("/customs/settings", { duty_rate: Number(duty), vat_rate: Number(vat) }, headers).then((r) => {
                setMsg(r.ok ? "Ставки сохранены" : String((r.json as Rec).message_ru || "Ошибка"));
              });
            }}
          >
            Сохранить ставки
          </Button>
        </div>
      ) : (
        <p className="eds-type-helper">Менять ставки может администратор.</p>
      )}
      {msg ? <p className="eds-type-helper">{msg}</p> : null}
      {canCreate ? (
        <div className="mt-3">
          <p className="eds-type-helper">Демо BMW X5 USA → Украина. Явно помечено DEMO.</p>
          <Button size="sm" variant="secondary" onClick={() => void autoOpsPost("/customs/demo", { confirm_demo: true }, headers)}>
            Создать демо-дело
          </Button>
        </div>
      ) : null}
    </Card>
  );
}
