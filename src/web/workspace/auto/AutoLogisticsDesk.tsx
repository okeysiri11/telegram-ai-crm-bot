/**
 * AUTO 1.1 — logistics operating desk.
 * Manual ETA/locations only. Not live AIS / container tracking.
 */

import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Button, Card, Input } from "@/ui";
import { asList, autoOpsGet, autoOpsPost, autoOpsUpload, pick } from "../business-ops/opsApi";
import {
  DELAY_RU,
  EXPENSE_RU,
  SHIPMENT_STATUS_RU,
  SHIPMENT_TYPE_RU,
  money,
} from "./autoLabels";

type Rec = Record<string, unknown>;

const TABS = [
  { id: "all", label: "Все перевозки" },
  { id: "awaiting_pickup", label: "Ожидают забора" },
  { id: "inland", label: "В пути по стране покупки" },
  { id: "origin_port", label: "В порту" },
  { id: "container", label: "В контейнере" },
  { id: "sea", label: "В море" },
  { id: "destination_port", label: "В порту назначения" },
  { id: "ua_delivery", label: "Доставка по Украине" },
  { id: "done", label: "Завершённые" },
  { id: "problems", label: "Проблемные" },
];

const DESKS = [
  { id: "shipments", label: "Перевозки" },
  { id: "carriers", label: "Перевозчики" },
  { id: "drivers", label: "Водители" },
  { id: "trucks", label: "Транспорт" },
  { id: "containers", label: "Контейнеры" },
  { id: "vessels", label: "Суда" },
  { id: "ports", label: "Порты" },
] as const;

function delayClass(level: string): string {
  if (level === "red") return "bg-red-100 text-red-800";
  if (level === "orange") return "bg-orange-100 text-orange-800";
  if (level === "yellow") return "bg-yellow-100 text-yellow-800";
  return "bg-emerald-100 text-emerald-800";
}

function TrackingActions({
  sid,
  trackingUrl,
  headers,
  post,
  canCreate,
}: {
  sid: string;
  trackingUrl: string;
  headers: Record<string, string>;
  post: (path: string, body: Rec) => Promise<boolean>;
  canCreate: boolean;
}) {
  const [note, setNote] = useState<string | null>(null);
  const [last, setLast] = useState<string | null>(null);

  async function check() {
    const res = await autoOpsPost(`/logistics/shipments/${sid}/tracking`, {}, headers);
    const j = (res.json || {}) as Rec;
    setNote(String(j.message_ru || (j.available ? "Проверено" : "Автоматическое отслеживание недоступно")));
  }

  async function lastData() {
    const res = await autoOpsGet(`/logistics/shipments/${sid}/tracking?fetch=1`, headers);
    const j = (res.json || {}) as Rec;
    setLast(j.last ? JSON.stringify(j.last) : String(j.message_ru || "Автоматическое отслеживание недоступно"));
    if (!j.available) setNote(String(j.message_ru || "Автоматическое отслеживание недоступно"));
  }

  return (
    <div className="space-y-2" data-testid="auto-tracking-actions">
      {note ? <p className="eds-type-helper">{note}</p> : <p className="eds-type-helper">Автоматическое отслеживание недоступно</p>}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" onClick={() => void check()}>Проверить</Button>
        <Button size="sm" variant="secondary" onClick={() => void lastData()}>Последние данные</Button>
        {trackingUrl ? (
          <a className="underline eds-type-helper" href={trackingUrl} target="_blank" rel="noreferrer">Открыть источник</a>
        ) : (
          <Button size="sm" variant="secondary" onClick={() => setNote("Источник не задан. Укажите tracking URL перевозки.")}>Открыть источник</Button>
        )}
        <a className="underline eds-type-helper" href="/workspace/auto?view=settings">Настройки</a>
      </div>
      {last ? <p className="eds-type-caption">{last}</p> : null}
      {canCreate ? (
        <Button
          size="sm"
          variant="secondary"
          onClick={() => void post(`/logistics/shipments/${sid}/events`, { event_type: "comment", description: "Ручное событие отслеживания", source: "manual" })}
        >
          Добавить событие вручную
        </Button>
      ) : null}
    </div>
  );
}

