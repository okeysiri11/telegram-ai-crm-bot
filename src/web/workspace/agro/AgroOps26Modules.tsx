/**
 * AGRO 2.6 — operational modules: Культуры (агро), Посевы, Работы, Урожай, Техника.
 * Same business capability on desktop and mobile. No dead buttons.
 */

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button, Card, Input } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

function nd(v: unknown): string {
  if (v === null || v === undefined || v === "") return "нет данных";
  return String(v);
}

function FilterBar(props: {
  q: string;
  setQ: (v: string) => void;
  status?: string;
  setStatus?: (v: string) => void;
  statusOptions?: { id: string; label: string }[];
  extra?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap gap-2" data-testid="agro26-filters">
      <Input
        className="min-h-11 min-w-[10rem] flex-1"
        placeholder="Поиск…"
        value={props.q}
        onChange={(e) => props.setQ(e.target.value)}
        data-testid="agro26-search"
      />
      {props.setStatus && props.statusOptions ? (
        <select
          className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2"
          value={props.status || ""}
          onChange={(e) => props.setStatus?.(e.target.value)}
          data-testid="agro26-status-filter"
        >
          <option value="">Все статусы</option>
          {props.statusOptions.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
      ) : null}
      {props.extra}
    </div>
  );
}

export function AgroCropsCatalog26(props: { headers: Record<string, string>; canCreate: boolean }) {
  const mobile = useIsMobile();
  const [items, setItems] = useState<Row[]>([]);
  const [q, setQ] = useState("");
  const [panel, setPanel] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    const qs = q ? `?q=${encodeURIComponent(q)}` : "";
    const res = await agroOpsGet(`/agro-crops${qs}`, props.headers);
    setItems(((res.json as { items?: Row[] })?.items) || []);
  }, [props.headers, q]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    const res = await agroOpsPost("/agro-crops", {
      name: form.name,
      variety: form.variety,
      producer: form.producer,
      season: form.season,
      expected_yield: form.expected_yield ? Number(form.expected_yield) : null,
      moisture_target: form.moisture_target ? Number(form.moisture_target) : null,
      notes: form.notes,
    }, props.headers);
    setMsg(String((res.json as { message_ru?: string }).message_ru || (res.ok ? "Сохранено" : "Ошибка")));
    setPanel(false);
    await load();
  };

  const archive = async (id: string) => {
    await agroOpsPost(`/agro-crops/${id}`, { archive: true }, props.headers);
    await load();
  };

  return (
    <div className="grid gap-3" data-testid="agro-crops-26">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="font-semibold">Культуры</h2>
        {props.canCreate ? (
          <Button size="sm" className="min-h-11" onClick={() => setPanel(true)} data-testid="agro-crop-create">
            Создать культуру
          </Button>
        ) : null}
      </div>
      <FilterBar q={q} setQ={setQ} />
      {panel ? (
        <Card title="Новая культура">
          <div className={mobile ? "grid gap-2" : "grid grid-cols-2 gap-2"}>
            <Input className="min-h-11" placeholder="Название" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input className="min-h-11" placeholder="Сорт / гибрид" value={form.variety || ""} onChange={(e) => setForm({ ...form, variety: e.target.value })} />
            <Input className="min-h-11" placeholder="Производитель" value={form.producer || ""} onChange={(e) => setForm({ ...form, producer: e.target.value })} />
            <Input className="min-h-11" placeholder="Сезон" value={form.season || ""} onChange={(e) => setForm({ ...form, season: e.target.value })} />
            <Input className="min-h-11" placeholder="Ожидаемая урожайность" value={form.expected_yield || ""} onChange={(e) => setForm({ ...form, expected_yield: e.target.value })} />
            <Input className="min-h-11" placeholder="Целевая влажность" value={form.moisture_target || ""} onChange={(e) => setForm({ ...form, moisture_target: e.target.value })} />
          </div>
          <Input className="mt-2 min-h-11" placeholder="Заметки" value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <Button className="mt-2 min-h-11" onClick={() => void save()}>Сохранить</Button>
        </Card>
      ) : null}
      <div className="grid gap-2">
        {items.map((c) => (
          <Card key={pick(c, "id")} data-testid={`agro-crop-card-${pick(c, "id")}`}>
            <p className="font-semibold">{nd(c.name)}</p>
            <p className="eds-type-small">
              {nd(c.variety)} · {nd(c.season)} · {nd(c.producer)}
            </p>
            <p className="eds-type-caption">Ожид. урожайность: {nd(c.expected_yield)} · Факт: {nd(c.actual_yield)}</p>
            {props.canCreate ? (
              <Button size="sm" variant="ghost" className="mt-2 min-h-11" onClick={() => void archive(pick(c, "id"))}>
                Архивировать
              </Button>
            ) : null}
          </Card>
        ))}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}

