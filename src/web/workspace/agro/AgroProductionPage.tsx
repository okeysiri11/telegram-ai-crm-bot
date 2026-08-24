/**
 * AGRO 2.3 — land bank, field map, Field 360, machinery.
 * Real numbers only. Missing → «нет данных». Touch: tap / zoom / pan / close / back.
 */

import { useCallback, useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { agroOpsGet, agroOpsPost, agroOpsUpload, pick } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

const LAYERS = [
  { id: "crop", label: "Культура" },
  { id: "status", label: "Статус поля" },
  { id: "work", label: "Работы" },
  { id: "weather", label: "Погодный риск" },
  { id: "yield", label: "Урожайность" },
  { id: "cost", label: "Себестоимость" },
];

const QUICK = [
  { id: "work", label: "Создать работу" },
  { id: "expense", label: "Добавить расход" },
  { id: "material", label: "Добавить материал" },
  { id: "photo", label: "Добавить фото" },
  { id: "issue", label: "Добавить проблему" },
  { id: "harvest", label: "Добавить урожай" },
  { id: "task", label: "Создать задачу" },
];

function nd(v: unknown): string {
  if (v === null || v === undefined || v === "") return "нет данных";
  return String(v);
}

function polyPoints(poly: unknown): string {
  const pts = Array.isArray(poly) ? poly : [];
  return pts.map((p) => (Array.isArray(p) ? `${p[0]},${p[1]}` : "")).join(" ");
}

export function AgroProductionPage(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  canFinance: boolean;
  fieldId?: string | null;
  tab?: string;
  onOpen: (id: string) => void;
  onBack: () => void;
  onGo: (view: string, extra?: Record<string, string>) => void;
}) {
  const mobile = useIsMobile();
  const [list, setList] = useState<Row[]>([]);
  const [land, setLand] = useState<number | null>(null);
  const [map, setMap] = useState<{ features?: Row[]; legend?: { id: string; label_ru: string; color: string }[]; layer?: string; map_provider?: { label_ru?: string } }>({});
  const [layer, setLayer] = useState("crop");
  const [selected, setSelected] = useState<string | null>(props.fieldId || null);
  const [card, setCard] = useState<Row | null>(null);
  const [msg, setMsg] = useState("");
  const [quick, setQuick] = useState(false);
  const [panel, setPanel] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [workId, setWorkId] = useState<string>("");
  const [tab, setTab] = useState(props.tab || "overview");
  const [pan, setPan] = useState({ x: 0, y: 0, z: 1 });
  const [infoOpen, setInfoOpen] = useState(false);

  const loadList = useCallback(async () => {
    const res = await agroOpsGet("/fields", props.headers);
    const json = res.json as { items?: Row[]; land_bank_ha?: number };
    setList(json.items || []);
    setLand(json.land_bank_ha ?? null);
  }, [props.headers]);

  const loadMap = useCallback(async () => {
    const res = await agroOpsGet(`/fields/map?layer=${encodeURIComponent(layer)}`, props.headers);
    setMap((res.json || {}) as typeof map);
  }, [props.headers, layer]);

  const load360 = useCallback(async (id: string) => {
    const res = await agroOpsGet(`/fields/${id}?tab=${encodeURIComponent(tab)}`, props.headers);
    setCard((res.json || {}) as Row);
  }, [props.headers, tab]);

  useEffect(() => {
    void loadList();
    void loadMap();
  }, [loadList, loadMap]);

  useEffect(() => {
    if (props.fieldId) {
      setSelected(props.fieldId);
      void load360(props.fieldId);
    }
  }, [props.fieldId, load360]);

  const item = (card?.item || {}) as Row;
  const metrics = item;

  async function post(path: string, body: Record<string, unknown>) {
    const res = await agroOpsPost(path, body, props.headers);
    setMsg(String((res.json as { message_ru?: string }).message_ru || (res.ok ? "Сохранено" : "Ошибка")));
    await loadList();
    await loadMap();
    if (selected) await load360(selected);
    return res;
  }

  const createField = async () => {
    const res = await post("/fields", {
      name: form.name || "Поле",
      number: form.number,
      area_ha: Number(form.area),
      cadastre: form.cadastre,
      region: form.region,
      district: form.district,
      locality: form.locality,
      lat: form.lat ? Number(form.lat) : undefined,
      lng: form.lng ? Number(form.lng) : undefined,
      owner: form.owner,
      ownership_type: form.ownership_type || "owned",
      lease_start: form.lease_start || undefined,
      lease_until: form.lease_until || undefined,
      lease_cost: form.lease_cost ? Number(form.lease_cost) : undefined,
      responsible: form.responsible,
      previous_crop: form.previous_crop,
      notes: form.notes,
    });
    const id = pick((res.json as { item?: Row }).item || {}, "id");
    if (id) props.onOpen(id);
    setPanel(null);
  };

  const econ = (card?.economics || item.economics || {}) as Row;

  if (selected && item.id) {
    const tabs = [
      { id: "overview", label: "Обзор" },
      { id: "works", label: "Работы" },
      { id: "materials", label: "Материалы" },
      { id: "harvests", label: "Урожай" },
      { id: "costs", label: "Затраты" },
      { id: "issues", label: "Проблемы" },
      { id: "documents", label: "Документы" },
    ];
    return (
      <div className="grid gap-3 min-w-0 overflow-x-hidden" data-testid="agro-field-360">
        <div className="flex flex-wrap items-center gap-2 sticky top-0 z-10 bg-[var(--ew-bg,transparent)] py-1">
          <Button size="sm" variant="ghost" className="min-h-11" onClick={props.onBack} data-testid="agro-field-back">
            Назад
          </Button>
          <h2 className="font-semibold">{nd(item.name)}</h2>
          {props.canCreate ? (
            <Button size="sm" className="ml-auto min-h-11" onClick={() => setQuick(true)} data-testid="agro-field-quick">
              +
            </Button>
          ) : null}
        </div>
        <p className="eds-type-small">
          {nd(item.number)} · {nd(item.area_ha)} га · {nd(item.current_crop || item.crop)} · {nd(item.status_ru)}
        </p>
        <p className="eds-type-caption">
          {nd(item.region)} / {nd(item.district)} / {nd(item.locality)} · {nd(item.ownership_ru)} · отв. {nd(item.responsible)}
        </p>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("sowing")} data-testid="agro-field-to-sowing">
            Перейти к посеву
          </Button>
          <Button size="sm" className="min-h-11" variant="ghost" onClick={() => props.onGo("harvest")} data-testid="agro-field-to-harvest">
            Перейти к урожаю
          </Button>
          {props.canCreate ? (
            <Button size="sm" className="min-h-11" variant="ghost" onClick={() => setPanel("work")} data-testid="agro-field-add-op">
              Добавить операцию
            </Button>
          ) : null}
          {props.canCreate ? (
            <Button
              size="sm"
              className="min-h-11"
              variant="ghost"
              data-testid="agro-field-archive"
              onClick={() => void post(`/fields/${selected}/archive`, {})}
            >
              Архивировать
            </Button>
          ) : null}
        </div>
        {props.canFinance || econ.can_finance ? (
          <Card title="Экономика поля" data-testid="agro-field-economics">
            <div className={mobile ? "grid grid-cols-2 gap-2" : "grid grid-cols-3 gap-2"}>
              {[
                ["Затраты всего", econ.total_costs],
                ["Семена", econ.seed_costs],
                ["Удобрения", econ.fertilizer_costs],
                ["СЗР", econ.plant_protection],
                ["Топливо", econ.fuel],
                ["Техника", econ.machinery],
                ["Труд", econ.labor],
                ["Логистика", econ.logistics],
                ["Прочее", econ.other_costs],
                ["Урожай, т", econ.harvest_quantity],
                ["Урож-ть т/га", econ.yield_t_ha],
                ["Оценка выручки", econ.estimated_revenue],
                ["Факт выручки", econ.actual_revenue],
                ["Маржа", econ.gross_margin],
                ["П/У", econ.profit_loss],
              ].map(([l, v]) => (
                <div key={String(l)}>
                  <p className="eds-type-caption">{l}</p>
                  <p className="font-semibold">{nd(v)}</p>
                </div>
              ))}
            </div>
          </Card>
        ) : null}
        <div className={mobile ? "grid grid-cols-2 gap-2" : "grid grid-cols-4 gap-2"}>
          {[
            ["Урожайность", metrics.yield_t_ha, "т/га"],
            ["Себестоимость/га", metrics.cost_ha, "UAH"],
            ["Себестоимость/т", metrics.cost_t, "UAH"],
            ["Норма семян", metrics.seed_rate_kg_ha, "кг/га"],
          ].map(([l, v, u]) => (
            <Card key={String(l)}>
              <p className="eds-type-caption">{l}</p>
              <p className="font-semibold">{v == null ? "нет данных" : `${v} ${u}`}</p>
            </Card>
          ))}
        </div>
        <Card title="План / факт">
          {Object.entries((card?.plan_vs_actual || {}) as Record<string, Row>).map(([k, row]) => (
            <p key={k} className="eds-type-small">
              {k}: план {nd(row.plan)} · факт {nd(row.actual)} · Δ {nd(row.difference)}
            </p>
          ))}
        </Card>
        <div className="flex flex-wrap gap-1" data-testid="agro-field-tabs">
          {tabs.map((t) => (
            <Button key={t.id} size="sm" variant={tab === t.id ? "primary" : "ghost"} className="min-h-11" onClick={() => setTab(t.id)}>
              {t.label}
            </Button>
          ))}
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => props.onGo("weather")} data-testid="agro-field-weather">
            Погода
          </Button>
        </div>
        {tab === "works" ? (
          <div data-testid="agro-field-work">
            {((card?.items || []) as Row[]).map((w) => (
              <div key={pick(w, "id")} className="mb-2 rounded border border-[var(--ew-border)] p-2">
                <p>{nd(w.title)} · {nd(w.status)}</p>
                {props.canCreate && String(w.status) === "planned" ? (
                  <Button size="sm" className="min-h-11" data-testid="agro-work-start" onClick={() => { setWorkId(pick(w, "id")); void post(`/fields/works/${pick(w, "id")}/status`, { status: "in_progress" }); }}>
                    В работу
                  </Button>
                ) : null}
                {props.canCreate && String(w.status) === "in_progress" ? (
                  <Button size="sm" className="min-h-11" data-testid="agro-work-finish" onClick={() => void post(`/fields/works/${pick(w, "id")}/status`, { status: "done", hours: Number(form.hours) || undefined, actual_qty: Number(form.qty) || undefined })}>
                    Завершить
                  </Button>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
        {tab === "overview" ? (
          <Card>
            <p className="eds-type-small">Код: {nd(item.number)}</p>
            <p className="eds-type-small">Кадастр: {nd(item.cadastre)}</p>
            <p className="eds-type-small">Регион / район / НП: {nd(item.region)} / {nd(item.district)} / {nd(item.locality)}</p>
            <p className="eds-type-small">Координаты: {nd(item.lat)}, {nd(item.lng)}</p>
            <p className="eds-type-small">Собственник: {nd(item.owner)} · {nd(item.ownership_ru)}</p>
            <p className="eds-type-small">Аренда: {nd(item.lease_start)} — {nd(item.lease_until)} · {nd(item.lease_cost)}</p>
            <p className="eds-type-small">Культура тек./пред.: {nd(item.current_crop || item.crop)} / {nd(item.previous_crop)}</p>
            <p className="eds-type-small">Заметки: {nd(item.notes)}</p>
            <p className="eds-type-small">Погода: {nd((item.weather as Row | undefined)?.label_ru)}</p>
            <p className="eds-type-small">Карта: {nd((card?.map_provider as Row | undefined)?.label_ru)}</p>
            <p className="eds-type-small">Прослеживаемость: {((card?.trace_forward as Row[]) || []).map((s) => s.label).join(" → ") || "нет данных"}</p>
          </Card>
        ) : null}
        {tab === "harvests" ? (
          <div data-testid="agro-field-harvests">
            {((card?.items || []) as Row[]).map((r) => (
              <div key={pick(r, "id")} className="mb-2 rounded border border-[var(--ew-border)] p-2">
                <p className="eds-type-small">{nd(r.title)} · {nd(r.actual_tonnes)} т</p>
                {props.canCreate && !r.lot_id ? (
                  <Button size="sm" className="min-h-11" onClick={() => void post("/harvest/to-warehouse", { harvest_id: pick(r, "id") })}>
                    На склад (2.2)
                  </Button>
                ) : null}
              </div>
            ))}
            {!(card?.items as Row[] | undefined)?.length ? <p className="eds-type-small">нет данных</p> : null}
          </div>
        ) : null}
        {tab !== "overview" && tab !== "works" && tab !== "harvests" ? (
          <ul>
            {((card?.items || []) as Row[]).map((r) => (
              <li key={pick(r, "id")} className="eds-type-small">{nd(r.title || r.name)} · {nd(r.quantity || r.amount || r.actual_tonnes)}</li>
            ))}
            {!(card?.items as Row[] | undefined)?.length ? <li className="eds-type-small">нет данных</li> : null}
          </ul>
        ) : null}
        {quick ? (
          <div className="rounded-lg border border-[var(--ew-border)] p-3" data-testid="agro-field-quick-menu">
            {QUICK.map((a) => (
              <Button key={a.id} size="sm" variant="ghost" className="min-h-11 w-full justify-start" onClick={() => { setPanel(a.id); setQuick(false); }}>
                {a.label}
              </Button>
            ))}
            <Button size="sm" variant="ghost" onClick={() => setQuick(false)}>Закрыть</Button>
          </div>
        ) : null}
        {panel === "work" ? (
          <Card title="Создать работу">
            <Input placeholder="Тип: sowing / spraying / fertilizer / harvest" value={form.work_type || ""} onChange={(e) => setForm({ ...form, work_type: e.target.value })} />
            <Input type="datetime-local" value={form.planned_at || ""} onChange={(e) => setForm({ ...form, planned_at: e.target.value })} />
            <Button className="mt-2 min-h-11" onClick={() => void post(`/fields/${selected}/work`, { work_type: form.work_type || "sowing", planned_at: form.planned_at, machine_id: form.machine_id, implement_id: form.implement_id })}>Сохранить</Button>
          </Card>
        ) : null}
        {panel === "material" ? (
          <Card title="Добавить материал">
            <Input placeholder="material_id" value={form.material_id || ""} onChange={(e) => setForm({ ...form, material_id: e.target.value })} />
            <Input placeholder="Количество" value={form.qty || ""} onChange={(e) => setForm({ ...form, qty: e.target.value })} />
            <Button className="mt-2 min-h-11" data-testid="agro-add-material" onClick={() => void post("/materials/issue", { material_id: form.material_id, quantity: Number(form.qty), field_id: selected, work_id: workId, unit_cost: form.unit_cost ? Number(form.unit_cost) : undefined })}>Выдать</Button>
          </Card>
        ) : null}
        {panel === "expense" && props.canFinance ? (
          <Card title="Расход">
            <Input placeholder="Сумма" value={form.amount || ""} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
            <Input placeholder="Категория fuel/seed/..." value={form.category || "fuel"} onChange={(e) => setForm({ ...form, category: e.target.value })} />
            <Button className="mt-2 min-h-11" data-testid="agro-add-fuel" onClick={() => void post("/fields/costs", { field_id: selected, amount: Number(form.amount), category: form.category || "fuel", source: "manual", source_id: workId || selected })}>Сохранить</Button>
          </Card>
        ) : null}
        {panel === "harvest" ? (
          <Card title="Урожай">
            <Input placeholder="Тонны" value={form.tonnes || ""} onChange={(e) => setForm({ ...form, tonnes: e.target.value })} />
            <Input placeholder="Площадь, га" value={form.area_h || ""} onChange={(e) => setForm({ ...form, area_h: e.target.value })} />
            <Button className="mt-2 min-h-11" data-testid="agro-add-harvest" onClick={() => void post(`/fields/${selected}/harvest`, { actual_tonnes: Number(form.tonnes), area_harvested: Number(form.area_h) || undefined })}>Сохранить</Button>
          </Card>
        ) : null}
        {panel === "issue" ? (
          <Card title="Проблема">
            <Input placeholder="Тип weeds/disease/..." value={form.issue_type || "other"} onChange={(e) => setForm({ ...form, issue_type: e.target.value })} />
            <Input placeholder="Описание" value={form.desc || ""} onChange={(e) => setForm({ ...form, desc: e.target.value })} />
            <Button className="mt-2 min-h-11" onClick={() => void post(`/fields/${selected}/issue`, { issue_type: form.issue_type, description: form.desc, create_task: true })}>Сохранить</Button>
          </Card>
        ) : null}
        {panel === "task" ? (
          <Card title="Задача">
            <Input placeholder="Название" value={form.task || ""} onChange={(e) => setForm({ ...form, task: e.target.value })} />
            <Button className="mt-2 min-h-11" onClick={() => void post("/tasks/from-entity", { title: form.task, entity_type: "agro_field", entity_id: selected, field_id: selected })}>Создать задачу</Button>
          </Card>
        ) : null}
        {panel === "photo" ? (
          <Card title="Фото">
            <input
              type="file"
              accept="image/*"
              capture="environment"
              data-testid="agro-add-photo"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file || !selected) return;
                await agroOpsUpload("/files", file, { entity_type: "agro_field", entity_id: selected, doc_type: "photo" }, props.headers);
                await load360(selected);
              }}
            />
          </Card>
        ) : null}
        {msg ? <p className="eds-type-small">{msg}</p> : null}
      </div>
    );
  }

  return (
    <div className="grid gap-3 min-w-0 overflow-x-hidden" data-testid="agro-fields-page">
      <div className="flex flex-wrap items-center gap-2 sticky top-0 z-10 bg-[var(--ew-bg,transparent)] py-2">
        <h2 className="font-semibold">Поля</h2>
        <p className="eds-type-small">{land == null ? "нет данных" : `${land} га`}</p>
        {props.canCreate ? (
          <Button size="sm" className="min-h-11" onClick={() => setPanel("field")} data-testid="agro-create-field">
            Создать поле
          </Button>
        ) : null}
        {props.canCreate ? (
          <Button size="sm" variant="ghost" className="min-h-11" data-testid="agro-production-demo" onClick={() => void post("/production/bootstrap", {})}>
            Загрузить демо AGRO Production
          </Button>
        ) : null}
      </div>
      {panel === "field" ? (
        <Card title="Новое поле">
          <div className={mobile ? "grid gap-2" : "grid grid-cols-2 gap-2"}>
            <Input className="min-h-11" placeholder="Название" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <Input className="min-h-11" placeholder="Код / номер" value={form.number || ""} onChange={(e) => setForm({ ...form, number: e.target.value })} />
            <Input className="min-h-11" placeholder="Площадь, га" value={form.area || ""} onChange={(e) => setForm({ ...form, area: e.target.value })} />
            <Input className="min-h-11" placeholder="Регион" value={form.region || ""} onChange={(e) => setForm({ ...form, region: e.target.value })} />
            <Input className="min-h-11" placeholder="Район" value={form.district || ""} onChange={(e) => setForm({ ...form, district: e.target.value })} />
            <Input className="min-h-11" placeholder="Населённый пункт" value={form.locality || ""} onChange={(e) => setForm({ ...form, locality: e.target.value })} />
            <Input className="min-h-11" placeholder="Широта" value={form.lat || ""} onChange={(e) => setForm({ ...form, lat: e.target.value })} />
            <Input className="min-h-11" placeholder="Долгота" value={form.lng || ""} onChange={(e) => setForm({ ...form, lng: e.target.value })} />
            <Input className="min-h-11" placeholder="Кадастр" value={form.cadastre || ""} onChange={(e) => setForm({ ...form, cadastre: e.target.value })} />
            <Input className="min-h-11" placeholder="Собственник" value={form.owner || ""} onChange={(e) => setForm({ ...form, owner: e.target.value })} />
            <select className="min-h-11 rounded-lg border border-[var(--ew-border)] bg-transparent px-2" value={form.ownership_type || "owned"} onChange={(e) => setForm({ ...form, ownership_type: e.target.value })}>
              <option value="owned">Собственность</option>
              <option value="lease">Аренда</option>
              <option value="sublease">Субаренда</option>
            </select>
            <Input className="min-h-11" type="date" value={form.lease_start || ""} onChange={(e) => setForm({ ...form, lease_start: e.target.value })} />
            <Input className="min-h-11" type="date" value={form.lease_until || ""} onChange={(e) => setForm({ ...form, lease_until: e.target.value })} />
            <Input className="min-h-11" placeholder="Стоимость аренды" value={form.lease_cost || ""} onChange={(e) => setForm({ ...form, lease_cost: e.target.value })} />
            <Input className="min-h-11" placeholder="Ответственный" value={form.responsible || ""} onChange={(e) => setForm({ ...form, responsible: e.target.value })} />
            <Input className="min-h-11" placeholder="Предыдущая культура" value={form.previous_crop || ""} onChange={(e) => setForm({ ...form, previous_crop: e.target.value })} />
          </div>
          <Input className="mt-2 min-h-11" placeholder="Заметки" value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          <Button className="mt-2 min-h-11" onClick={() => void createField()}>Сохранить</Button>
        </Card>
      ) : null}
      <div className="flex flex-wrap gap-1">
        {LAYERS.map((l) => (
          <Button key={l.id} size="sm" variant={layer === l.id ? "primary" : "ghost"} className="min-h-11" onClick={() => setLayer(l.id)}>
            {l.label}
          </Button>
        ))}
      </div>
      <div
        className="overflow-hidden rounded-lg border border-[var(--ew-border)]"
        data-testid="agro-field-map"
        onPointerDown={(e) => {
          const start = { x: e.clientX, y: e.clientY, px: pan.x, py: pan.y };
          const move = (ev: PointerEvent) => setPan((p) => ({ ...p, x: start.px + ev.clientX - start.x, y: start.py + ev.clientY - start.y }));
          const up = () => {
            window.removeEventListener("pointermove", move);
            window.removeEventListener("pointerup", up);
          };
          window.addEventListener("pointermove", move);
          window.addEventListener("pointerup", up);
        }}
        onWheel={(e) => {
          e.preventDefault();
          setPan((p) => ({ ...p, z: Math.min(4, Math.max(0.5, p.z + (e.deltaY > 0 ? -0.1 : 0.1))) }));
        }}
      >
        <svg viewBox="0 0 1000 600" className="h-64 w-full bg-[#0b1220]" style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${pan.z})` }}>
          {(map.features || []).map((f) => (
            <polygon
              key={pick(f, "id")}
              points={polyPoints(f.polygon)}
              fill={String(f.color || "#1a2740")}
              stroke="#e8eef7"
              strokeWidth={selected === pick(f, "id") ? 3 : 1}
              data-testid={`agro-field-poly-${pick(f, "id")}`}
              onClick={() => {
                setSelected(pick(f, "id"));
                setInfoOpen(true);
              }}
            />
          ))}
        </svg>
      </div>
      {infoOpen && selected ? (
        <Card data-testid="agro-map-compact-card">
          {(() => {
            const f = (map.features || []).find((x) => pick(x, "id") === selected);
            return (
              <>
                <p className="font-semibold">{nd(f?.name)}</p>
                <p className="eds-type-small">Площадь: {nd(f?.area_ha)} га</p>
                <p className="eds-type-small">Культура: {nd(f?.crop)}</p>
                <p className="eds-type-small">Статус: {nd(f?.status_ru || f?.status)}</p>
                <p className="eds-type-small">Текущие работы: {nd(f?.today_work)}</p>
                <p className="eds-type-small">Ответственный: {nd(f?.responsible)}</p>
                <p className="eds-type-caption">{nd((map as { map_provider?: { label_ru?: string } }).map_provider?.label_ru)}</p>
              </>
            );
          })()}
          <Button size="sm" className="min-h-11" onClick={() => props.onOpen(selected)}>Открыть Field 360</Button>
          <Button size="sm" variant="ghost" className="min-h-11" data-testid="agro-map-close" onClick={() => setInfoOpen(false)}>Закрыть</Button>
        </Card>
      ) : null}
      <div className="grid gap-1" data-testid="agro-map-legend">
        {(map.legend || []).map((l) => (
          <p key={l.id} className="eds-type-caption">
            <span className="mr-2 inline-block h-3 w-3 rounded" style={{ background: l.color }} />
            {l.label_ru}
          </p>
        ))}
      </div>
      <div className="grid gap-2" data-testid="agro-field-list">
        {list.map((f) => (
          <button
            key={pick(f, "id")}
            type="button"
            className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
            data-testid={`agro-field-card-${pick(f, "id")}`}
            onClick={() => props.onOpen(pick(f, "id"))}
          >
            <p className="font-semibold">{nd(f.name)}</p>
            <p className="eds-type-small">{nd(f.area_ha)} ha · {nd(f.crop)} · {nd(f.status_ru)}</p>
            <p className="eds-type-caption">Today: {nd(f.today_work)}</p>
            <p className="eds-type-caption">Risk: {nd(f.weather_risk)}</p>
          </button>
        ))}
        {!list.length ? <p className="eds-type-small">нет данных</p> : null}
      </div>
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}

export function AgroMachineryPage(props: { headers: Record<string, string>; canCreate: boolean }) {
  const [machines, setMachines] = useState<Row[]>([]);
  const [form, setForm] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState("");
  const load = useCallback(async () => {
    const res = await agroOpsGet("/entities/machine", props.headers);
    setMachines(((res.json as { items?: Row[] }).items) || []);
  }, [props.headers]);
  useEffect(() => { void load(); }, [load]);
  return (
    <div className="grid gap-3" data-testid="agro-machinery-page">
      <h2 className="font-semibold">Машины</h2>
      {props.canCreate ? (
        <Card title="Техника / агрегат / ТО">
          <Input placeholder="Госномер / модель" value={form.plate || ""} onChange={(e) => setForm({ ...form, plate: e.target.value })} />
          <Input placeholder="Вид tractor/combine" value={form.kind || "tractor"} onChange={(e) => setForm({ ...form, kind: e.target.value })} />
          <Button className="min-h-11" onClick={async () => {
            await agroOpsPost("/machines", { plate: form.plate, kind: form.kind || "tractor", model: form.plate }, props.headers);
            setMsg("Сохранено");
            await load();
          }}>Создать машину</Button>
          <Input className="mt-2" placeholder="Агрегат seeder/sprayer" value={form.impl || ""} onChange={(e) => setForm({ ...form, impl: e.target.value })} />
          <Button className="min-h-11" onClick={() => void agroOpsPost("/implements", { name: form.impl, kind: form.impl_kind || "seeder" }, props.headers)}>Создать агрегат</Button>
          <Input className="mt-2" placeholder="machine_id для ТО" value={form.mid || ""} onChange={(e) => setForm({ ...form, mid: e.target.value })} />
          <Input type="date" value={form.due || ""} onChange={(e) => setForm({ ...form, due: e.target.value })} />
          <Button className="min-h-11" onClick={() => void agroOpsPost("/maintenance", { machine_id: form.mid, due_date: form.due, maintenance_type: "service" }, props.headers)}>Плановое ТО</Button>
        </Card>
      ) : null}
      {machines.map((m) => (
        <p key={pick(m, "id")} className="eds-type-small">{nd(m.plate || m.name)} · мч {nd(m.engine_hours)}</p>
      ))}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}

export const FIELD_QUICK_ACTIONS = QUICK;