export function AutoLogisticsDesk({
  headers,
  canCreate,
  canFinance,
  vehicles,
  onOpenVehicle,
}: {
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  vehicles: Rec[];
  onOpenVehicle: (id: string) => void;
}) {
  const [desk, setDesk] = useState<(typeof DESKS)[number]["id"]>("shipments");
  const [tab, setTab] = useState("all");
  const [q, setQ] = useState("");
  const [country, setCountry] = useState("");
  const [status, setStatus] = useState("");
  const [delayedOnly, setDelayedOnly] = useState(false);
  const [items, setItems] = useState<Rec[]>([]);
  const [counts, setCounts] = useState<Rec>({});
  const [selected, setSelected] = useState<Rec | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [refs, setRefs] = useState<{ carriers: Rec[]; containers: Rec[]; vessels: Rec[]; ports: Rec[]; drivers: Rec[]; trucks: Rec[] }>({
    carriers: [],
    containers: [],
    vessels: [],
    ports: [],
    drivers: [],
    trucks: [],
  });

  const loadShipments = useCallback(async () => {
    const params = new URLSearchParams({ tab, q, country, status, delayed: delayedOnly ? "1" : "" });
    const res = await autoOpsGet(`/logistics/shipments?${params.toString()}`, headers);
    const json = res.json as Rec;
    setItems(asList(json) as Rec[]);
    setCounts((json.counts || {}) as Rec);
  }, [headers, tab, q, country, status, delayedOnly]);

  const loadRefs = useCallback(async () => {
    const [carriers, containers, vessels, ports, drivers, trucks] = await Promise.all([
      autoOpsGet("/logistics/carriers", headers),
      autoOpsGet("/logistics/containers", headers),
      autoOpsGet("/logistics/vessels", headers),
      autoOpsGet("/logistics/ports", headers),
      autoOpsGet("/logistics/drivers", headers),
      autoOpsGet("/logistics/trucks", headers),
    ]);
    setRefs({
      carriers: asList(carriers.json) as Rec[],
      containers: asList(containers.json) as Rec[],
      vessels: asList(vessels.json) as Rec[],
      ports: asList(ports.json) as Rec[],
      drivers: asList(drivers.json) as Rec[],
      trucks: asList(trucks.json) as Rec[],
    });
  }, [headers]);

  useEffect(() => {
    void loadShipments();
    void loadRefs();
  }, [loadShipments, loadRefs]);

  async function post(path: string, body: Rec): Promise<boolean> {
    const res = await autoOpsPost(path, body, headers);
    const j = res.json as Rec;
    if (!res.ok || j.ok === false) {
      setMsg(String(j.message_ru || j.error || "Операция не выполнена"));
      return false;
    }
    setMsg("Сохранено");
    await loadShipments();
    await loadRefs();
    if (selected && path.includes(String(selected.id || ""))) {
      const det = await autoOpsGet(`/logistics/shipments/${String(selected.id)}`, headers);
      if (det.ok) setSelected((det.json as Rec).item as Rec);
    }
    return true;
  }

  async function openShipment(id: string) {
    const det = await autoOpsGet(`/logistics/shipments/${id}`, headers);
    if (det.ok) setSelected({ ...(det.json as Rec), ...(det.json as Rec).item as Rec });
  }

  return (
    <div className="space-y-4" data-testid="auto-logistics-desk">
      <div className="flex flex-wrap gap-1">
        {DESKS.map((d) => (
          <Button key={d.id} size="sm" variant={desk === d.id ? undefined : "secondary"} onClick={() => setDesk(d.id)}>
            {d.label}
          </Button>
        ))}
      </div>
      {msg ? <p className="eds-type-helper">{msg}</p> : null}
      {desk === "shipments" ? (
        <ShipmentsPanel
          items={items}
          counts={counts}
          tab={tab}
          setTab={setTab}
          q={q}
          setQ={setQ}
          country={country}
          setCountry={setCountry}
          status={status}
          setStatus={setStatus}
          delayedOnly={delayedOnly}
          setDelayedOnly={setDelayedOnly}
          canCreate={canCreate}
          canFinance={canFinance}
          selected={selected}
          setSelected={setSelected}
          onOpen={openShipment}
          onOpenVehicle={onOpenVehicle}
          post={post}
          headers={headers}
          vehicles={vehicles}
          refs={refs}
        />
      ) : null}
      {desk === "carriers" ? <SimpleDesk title="Перевозчики" path="/logistics/carriers" items={refs.carriers} canCreate={canCreate} post={post} fields={["company_name", "type", "country", "phone", "telegram"]} /> : null}
      {desk === "drivers" ? <SimpleDesk title="Водители" path="/logistics/drivers" items={refs.drivers} canCreate={canCreate} post={post} fields={["full_name", "phone", "telegram", "carrier_id"]} note="Паспорт и ВУ скрыты без роли директора/администратора." /> : null}
      {desk === "trucks" ? <SimpleDesk title="Транспорт" path="/logistics/trucks" items={refs.trucks} canCreate={canCreate} post={post} fields={["plate_number", "type", "brand", "model", "country"]} /> : null}
      {desk === "containers" ? <ContainerDesk items={refs.containers} canCreate={canCreate} post={post} vehicles={vehicles} headers={headers} /> : null}
      {desk === "vessels" ? <SimpleDesk title="Суда" path="/logistics/vessels" items={refs.vessels} canCreate={canCreate} post={post} fields={["name", "shipping_line", "voyage_number", "eta"]} note="Позиция судна введена вручную. Live AIS не подключён." /> : null}
      {desk === "ports" ? <PortsDesk items={refs.ports} canCreate={canCreate} post={post} /> : null}
    </div>
  );
}