export function AgroSowingsPage(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  onOpenField: (id: string) => void;
}) {
  const mobile = useIsMobile();
  const [items, setItems] = useState<Row[]>([]);
  const [fields, setFields] = useState<Row[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [panel, setPanel] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    const res = await agroOpsGet(`/sowings?${params}`, props.headers);
    setItems(((res.json as { items?: Row[] })?.items) || []);
  }, [props.headers, q, status]);

  useEffect(() => {
    void load();
    void agroOpsGet("/fields", props.headers).then((r) => setFields(((r.json as { items?: Row[] })?.items) || []));
  }, [load, props.headers]);

  const save = async () => {
    const res = await agroOpsPost("/sowings", {
      field_id: form.field_id,
      crop: form.crop,
      variety: form.variety,
      season: form.season || new Date().getFullYear(),
      sowing_date: form.sowing_date,
      area: form.area ? Number(form.area) : undefined,
      seed_rate: form.seed_rate ? Number(form.seed_rate) : undefined,
      seed_quantity: form.seed_quantity ? Number(form.seed_quantity) : undefined,
      seed_cost: form.seed_cost ? Number(form.seed_cost) : undefined,
      fuel_consumption: form.fuel_consumption ? Number(form.fuel_consumption) : undefined,
      fuel_cost: form.fuel_cost ? Number(form.fuel_cost) : undefined,
      fertilizer_cost: form.fertilizer_cost ? Number(form.fertilizer_cost) : undefined,
      ppp_cost: form.ppp_cost ? Number(form.ppp_cost) : undefined,
      other_costs: form.other_costs ? Number(form.other_costs) : undefined,
      machine_id: form.machine_id || undefined,
      operator: form.operator,
      responsible: form.responsible,
      notes: form.notes,
      status: form.status || "plan",
    }, props.headers);
    const j = res.json as { message_ru?: string; cost_per_hectare?: number; total_operation_cost?: number };
    setMsg(j.message_ru || (res.ok ? `Сохранено. Итого: ${nd(j.total_operation_cost)} · /га: ${nd(j.cost_per_hectare)}` : "Ошибка"));
    setPanel(false);
    await load();
  };

  return (
    <div className="grid gap-3" data-testid="agro-sowings-page">
      <div className="flex flex-wrap items-center gap-2 sticky top-0 z-10 bg-[var(--ew-bg,transparent)] py-2">
        <h2 className="font-semibold">Посевы</h2>
        {props.canCreate ? (
          <Button size="sm" className="ml-auto min-h-11" onClick={() => setPanel(true)} data-testid="agro-sowing-create">
            Создать посев
          </Button>
        ) : null}
      </div>
      <FilterBar
        q={q}
        setQ={setQ}
        status={status}
        setStatus={setStatus}
        statusOptions={[
          { id: "plan", label: "План" },
          { id: "prep", label: "Подготовка" },
          { id: "in_progress", label: "В работе" },
          { id: "done", label: "Завершён" },
          { id: "cancelled", label: "Отменён" },
        ]}
      />
      {panel ? (
        <Card title="Новый посев">
          <div className={mobile ? "grid gap-2" : "grid grid-cols-2 gap-2"}>
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.field_id || ""} onChange={(e) => setForm({ ...form, field_id: e.target.value })} data-testid="agro-sowing-field">
              <option value="">Поле</option>
              {fields.map((f) => (
                <option key={pick(f, "id")} value={pick(f, "id")}>{nd(f.name)}</option>
              ))}
            </select>
            <Input className="min-h-11" placeholder="Культура" value={form.crop || ""} onChange={(e) => setForm({ ...form, crop: e.target.value })} />
            <Input className="min-h-11" placeholder="Сорт / гибрид" value={form.variety || ""} onChange={(e) => setForm({ ...form, variety: e.target.value })} />
            <Input className="min-h-11" placeholder="Сезон / год" value={form.season || ""} onChange={(e) => setForm({ ...form, season: e.target.value })} />
            <Input className="min-h-11" type="date" value={form.sowing_date || ""} onChange={(e) => setForm({ ...form, sowing_date: e.target.value })} />
            <Input className="min-h-11" placeholder="Площадь, га" value={form.area || ""} onChange={(e) => setForm({ ...form, area: e.target.value })} />
            <Input className="min-h-11" placeholder="Норма высева" value={form.seed_rate || ""} onChange={(e) => setForm({ ...form, seed_rate: e.target.value })} />
            <Input className="min-h-11" placeholder="Кол-во семян" value={form.seed_quantity || ""} onChange={(e) => setForm({ ...form, seed_quantity: e.target.value })} />
            <Input className="min-h-11" placeholder="Стоимость семян" value={form.seed_cost || ""} onChange={(e) => setForm({ ...form, seed_cost: e.target.value })} />
            <Input className="min-h-11" placeholder="Расход топлива" value={form.fuel_consumption || ""} onChange={(e) => setForm({ ...form, fuel_consumption: e.target.value })} />
            <Input className="min-h-11" placeholder="Стоимость топлива" value={form.fuel_cost || ""} onChange={(e) => setForm({ ...form, fuel_cost: e.target.value })} />
            <Input className="min-h-11" placeholder="Удобрения, стоимость" value={form.fertilizer_cost || ""} onChange={(e) => setForm({ ...form, fertilizer_cost: e.target.value })} />
            <Input className="min-h-11" placeholder="СЗР, стоимость" value={form.ppp_cost || ""} onChange={(e) => setForm({ ...form, ppp_cost: e.target.value })} />
            <Input className="min-h-11" placeholder="Прочие затраты" value={form.other_costs || ""} onChange={(e) => setForm({ ...form, other_costs: e.target.value })} />
            <Input className="min-h-11" placeholder="Оператор" value={form.operator || ""} onChange={(e) => setForm({ ...form, operator: e.target.value })} />
            <Input className="min-h-11" placeholder="Ответственный" value={form.responsible || ""} onChange={(e) => setForm({ ...form, responsible: e.target.value })} />
          </div>
          <Button className="mt-2 min-h-11" onClick={() => void save()} data-testid="agro-sowing-save">Сохранить</Button>
        </Card>
      ) : null}
      <div className="grid gap-2">
        {items.map((s) => (
          <button
            key={pick(s, "id")}
            type="button"
            className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
            data-testid={`agro-sowing-card-${pick(s, "id")}`}
            onClick={() => s.field_id && props.onOpenField(String(s.field_id))}
          >
            <p className="font-semibold">{nd(s.title)}</p>
            <p className="eds-type-small">{nd(s.field_name)} · {nd(s.crop)} · {nd(s.status_ru)}</p>
            <p className="eds-type-caption">
              {nd(s.area_ha)} га · итого {nd(s.total_operation_cost)} · /га {nd(s.cost_per_hectare)}
            </p>
          </button>
        ))}
        {!items.length ? <p className="eds-type-small">Нет данных</p> : null}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}

export function AgroWorksPage(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  onOpenField: (id: string) => void;
}) {
  const mobile = useIsMobile();
  const [items, setItems] = useState<Row[]>([]);
  const [fields, setFields] = useState<Row[]>([]);
  const [machines, setMachines] = useState<Row[]>([]);
  const [types, setTypes] = useState<{ id: string; label_ru: string }[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [panel, setPanel] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    const res = await agroOpsGet(`/works?${params}`, props.headers);
    const json = res.json as { items?: Row[]; work_types?: { id: string; label_ru: string }[] };
    setItems(json.items || []);
    if (json.work_types) setTypes(json.work_types);
  }, [props.headers, q, status]);

  useEffect(() => {
    void load();
    void agroOpsGet("/fields", props.headers).then((r) => setFields(((r.json as { items?: Row[] })?.items) || []));
    void agroOpsGet("/machines", props.headers).then((r) => setMachines(((r.json as { items?: Row[] })?.items) || []));
  }, [load, props.headers]);

  const save = async () => {
    const res = await agroOpsPost("/works", {
      field_id: form.field_id,
      operation: form.operation,
      planned_date: form.planned_date,
      actual_date: form.actual_date || undefined,
      machine_id: form.machine_id || undefined,
      operator: form.operator,
      materials: form.materials,
      fuel: form.fuel ? Number(form.fuel) : undefined,
      cost: form.cost ? Number(form.cost) : undefined,
      comment: form.comment,
      responsible: form.responsible,
    }, props.headers);
    setMsg(String((res.json as { message_ru?: string }).message_ru || (res.ok ? "Сохранено" : "Ошибка")));
    setPanel(false);
    await load();
  };

  const setStatusWork = async (id: string, next: string) => {
    await agroOpsPost(`/fields/works/${id}/status`, { status: next }, props.headers);
    await load();
  };

  return (
    <div className="grid gap-3" data-testid="agro-works-page">
      <div className="flex flex-wrap items-center gap-2 sticky top-0 z-10 bg-[var(--ew-bg,transparent)] py-2">
        <h2 className="font-semibold">Работы</h2>
        {props.canCreate ? (
          <Button size="sm" className="ml-auto min-h-11" onClick={() => setPanel(true)} data-testid="agro-work-create">
            Создать работу
          </Button>
        ) : null}
      </div>
      <FilterBar
        q={q}
        setQ={setQ}
        status={status}
        setStatus={setStatus}
        statusOptions={[
          { id: "planned", label: "Запланировано" },
          { id: "in_progress", label: "В работе" },
          { id: "done", label: "Выполнено" },
          { id: "overdue", label: "Просрочено" },
          { id: "cancelled", label: "Отменено" },
        ]}
      />
      {panel ? (
        <Card title="Наряд на работу">
          <div className={mobile ? "grid gap-2" : "grid grid-cols-2 gap-2"}>
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.field_id || ""} onChange={(e) => setForm({ ...form, field_id: e.target.value })}>
              <option value="">Поле</option>
              {fields.map((f) => (
                <option key={pick(f, "id")} value={pick(f, "id")}>{nd(f.name)}</option>
              ))}
            </select>
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.operation || ""} onChange={(e) => setForm({ ...form, operation: e.target.value })} data-testid="agro-work-operation">
              <option value="">Операция</option>
              {(types.length ? types : [
                { id: "tillage", label_ru: "Подготовка почвы" },
                { id: "sowing", label_ru: "Посев" },
                { id: "fertilizer", label_ru: "Внесение удобрений" },
                { id: "spraying", label_ru: "Опрыскивание" },
                { id: "irrigation", label_ru: "Полив" },
                { id: "harvest", label_ru: "Уборка" },
                { id: "transport", label_ru: "Перевозка" },
              ]).map((t) => (
                <option key={t.id} value={t.id}>{t.label_ru}</option>
              ))}
            </select>
            <Input className="min-h-11" type="date" value={form.planned_date || ""} onChange={(e) => setForm({ ...form, planned_date: e.target.value })} />
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.machine_id || ""} onChange={(e) => setForm({ ...form, machine_id: e.target.value })}>
              <option value="">Техника</option>
              {machines.map((m) => (
                <option key={pick(m, "id")} value={pick(m, "id")}>{nd(m.name)}</option>
              ))}
            </select>
            <Input className="min-h-11" placeholder="Оператор" value={form.operator || ""} onChange={(e) => setForm({ ...form, operator: e.target.value })} />
            <Input className="min-h-11" placeholder="Материалы" value={form.materials || ""} onChange={(e) => setForm({ ...form, materials: e.target.value })} />
            <Input className="min-h-11" placeholder="Топливо" value={form.fuel || ""} onChange={(e) => setForm({ ...form, fuel: e.target.value })} />
            <Input className="min-h-11" placeholder="Стоимость" value={form.cost || ""} onChange={(e) => setForm({ ...form, cost: e.target.value })} />
          </div>
          <Input className="mt-2 min-h-11" placeholder="Комментарий" value={form.comment || ""} onChange={(e) => setForm({ ...form, comment: e.target.value })} />
          <Button className="mt-2 min-h-11" onClick={() => void save()} data-testid="agro-work-save">Сохранить</Button>
        </Card>
      ) : null}
      <div className="grid gap-2">
        {items.map((w) => (
          <Card key={pick(w, "id")} data-testid={`agro-work-card-${pick(w, "id")}`}>
            <button type="button" className="w-full text-left min-h-11" onClick={() => w.field_id && props.onOpenField(String(w.field_id))}>
              <p className="font-semibold">{nd(w.title)}</p>
              <p className="eds-type-small">{nd(w.field_name)} · {nd(w.operation_ru)} · {nd(w.status_ru)}</p>
              <p className="eds-type-caption">{nd(w.machine_name)} · {nd(w.operator)} · {nd(w.cost)}</p>
            </button>
            {props.canCreate && String(w.status) === "planned" ? (
              <Button size="sm" className="mt-2 min-h-11" onClick={() => void setStatusWork(pick(w, "id"), "in_progress")}>В работу</Button>
            ) : null}
            {props.canCreate && String(w.status) === "in_progress" ? (
              <Button size="sm" className="mt-2 min-h-11" onClick={() => void setStatusWork(pick(w, "id"), "done")}>Завершить</Button>
            ) : null}
          </Card>
        ))}
        {!items.length ? <p className="eds-type-small">Нет данных</p> : null}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}