function ShipmentsPanel(props: {
  items: Rec[];
  counts: Rec;
  tab: string;
  setTab: (t: string) => void;
  q: string;
  setQ: (v: string) => void;
  country: string;
  setCountry: (v: string) => void;
  status: string;
  setStatus: (v: string) => void;
  delayedOnly: boolean;
  setDelayedOnly: (v: boolean) => void;
  canCreate: boolean;
  canFinance: boolean;
  selected: Rec | null;
  setSelected: (v: Rec | null) => void;
  onOpen: (id: string) => void;
  onOpenVehicle: (id: string) => void;
  post: (path: string, body: Rec) => Promise<boolean>;
  headers: Record<string, string>;
  vehicles: Rec[];
  refs: { carriers: Rec[]; containers: Rec[]; vessels: Rec[] };
}) {
  const [createOpen, setCreateOpen] = useState(false);
  return (
    <div className="space-y-3">
      <p className="eds-type-title text-lg">Где сейчас автомобиль?</p>
      <div className="flex flex-wrap gap-2" data-testid="auto-logistics-tabs">
        {TABS.map((t) => (
          <Button key={t.id} size="sm" variant={props.tab === t.id ? undefined : "secondary"} onClick={() => props.setTab(t.id)}>
            {t.label} ({Number(props.counts[t.id] || 0)})
          </Button>
        ))}
      </div>
      <div className="grid gap-2 md:grid-cols-5">
        <Input placeholder="VIN, контейнер, B/L, судно, перевозчик" value={props.q} onChange={(e) => props.setQ(e.target.value)} />
        <Input placeholder="Страна" value={props.country} onChange={(e) => props.setCountry(e.target.value)} />
        <select className="rounded border px-2 py-1" value={props.status} onChange={(e) => props.setStatus(e.target.value)}>
          <option value="">Все статусы</option>
          {Object.entries(SHIPMENT_STATUS_RU).map(([id, label]) => (
            <option key={id} value={id}>{label}</option>
          ))}
        </select>
        <label className="flex items-center gap-2 eds-type-caption">
          <input type="checkbox" checked={props.delayedOnly} onChange={(e) => props.setDelayedOnly(e.target.checked)} />
          Только с задержкой
        </label>
        {props.canCreate ? <Button onClick={() => setCreateOpen(true)}>+ Перевозка</Button> : null}
      </div>
      {createOpen ? (
        <CreateShipment vehicles={props.vehicles} onCancel={() => setCreateOpen(false)} onSubmit={async (body) => {
          const ok = await props.post("/logistics/shipments", body);
          if (ok) setCreateOpen(false);
          return ok;
        }} />
      ) : null}
      <div className="overflow-x-auto rounded border">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b text-left">
              {["Фото", "Автомобиль", "VIN", "Страна", "Этап", "Где", "Перевозчик", "Контейнер", "Судно", "ETA", "Задержка", "Менеджер", "Стоимость"].map((h) => (
                <th key={h} className="px-2 py-2 eds-type-caption">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {props.items.map((s) => {
              const delay = (s.delay || {}) as Rec;
              return (
                <tr key={String(s.id)} className="border-b hover:bg-[var(--eds-surface-muted,#f8fafc)]">
                  <td className="px-2 py-2">{s.cover_file_id ? "●" : "—"}</td>
                  <td className="px-2 py-2">
                    <button className="underline" onClick={() => void props.onOpen(String(s.id))}>{pick(s, "vehicle_title")}</button>
                  </td>
                  <td className="px-2 py-2 font-mono">{pick(s, "vin")}</td>
                  <td className="px-2 py-2">{pick(s, "origin_country")}</td>
                  <td className="px-2 py-2">{pick(s, "status_ru")}</td>
                  <td className="px-2 py-2">{pick(s, "current_location")}</td>
                  <td className="px-2 py-2">{pick(s, "carrier_name")}</td>
                  <td className="px-2 py-2">{pick(s, "container_number")}</td>
                  <td className="px-2 py-2">{pick(s, "vessel_name")}</td>
                  <td className="px-2 py-2">{String((delay.current_eta as string) || s.eta || "—")}<div className="eds-type-caption">Введено вручную</div></td>
                  <td className="px-2 py-2"><span className={`rounded px-2 py-0.5 ${delayClass(String(delay.level || "green"))}`}>{DELAY_RU[String(delay.level)] || "В срок"}</span></td>
                  <td className="px-2 py-2">{pick(s, "responsible_manager_id")}</td>
                  <td className="px-2 py-2">{props.canFinance && !(s.costs as Rec)?.restricted ? money((s.costs as Rec)?.actual) : "скрыто"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!props.items.length ? <p className="p-4 eds-type-helper">Перевозок нет. Система не создаёт фиктивные маршруты.</p> : null}
      </div>
      {props.selected ? (
        <ShipmentCard
          data={props.selected}
          canCreate={props.canCreate}
          canFinance={props.canFinance}
          refs={props.refs}
          headers={props.headers}
          post={props.post}
          onClose={() => props.setSelected(null)}
          onOpenVehicle={props.onOpenVehicle}
        />
      ) : null}
    </div>
  );
}

function ShipmentCard({
  data,
  canCreate,
  canFinance,
  refs,
  headers,
  post,
  onClose,
  onOpenVehicle,
}: {
  data: Rec;
  canCreate: boolean;
  canFinance: boolean;
  refs: { carriers: Rec[]; containers: Rec[]; vessels: Rec[] };
  headers: Record<string, string>;
  post: (path: string, body: Rec) => Promise<boolean>;
  onClose: () => void;
  onOpenVehicle: (id: string) => void;
}) {
  const sid = String(data.id || "");
  const pipeline = asList(data.pipeline, ["pipeline"]) as Rec[];
  const delay = (data.delay || {}) as Rec;
  const costs = (data.costs || {}) as Rec;
  const route = (data.route || {}) as Rec;
  const [status, setStatus] = useState(String(data.status || "PLANNED"));
  const [eta, setEta] = useState(String(data.current_eta || data.eta || ""));
  const [eventText, setEventText] = useState("");
  const [expense, setExpense] = useState({ category: "SEA_FREIGHT", amount: "", payment_status: "planned" });
  const [task, setTask] = useState({ title: "Проверить ETA", due_at: "" });
  const [carrierId, setCarrierId] = useState(String(data.carrier_id || ""));
  const [containerId, setContainerId] = useState(String(data.container_id || ""));
  const [vesselId, setVesselId] = useState(String(data.vessel_id || ""));
  const docs = asList(data.documents) as Rec[];
  const events = asList(data.events) as Rec[];

  return (
    <div data-testid="auto-shipment-card">
    <Card title={`Перевозка · ${pick(data, "vehicle_title")} · ${pick(data, "vin")}`}>
      <div className="flex justify-between gap-2">
        <button className="underline" onClick={() => onOpenVehicle(String(data.vehicle_id))}>Открыть автомобиль</button>
        <Button variant="secondary" size="sm" onClick={onClose}>Закрыть</Button>
      </div>
      <p className="eds-type-helper">Где сейчас: {pick(data, "current_location")} · {pick(data, "status_ru")}</p>
      <span className={`inline-block rounded px-2 py-0.5 ${delayClass(String(delay.level || "green"))}`}>{DELAY_RU[String(delay.level)] || "В срок"} · {String(delay.delay_days || 0)} дн.</span>
      <ol className="mt-3 flex flex-wrap items-center gap-2" data-testid="auto-logistics-pipeline">
        {pipeline.map((step, i) => (
          <li key={String(step.id)} className="flex items-center gap-2">
            <span className={step.state === "current" ? "rounded bg-[var(--eds-primary)] px-2 py-1 text-white" : step.state === "done" ? "rounded bg-[var(--eds-success-soft,#dcfce7)] px-2 py-1" : "rounded border px-2 py-1 text-[var(--eds-text-muted)]"}>
              {String(step.label_ru)}
            </span>
            {i < pipeline.length - 1 ? <span>↓</span> : null}
          </li>
        ))}
      </ol>
      <div className="mt-3 rounded border p-3" data-testid="auto-logistics-map">
        <p className="eds-type-caption">{String(route.label_ru || "Схема маршрута, не live-tracking")}</p>
        <p>{pick(route, "origin")} → {pick(route, "port")} → {pick(route, "destination")}</p>
      </div>
      {canFinance && !costs.restricted ? (
        <p className="mt-2">План {money(costs.planned)} · Факт {money(costs.actual)} · Оплачено {money(costs.paid)} · Не оплачено {money(costs.unpaid)}</p>
      ) : null}
      {canCreate ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="space-y-2">
            <select className="w-full rounded border px-2 py-1" value={status} onChange={(e) => setStatus(e.target.value)}>
              {Object.entries(SHIPMENT_STATUS_RU).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
            <Button size="sm" onClick={() => void post(`/logistics/shipments/${sid}`, { status })}>Изменить этап</Button>
            <Input type="date" value={eta} onChange={(e) => setEta(e.target.value)} />
            <Button size="sm" onClick={() => void post(`/logistics/shipments/${sid}`, { eta, current_eta: eta })}>Изменить ETA</Button>
            <Input value={eventText} onChange={(e) => setEventText(e.target.value)} placeholder="Комментарий / событие" />
            <Button size="sm" onClick={() => void post(`/logistics/shipments/${sid}/events`, { event_type: "comment", description: eventText, comment: eventText })}>Добавить событие</Button>
            <Button size="sm" variant="secondary" onClick={() => void post(`/logistics/shipments/${sid}/events`, { event_type: "comment", description: eventText || "Комментарий" })}>Добавить комментарий</Button>
          </div>
          <div className="space-y-2">
            <select className="w-full rounded border px-2 py-1" value={carrierId} onChange={(e) => setCarrierId(e.target.value)}>
              <option value="">Перевозчик</option>
              {refs.carriers.map((c) => <option key={String(c.id)} value={String(c.id)}>{String(c.company_name)}</option>)}
            </select>
            <Button size="sm" onClick={() => void post(`/logistics/shipments/${sid}`, { carrier_id: carrierId })}>Назначить перевозчика</Button>
            <select className="w-full rounded border px-2 py-1" value={containerId} onChange={(e) => setContainerId(e.target.value)}>
              <option value="">Контейнер</option>
              {refs.containers.map((c) => <option key={String(c.id)} value={String(c.id)}>{String(c.container_number)}</option>)}
            </select>
            <Button size="sm" onClick={() => void post(`/logistics/shipments/${sid}`, { container_id: containerId })}>Назначить контейнер</Button>
            <select className="w-full rounded border px-2 py-1" value={vesselId} onChange={(e) => setVesselId(e.target.value)}>
              <option value="">Судно</option>
              {refs.vessels.map((c) => <option key={String(c.id)} value={String(c.id)}>{String(c.name)}</option>)}
            </select>
            <Button size="sm" onClick={() => void post(`/logistics/shipments/${sid}`, { vessel_id: vesselId })}>Назначить судно</Button>
          </div>
          <div className="space-y-2">
            <select className="w-full rounded border px-2 py-1" value={expense.category} onChange={(e) => setExpense({ ...expense, category: e.target.value })}>
              {["INLAND_TRANSPORT", "PORT_FEE", "CONTAINER", "SEA_FREIGHT", "FORWARDER", "DEMURRAGE", "UA_TRANSPORT", "TOW_TRUCK"].map((id) => (
                <option key={id} value={id}>{EXPENSE_RU[id] || id}</option>
              ))}
            </select>
            <Input value={expense.amount} onChange={(e) => setExpense({ ...expense, amount: e.target.value })} placeholder="Сумма" />
            <Button size="sm" onClick={() => void post("/expenses", { shipment_id: sid, vehicle_id: data.vehicle_id, ...expense, amount: Number(expense.amount) })}>Добавить расход</Button>
            <Input value={task.title} onChange={(e) => setTask({ ...task, title: e.target.value })} />
            <Input type="date" value={task.due_at} onChange={(e) => setTask({ ...task, due_at: e.target.value })} />
            <Button size="sm" onClick={() => void post("/tasks", { ...task, shipment_id: sid, vehicle_id: data.vehicle_id })}>Создать задачу</Button>
            <input
              type="file"
              accept="image/*,application/pdf,.pdf,.doc,.docx,.jpg,.jpeg,.png,.webp"
              data-testid="auto-logistics-file"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                await autoOpsUpload("/files", file, { entity_type: "shipment", entity_id: sid, document_type: "bill_of_lading" }, headers);
                await post(`/logistics/shipments/${sid}/events`, { event_type: "document_added", description: file.name });
              }}
            />
            <p className="eds-type-caption">Документ / фото (скрепка)</p>
          </div>
        </div>
      ) : null}
      <h4 className="mt-4 eds-type-section">Отслеживание</h4>
      <TrackingActions sid={sid} trackingUrl={String(data.tracking_url || "")} headers={headers} post={post} canCreate={canCreate} />
      <h4 className="mt-4 eds-type-section">События</h4>
      <ul>{events.map((ev) => <li key={String(ev.id)} className="eds-type-helper">{pick(ev, "created_at")} · <span data-testid="auto-event-source">{String(ev.source || "MANUAL")}</span> · {String(ev.confirmation || "")} · {pick(ev, "description")}</li>)}</ul>
      <h4 className="mt-2 eds-type-section">Документы</h4>
      <ul>{docs.map((d) => <li key={String(d.id)}>{pick(d, "file_name", "title")}</li>)}</ul>
    </Card>
    </div>
  );
}

function CreateShipment({ vehicles, onCancel, onSubmit }: { vehicles: Rec[]; onCancel: () => void; onSubmit: (body: Rec) => Promise<boolean> }) {
  const [form, setForm] = useState({ vehicle_id: "", shipment_type: "CONTAINER", origin_country: "US", destination_country: "UA", origin_location: "", eta: "" });
  return (
    <Card title="Новая перевозка">
      <form className="grid gap-2 md:grid-cols-2" onSubmit={(e: FormEvent) => { e.preventDefault(); void onSubmit(form); }}>
        <select className="rounded border px-2 py-1" value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })} required>
          <option value="">Автомобиль</option>
          {vehicles.map((v) => <option key={String(v.id)} value={String(v.id)}>{pick(v, "vin")} {pick(v, "model")}</option>)}
        </select>
        <select className="rounded border px-2 py-1" value={form.shipment_type} onChange={(e) => setForm({ ...form, shipment_type: e.target.value })}>
          {Object.entries(SHIPMENT_TYPE_RU).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
        </select>
        <Input placeholder="Страна покупки" value={form.origin_country} onChange={(e) => setForm({ ...form, origin_country: e.target.value })} />
        <Input placeholder="Страна назначения" value={form.destination_country} onChange={(e) => setForm({ ...form, destination_country: e.target.value })} />
        <Input placeholder="Откуда" value={form.origin_location} onChange={(e) => setForm({ ...form, origin_location: e.target.value })} />
        <Input type="date" value={form.eta} onChange={(e) => setForm({ ...form, eta: e.target.value })} />
        <div className="flex gap-2">
          <Button type="submit">Создать</Button>
          <Button type="button" variant="secondary" onClick={onCancel}>Отмена</Button>
        </div>
      </form>
    </Card>
  );
}

function SimpleDesk({ title, path, items, canCreate, post, fields, note }: { title: string; path: string; items: Rec[]; canCreate: boolean; post: (path: string, body: Rec) => Promise<boolean>; fields: string[]; note?: string }) {
  const [form, setForm] = useState<Rec>({});
  return (
    <Card title={title}>
      {note ? <p className="eds-type-helper">{note}</p> : null}
      <ul className="mb-3 space-y-1">
        {items.map((row) => (
          <li key={String(row.id)}>{fields.map((f) => pick(row, f)).join(" · ")}{row.pii_restricted ? " · PII скрыто" : ""}</li>
        ))}
        {!items.length ? <p className="eds-type-helper">Записей нет.</p> : null}
      </ul>
      {canCreate ? (
        <form className="grid gap-2 md:grid-cols-3" onSubmit={(e) => { e.preventDefault(); void post(path, form); }}>
          {fields.map((f) => (
            <Input key={f} placeholder={f} value={String(form[f] || "")} onChange={(e) => setForm({ ...form, [f]: e.target.value })} />
          ))}
          <Button type="submit">Сохранить</Button>
        </form>
      ) : null}
    </Card>
  );
}

function ContainerDesk({ items, canCreate, post, vehicles, headers }: { items: Rec[]; canCreate: boolean; post: (p: string, b: Rec) => Promise<boolean>; vehicles: Rec[]; headers: Record<string, string> }) {
  const [form, setForm] = useState({ container_number: "", container_type: "40HC", shipping_line: "", booking_number: "" });
  const [openId, setOpenId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Rec | null>(null);
  const [vehicleId, setVehicleId] = useState("");
  useEffect(() => {
    if (!openId) return;
    void autoOpsGet(`/logistics/containers/${openId}`, headers).then((r) => setDetail(r.json as Rec));
  }, [openId, headers]);
  return (
    <div className="space-y-3" data-testid="auto-containers">
      <Card title="Контейнеры">
        <p className="eds-type-helper">Live-tracking контейнера не подключён. ETA введена вручную.</p>
        {items.map((c) => (
          <button key={String(c.id)} className="mr-2 underline" onClick={() => setOpenId(String(c.id))}>{pick(c, "container_number")} · {pick(c, "status")}</button>
        ))}
        {canCreate ? (
          <form className="mt-3 grid gap-2 md:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void post("/logistics/containers", form); }}>
            <Input placeholder="Номер" value={form.container_number} onChange={(e) => setForm({ ...form, container_number: e.target.value })} />
            <select className="rounded border px-2 py-1" value={form.container_type} onChange={(e) => setForm({ ...form, container_type: e.target.value })}>
              {["20FT", "40FT", "40HC", "45FT", "OTHER"].map((t) => <option key={t}>{t}</option>)}
            </select>
            <Input placeholder="Линия" value={form.shipping_line} onChange={(e) => setForm({ ...form, shipping_line: e.target.value })} />
            <Button type="submit">Создать контейнер</Button>
          </form>
        ) : null}
      </Card>
      {detail ? (
        <Card title={`Контейнер ${pick((detail.item || {}) as Rec, "container_number")}`}>
          <p>Состав: {asList(detail.vehicles).length} а/м</p>
          <ul>{(asList(detail.vehicles) as Rec[]).map((v) => <li key={String(v.id)}>{pick((v.vehicle || v) as Rec, "vin")}</li>)}</ul>
          {canCreate ? (
            <div className="mt-2 flex gap-2">
              <select className="rounded border px-2 py-1" value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
                <option value="">Автомобиль</option>
                {vehicles.map((v) => <option key={String(v.id)} value={String(v.id)}>{pick(v, "vin")}</option>)}
              </select>
              <Button size="sm" onClick={() => void post(`/logistics/containers/${openId}/vehicles`, { vehicle_id: vehicleId })}>+ Добавить автомобиль в контейнер</Button>
            </div>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}

function PortsDesk({ items, canCreate, post }: { items: Rec[]; canCreate: boolean; post: (p: string, b: Rec) => Promise<boolean> }) {
  const own = items.filter((p) => p.source === "organization");
  const refs = items.filter((p) => p.source === "reference");
  const [form, setForm] = useState({ name: "", unlocode: "", country: "", city: "" });
  return (
    <Card title="Порты">
      <p className="eds-type-helper">Справочные UN/LOCODE не выдумываются и не пишутся в продакшен автоматически.</p>
      <p className="eds-type-caption">Справочник: {refs.map((p) => `${p.unlocode} ${p.name}`).join(" · ")}</p>
      <ul className="mt-2">{own.map((p) => <li key={String(p.id)}>{pick(p, "name")} · {pick(p, "unlocode")}</li>)}</ul>
      {canCreate ? (
        <form className="mt-3 grid gap-2 md:grid-cols-4" onSubmit={(e) => { e.preventDefault(); void post("/logistics/ports", form); }}>
          <Input placeholder="Название" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="UN/LOCODE (опц.)" value={form.unlocode} onChange={(e) => setForm({ ...form, unlocode: e.target.value })} />
          <Input placeholder="Страна" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
          <Button type="submit">Добавить порт организации</Button>
        </form>
      ) : null}
    </Card>
  );
}

export function VehicleLogisticsBlock({ logistics, canFinance }: { logistics: Rec; canFinance: boolean }) {
  const ship = (logistics.shipment || null) as Rec | null;
  if (!ship) return <p className="eds-type-helper">{String(logistics.message_ru || "Перевозка ещё не создана.")}</p>;
  const delay = (ship.delay || {}) as Rec;
  const costs = (ship.costs || {}) as Rec;
  const pipeline = asList(ship.pipeline, ["pipeline"]) as Rec[];
  return (
    <div data-testid="auto-vehicle-logistics">
      <dl className="grid gap-2 md:grid-cols-2">
        <div><dt className="eds-type-caption">Статус</dt><dd>{pick(ship, "status_ru")}</dd></div>
        <div><dt className="eds-type-caption">Где сейчас</dt><dd>{pick(ship, "current_location")}</dd></div>
        <div><dt className="eds-type-caption">Перевозчик</dt><dd>{pick(ship, "carrier_name")}</dd></div>
        <div><dt className="eds-type-caption">Контейнер</dt><dd>{pick(ship, "container_number")}</dd></div>
        <div><dt className="eds-type-caption">Судно</dt><dd>{pick(ship, "vessel_name")}</dd></div>
        <div><dt className="eds-type-caption">Маршрут</dt><dd>{pick(ship.origin_country ? ship : {}, "origin_country")} → {pick(ship, "destination_country")}</dd></div>
        <div><dt className="eds-type-caption">ETD / ETA</dt><dd>{pick(ship, "etd")} / {pick(ship, "eta")} · Введено вручную</dd></div>
        <div><dt className="eds-type-caption">Задержка</dt><dd>{DELAY_RU[String(delay.level)] || "В срок"}</dd></div>
      </dl>
      {canFinance && !costs.restricted ? <p className="mt-2">Стоимость логистики: план {money(costs.planned)} / факт {money(costs.actual)}</p> : null}
      <ol className="mt-3 flex flex-wrap gap-2">
        {pipeline.map((s) => <li key={String(s.id)} className={s.state === "current" ? "rounded bg-[var(--eds-primary)] px-2 py-1 text-white" : "rounded border px-2 py-1"}>{String(s.label_ru)}</li>)}
      </ol>
      <h4 className="mt-4 eds-type-section">История</h4>
      <ul data-testid="auto-logistics-history">
        {(asList(logistics.history) as Rec[]).length ? (
          (asList(logistics.history) as Rec[]).map((h) => (
            <li key={String(h.id)} className="eds-type-helper">
              {pick(h, "at")} · {pick(h, "title")} · {String(h.source || "")}
            </li>
          ))
        ) : (
          <li className="eds-type-helper">История появится после событий перевозки.</li>
        )}
      </ul>
    </div>
  );
}

export function LogisticsSettingsPanel({ catalogs, canAdmin, headers }: { catalogs: Rec; canAdmin: boolean; headers: Record<string, string> }) {
  const [yellow, setYellow] = useState("3");
  const [orange, setOrange] = useState("7");
  const [msg, setMsg] = useState<string | null>(null);
  const [providers, setProviders] = useState<Rec[]>([]);
  const [form, setForm] = useState({ name: "", type: "ais", url: "", api_key_env: "", enabled: false });

  const loadProviders = useCallback(async () => {
    const res = await autoOpsGet("/logistics/providers", headers);
    setProviders(asList(res.json) as Rec[]);
  }, [headers]);

  useEffect(() => {
    void loadProviders();
  }, [loadProviders]);

  return (
    <Card title="Логистика">
      <p className="eds-type-helper">Статусы, типы перевозок, порты и пороги задержки. Live-tracking не включён.</p>
      <p>Типы: {(asList(catalogs.shipment_types) as Rec[]).map((s) => String(s.label_ru)).join(" · ")}</p>
      <p>Статусы: {(asList(catalogs.shipment_statuses) as Rec[]).map((s) => String(s.label_ru)).join(" · ")}</p>
      <p>Порты справочника: {(asList(catalogs.reference_ports) as Rec[]).map((s) => String(s.unlocode)).join(", ")}</p>
      {canAdmin ? (
        <div className="mt-3 flex gap-2">
          <Input value={yellow} onChange={(e) => setYellow(e.target.value)} />
          <Input value={orange} onChange={(e) => setOrange(e.target.value)} />
          <Button size="sm" onClick={async () => {
            const res = await autoOpsPost("/logistics/settings", { yellow_days: Number(yellow), orange_days: Number(orange) }, headers);
            setMsg((res.json as Rec).ok ? "Сохранено" : String((res.json as Rec).message_ru || "Ошибка"));
          }}>Пороги задержки</Button>
        </div>
      ) : null}
      <div className="mt-4" data-testid="auto-logistics-providers">
        <h4 className="eds-type-section">Провайдеры логистики</h4>
        <p className="eds-type-helper">Имя переменной ключа, не само значение. Секреты в интерфейс не выводятся.</p>
        <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr>
              <th>Провайдер</th>
              <th>Тип</th>
              <th>URL</th>
              <th>API key environment name</th>
              <th>Статус</th>
              <th>Последняя проверка</th>
              <th>Ошибка</th>
              <th>Включён</th>
            </tr>
          </thead>
          <tbody>
            {providers.map((p) => (
              <tr key={String(p.id)}>
                <td>{pick(p, "name")}</td>
                <td>{pick(p, "type")}</td>
                <td>{pick(p, "url")}</td>
                <td>{pick(p, "api_key_env")}</td>
                <td>{pick(p, "status_ru", "status")}</td>
                <td>{pick(p, "last_check_at")}</td>
                <td>{pick(p, "last_error")}</td>
                <td>{p.enabled ? "да" : "нет"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
        {canAdmin ? (
          <form
            className="mt-3 grid gap-2 md:grid-cols-2"
            onSubmit={async (e: FormEvent) => {
              e.preventDefault();
              await autoOpsPost("/logistics/providers", form, headers);
              setForm({ name: "", type: "ais", url: "", api_key_env: "", enabled: false });
              await loadProviders();
            }}
          >
            <Input placeholder="Провайдер" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <select className="rounded border px-2 py-1" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option value="ais">AIS / судно</option>
              <option value="container">Контейнер</option>
              <option value="vessel">Судоходная линия</option>
              <option value="port">Порт</option>
              <option value="other">Другое</option>
            </select>
            <Input placeholder="URL" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} />
            <Input placeholder="API key environment name" value={form.api_key_env} onChange={(e) => setForm({ ...form, api_key_env: e.target.value })} />
            <label className="flex items-center gap-2 eds-type-helper">
              <input type="checkbox" checked={form.enabled} onChange={(e) => setForm({ ...form, enabled: e.target.checked })} />
              Включён
            </label>
            <Button type="submit" size="sm">Сохранить провайдера</Button>
          </form>
        ) : null}
      </div>
      {msg ? <p className="eds-type-helper">{msg}</p> : null}
    </Card>
  );
}