export function AgroHarvestPage(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  onOpenField: (id: string) => void;
}) {
  const mobile = useIsMobile();
  const [items, setItems] = useState<Row[]>([]);
  const [fields, setFields] = useState<Row[]>([]);
  const [warehouses, setWarehouses] = useState<Row[]>([]);
  const [q, setQ] = useState("");
  const [panel, setPanel] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    const params = q ? `?q=${encodeURIComponent(q)}` : "";
    const res = await agroOpsGet(`/harvests${params}`, props.headers);
    setItems(((res.json as { items?: Row[] })?.items) || []);
  }, [props.headers, q]);

  useEffect(() => {
    void load();
    void agroOpsGet("/fields", props.headers).then((r) => setFields(((r.json as { items?: Row[] })?.items) || []));
    void agroOpsGet("/entities/warehouse", props.headers).then((r) => setWarehouses(((r.json as { items?: Row[] })?.items) || [])).catch(() => undefined);
  }, [load, props.headers]);

  const save = async () => {
    const res = await agroOpsPost("/harvests", {
      field_id: form.field_id,
      crop: form.crop,
      area_ha: form.area ? Number(form.area) : undefined,
      date: form.date,
      gross_weight: form.gross ? Number(form.gross) : undefined,
      net_weight: form.net ? Number(form.net) : undefined,
      actual_tonnes: form.net ? Number(form.net) : form.tonnes ? Number(form.tonnes) : undefined,
      moisture: form.moisture ? Number(form.moisture) : undefined,
      impurity: form.impurity ? Number(form.impurity) : undefined,
      quality: form.quality,
      warehouse_destination: form.warehouse_id || undefined,
      to_warehouse: Boolean(form.warehouse_id),
      transport: form.transport,
      responsible: form.responsible,
      price_per_t: form.price ? Number(form.price) : undefined,
      operational_cost: form.cost ? Number(form.cost) : undefined,
    }, props.headers);
    const j = res.json as { message_ru?: string; yield_t_ha?: number; estimated_value?: number; warehouse?: { ok?: boolean } };
    setMsg(
      j.message_ru
        || (res.ok
          ? `Сохранено. Урож-ть ${nd(j.yield_t_ha)} т/га · оценка ${nd(j.estimated_value)}${j.warehouse?.ok ? " · на склад" : ""}`
          : "Ошибка"),
    );
    setPanel(false);
    await load();
  };

  const toWh = async (id: string, warehouseId?: string) => {
    const res = await agroOpsPost("/harvest/to-warehouse", { harvest_id: id, warehouse_id: warehouseId }, props.headers);
    setMsg(String((res.json as { message_ru?: string }).message_ru || (res.ok ? "Оприходовано на склад" : "Ошибка")));
    await load();
  };

  return (
    <div className="grid gap-3" data-testid="agro-harvest-page">
      <div className="flex flex-wrap items-center gap-2 sticky top-0 z-10 bg-[var(--ew-bg,transparent)] py-2">
        <h2 className="font-semibold">Урожай</h2>
        {props.canCreate ? (
          <Button size="sm" className="ml-auto min-h-11" onClick={() => setPanel(true)} data-testid="agro-harvest-create">
            Добавить урожай
          </Button>
        ) : null}
      </div>
      <FilterBar q={q} setQ={setQ} />
      {panel ? (
        <Card title="Уборка">
          <div className={mobile ? "grid gap-2" : "grid grid-cols-2 gap-2"}>
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.field_id || ""} onChange={(e) => setForm({ ...form, field_id: e.target.value })}>
              <option value="">Поле</option>
              {fields.map((f) => (
                <option key={pick(f, "id")} value={pick(f, "id")}>{nd(f.name)}</option>
              ))}
            </select>
            <Input className="min-h-11" placeholder="Культура" value={form.crop || ""} onChange={(e) => setForm({ ...form, crop: e.target.value })} />
            <Input className="min-h-11" type="date" value={form.date || ""} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            <Input className="min-h-11" placeholder="Площадь, га" value={form.area || ""} onChange={(e) => setForm({ ...form, area: e.target.value })} />
            <Input className="min-h-11" placeholder="Брутто, т" value={form.gross || ""} onChange={(e) => setForm({ ...form, gross: e.target.value })} />
            <Input className="min-h-11" placeholder="Нетто, т" value={form.net || ""} onChange={(e) => setForm({ ...form, net: e.target.value })} />
            <Input className="min-h-11" placeholder="Влажность %" value={form.moisture || ""} onChange={(e) => setForm({ ...form, moisture: e.target.value })} />
            <Input className="min-h-11" placeholder="Сорность %" value={form.impurity || ""} onChange={(e) => setForm({ ...form, impurity: e.target.value })} />
            <Input className="min-h-11" placeholder="Качество" value={form.quality || ""} onChange={(e) => setForm({ ...form, quality: e.target.value })} />
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.warehouse_id || ""} onChange={(e) => setForm({ ...form, warehouse_id: e.target.value })}>
              <option value="">Склад (опционально)</option>
              {warehouses.map((w) => (
                <option key={pick(w, "id")} value={pick(w, "id")}>{nd(w.name || w.title)}</option>
              ))}
            </select>
            <Input className="min-h-11" placeholder="Транспорт" value={form.transport || ""} onChange={(e) => setForm({ ...form, transport: e.target.value })} />
            <Input className="min-h-11" placeholder="Ответственный" value={form.responsible || ""} onChange={(e) => setForm({ ...form, responsible: e.target.value })} />
            <Input className="min-h-11" placeholder="Цена за т" value={form.price || ""} onChange={(e) => setForm({ ...form, price: e.target.value })} />
            <Input className="min-h-11" placeholder="Опер. затраты" value={form.cost || ""} onChange={(e) => setForm({ ...form, cost: e.target.value })} />
          </div>
          <Button className="mt-2 min-h-11" onClick={() => void save()} data-testid="agro-harvest-save">Сохранить</Button>
        </Card>
      ) : null}
      <div className="grid gap-2">
        {items.map((h) => (
          <Card key={pick(h, "id")} data-testid={`agro-harvest-card-${pick(h, "id")}`}>
            <button type="button" className="w-full text-left min-h-11" onClick={() => h.field_id && props.onOpenField(String(h.field_id))}>
              <p className="font-semibold">{nd(h.title)}</p>
              <p className="eds-type-small">{nd(h.field_name)} · {nd(h.crop)} · {nd(h.actual_tonnes)} т · {nd(h.yield_t_ha)} т/га</p>
              <p className="eds-type-caption">
                Склад: {h.linked_warehouse ? "связан" : "нет"} · оценка {nd(h.estimated_value)}
              </p>
            </button>
            {props.canCreate && !h.linked_warehouse ? (
              <Button size="sm" className="mt-2 min-h-11" onClick={() => void toWh(pick(h, "id"), h.warehouse_id ? String(h.warehouse_id) : undefined)} data-testid={`agro-harvest-towh-${pick(h, "id")}`}>
                На склад (2.2)
              </Button>
            ) : null}
          </Card>
        ))}
        {!items.length ? <p className="eds-type-small">Нет данных</p> : null}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}

export function AgroMachinery26Page(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  machineId?: string | null;
  onOpen: (id: string) => void;
  onBack: () => void;
}) {
  const mobile = useIsMobile();
  const [items, setItems] = useState<Row[]>([]);
  const [card, setCard] = useState<Row | null>(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [panel, setPanel] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [types, setTypes] = useState<{ id: string; label_ru: string }[]>([]);
  const [statuses, setStatuses] = useState<{ id: string; label_ru: string }[]>([]);
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status", status);
    const res = await agroOpsGet(`/machines?${params}`, props.headers);
    const json = res.json as { items?: Row[]; types?: { id: string; label_ru: string }[]; statuses?: { id: string; label_ru: string }[] };
    setItems(json.items || []);
    if (json.types) setTypes(json.types);
    if (json.statuses) setStatuses(json.statuses);
  }, [props.headers, q, status]);

  const load360 = useCallback(async (id: string) => {
    const res = await agroOpsGet(`/machines/${id}`, props.headers);
    setCard((res.json || {}) as Row);
  }, [props.headers]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (props.machineId) void load360(props.machineId);
  }, [props.machineId, load360]);

  const save = async () => {
    const res = await agroOpsPost("/machines", {
      name: form.name,
      type: form.type || "tractor",
      brand: form.brand,
      model: form.model,
      plate: form.plate,
      vin: form.vin,
      year: form.year,
      owner: form.owner,
      responsible: form.responsible,
      status: form.status || "idle",
      engine_hours: form.hours ? Number(form.hours) : undefined,
      fuel_consumption: form.fuel ? Number(form.fuel) : undefined,
      last_service: form.last_service || undefined,
      next_service: form.next_service || undefined,
      notes: form.notes,
    }, props.headers);
    setMsg(String((res.json as { message_ru?: string }).message_ru || (res.ok ? "Сохранено" : "Ошибка")));
    setPanel(false);
    await load();
  };

  const item = (card?.item || {}) as Row;
  if (props.machineId && item.id) {
    return (
      <div className="grid gap-3" data-testid="agro-machine-360">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" className="min-h-11" onClick={props.onBack}>Назад</Button>
          <h2 className="font-semibold">{nd(item.name)}</h2>
        </div>
        <p className="eds-type-small">{nd(item.type_ru)} · {nd(item.status_ru)} · {nd(item.plate)}</p>
        <Card>
          <p>Марка / модель: {nd(item.brand)} {nd(item.model)}</p>
          <p>VIN: {nd(item.vin)} · Год: {nd(item.year)}</p>
          <p>Моточасы: {nd(item.engine_hours)} · Расход: {nd(item.fuel_consumption)}</p>
          <p>ТО: {nd(item.last_service)} → {nd(item.next_service)}</p>
          <p>Ответственный: {nd(item.responsible)}</p>
          <p>Заметки: {nd(item.notes)}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid gap-3" data-testid="agro-machinery-26">
      <div className="flex flex-wrap items-center gap-2 sticky top-0 z-10 bg-[var(--ew-bg,transparent)] py-2">
        <h2 className="font-semibold">Техника</h2>
        {props.canCreate ? (
          <Button size="sm" className="ml-auto min-h-11" onClick={() => setPanel(true)} data-testid="agro-machine-create">
            Добавить технику
          </Button>
        ) : null}
      </div>
      <FilterBar
        q={q}
        setQ={setQ}
        status={status}
        setStatus={setStatus}
        statusOptions={(statuses.length ? statuses : [
          { id: "working", label_ru: "Работает" },
          { id: "idle", label_ru: "Свободна" },
          { id: "on_field", label_ru: "На поле" },
          { id: "repair", label_ru: "В ремонте" },
          { id: "service", label_ru: "ТО" },
          { id: "inactive", label_ru: "Неактивна" },
        ]).map((s) => ({ id: s.id, label: s.label_ru }))}
      />
      {panel ? (
        <Card title="Новая техника">
          <div className={mobile ? "grid gap-2" : "grid grid-cols-2 gap-2"}>
            <Input className="min-h-11" placeholder="Название" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.type || "tractor"} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {(types.length ? types : [
                { id: "tractor", label_ru: "Трактор" },
                { id: "combine", label_ru: "Комбайн" },
                { id: "seeder", label_ru: "Сеялка" },
                { id: "sprayer", label_ru: "Опрыскиватель" },
                { id: "truck", label_ru: "Грузовик" },
                { id: "trailer", label_ru: "Прицеп" },
                { id: "other", label_ru: "Другая техника" },
              ]).map((t) => (
                <option key={t.id} value={t.id}>{t.label_ru}</option>
              ))}
            </select>
            <Input className="min-h-11" placeholder="Марка" value={form.brand || ""} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
            <Input className="min-h-11" placeholder="Модель" value={form.model || ""} onChange={(e) => setForm({ ...form, model: e.target.value })} />
            <Input className="min-h-11" placeholder="Госномер" value={form.plate || ""} onChange={(e) => setForm({ ...form, plate: e.target.value })} />
            <Input className="min-h-11" placeholder="VIN / serial" value={form.vin || ""} onChange={(e) => setForm({ ...form, vin: e.target.value })} />
            <Input className="min-h-11" placeholder="Год" value={form.year || ""} onChange={(e) => setForm({ ...form, year: e.target.value })} />
            <Input className="min-h-11" placeholder="Владелец" value={form.owner || ""} onChange={(e) => setForm({ ...form, owner: e.target.value })} />
            <Input className="min-h-11" placeholder="Ответственный" value={form.responsible || ""} onChange={(e) => setForm({ ...form, responsible: e.target.value })} />
            <Input className="min-h-11" placeholder="Моточасы" value={form.hours || ""} onChange={(e) => setForm({ ...form, hours: e.target.value })} />
            <Input className="min-h-11" type="date" placeholder="Последнее ТО" value={form.last_service || ""} onChange={(e) => setForm({ ...form, last_service: e.target.value })} />
            <Input className="min-h-11" type="date" placeholder="Следующее ТО" value={form.next_service || ""} onChange={(e) => setForm({ ...form, next_service: e.target.value })} />
          </div>
          <Button className="mt-2 min-h-11" onClick={() => void save()}>Сохранить</Button>
        </Card>
      ) : null}
      <div className="grid gap-2">
        {items.map((m) => (
          <button
            key={pick(m, "id")}
            type="button"
            className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
            data-testid={`agro-machine-card-${pick(m, "id")}`}
            onClick={() => props.onOpen(pick(m, "id"))}
          >
            <p className="font-semibold">{nd(m.name)}</p>
            <p className="eds-type-small">{nd(m.type_ru)} · {nd(m.status_ru)} · {nd(m.plate)}</p>
            {m.needs_service ? <p className="eds-type-caption text-amber-700">Требует ТО</p> : null}
          </button>
        ))}
        {!items.length ? <p className="eds-type-small">Нет данных</p> : null}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
