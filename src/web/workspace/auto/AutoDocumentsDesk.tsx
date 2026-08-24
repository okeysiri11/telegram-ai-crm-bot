/**
 * AUTO 1.6 — documents desk: KPIs, register, generate DRAFT, completeness.
 * Business language only. No storage keys or DB ids in the main view.
 */

import { useCallback, useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { asList, autoOpsGet, autoOpsPost, pick } from "../business-ops/opsApi";
import { DOC_RU } from "./autoLabels";

type Rec = Record<string, unknown>;

export function AutoDocumentsDesk({
  headers,
  vehicles,
  canCreate,
  onDone,
}: {
  headers: Record<string, string>;
  vehicles: Rec[];
  canCreate: boolean;
  onDone: () => Promise<void>;
}) {
  const [data, setData] = useState<Rec>({});
  const [vin, setVin] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [gen, setGen] = useState("sale_agreement_draft");
  const [vehicleId, setVehicleId] = useState("");

  const load = useCallback(async () => {
    const q = vin ? `?vin=${encodeURIComponent(vin)}` : "";
    const res = await autoOpsGet(`/documents/desk${q}`, headers);
    setData((res.json || {}) as Rec);
  }, [headers, vin]);

  useEffect(() => {
    void load();
  }, [load]);

  const kpis = (data.kpis || {}) as Rec;
  const items = asList(data) as Rec[];
  const templates = asList(data.generation_templates, ["generation_templates"]) as Rec[];

  async function defAction(path: string, body: Rec = {}) {
    const res = await autoOpsPost(path, body, headers);
    const j = (res.json || {}) as Rec;
    if (!res.ok || j.ok === false) setMsg(String(j.message_ru || "Не выполнено"));
    else {
      setMsg(String(j.message_ru || "Готово"));
      await load();
      await onDone();
    }
  }

  return (
    <div className="space-y-4" data-testid="auto-documents-desk">
      <div className="grid gap-3 md:grid-cols-5">
        {[
          ["Всего документов", kpis.total],
          ["Не хватает", kpis.missing],
          ["На проверке", kpis.review],
          ["Истекают", kpis.expiring],
          ["Отклонены", kpis.rejected],
        ].map(([label, value]) => (
          <Card key={String(label)}>
            <p className="eds-type-caption">{String(label)}</p>
            <p className="text-xl font-medium">{String(value ?? 0)}</p>
          </Card>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {canCreate ? <span className="eds-type-helper">+ Добавить документ — форма ниже.</span> : null}
        <Button
          size="sm"
          onClick={() => void defAction("/documents/generate", { template_id: gen, vehicle_id: vehicleId })}
        >
          Создать документ
        </Button>
        <Button size="sm" variant="secondary" onClick={() => void defAction("/documents/check", { vehicle_id: vehicleId })}>
          Проверить комплектность
        </Button>
        <a className="eds-btn eds-btn-sm" href={`/api/auto-ops/v1/documents/export`} onClick={(e) => {
          e.preventDefault();
          void autoOpsGet("/documents/export", headers).then(() => setMsg("Экспорт CSV готов (список, без файлов)."));
        }}>
          Экспорт списка
        </a>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <Input placeholder="Поиск по VIN" value={vin} onChange={(e) => setVin(e.target.value)} />
        <select className="eds-input rounded border px-2 py-1" value={vehicleId} onChange={(e) => setVehicleId(e.target.value)}>
          <option value="">Автомобиль</option>
          {vehicles.map((v) => (
            <option key={String(v.id)} value={String(v.id)}>{pick(v, "title", "vin")}</option>
          ))}
        </select>
        <select className="eds-input rounded border px-2 py-1" value={gen} onChange={(e) => setGen(e.target.value)}>
          {templates.map((t) => (
            <option key={String(t.id)} value={String(t.id)}>{String(t.name_ru)}</option>
          ))}
        </select>
      </div>
      <p className="eds-type-helper">Созданный документ — черновик шаблона, не юридически гарантированный текст.</p>
      <div className="overflow-x-auto" data-testid="auto-documents-table-wrap">
      <table className="w-full min-w-[720px] text-left" data-testid="auto-documents-table">
        <thead>
          <tr className="eds-type-caption">
            {["Документ", "Авто", "VIN", "Клиент", "Категория", "Тип", "Дата", "Статус", "Ответственный"].map((h) => (
              <th key={h} className="pr-2">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((d) => (
            <tr key={String(d.id)}>
              <td>{pick(d, "title", "file_name")}</td>
              <td>{pick(d, "vehicle_title")}</td>
              <td>{pick(d, "vin")}</td>
              <td>{pick(d, "client_name")}</td>
              <td>{pick(d, "category")}</td>
              <td>{DOC_RU[String(d.document_type)] || pick(d, "type_ru", "document_type")}</td>
              <td>{String(d.issued_date || d.created_at || "").slice(0, 10)}</td>
              <td>{pick(d, "workflow_status") || pick(d, "finance_verify") || "—"}</td>
              <td>{pick(d, "assigned_to", "uploaded_by")}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
      {!items.length ? <p className="eds-type-helper">Документов пока нет</p> : null}
      {msg ? <p className="eds-type-helper">{msg}</p> : null}
    </div>
  );
}

export function DocumentPackageCard({
  title,
  pack,
}: {
  title: string;
  pack: Rec | null;
}) {
  if (!pack) return null;
  const items = asList(pack) as Rec[];
  const missing = asList(pack.missing, ["missing"]) as string[];
  return (
    <Card title={title} data-testid={title.includes("продаж") ? "auto-sale-package" : "auto-registration-package"}>
      <p className="font-medium">{String(pack.status_ru || (pack.ready ? "ГОТОВО" : "НЕ ГОТОВО"))}</p>
      {pack.note_ru ? <p className="eds-type-helper">{String(pack.note_ru)}</p> : null}
      <ul className="mt-2 space-y-1">
        {items.map((i) => (
          <li key={String(i.id || i.name)}>{i.present ? "✓" : "○"} {pick(i, "label_ru", "name")}</li>
        ))}
      </ul>
      {missing.length ? (
        <p className="mt-2 eds-type-helper">Отсутствуют: {missing.join(", ")}</p>
      ) : null}
    </Card>
  );
}

export function DocumentTemplatesSettings({
  headers,
  canAdmin,
}: {
  headers: Record<string, string>;
  canAdmin: boolean;
}) {
  const [items, setItems] = useState<Rec[]>([]);
  const [stages, setStages] = useState<Rec[]>([]);
  const [name, setName] = useState("");
  const [stage, setStage] = useState("registration");

  const load = useCallback(async () => {
    const res = await autoOpsGet("/documents/templates", headers);
    const j = (res.json || {}) as Rec;
    setItems(asList(j) as Rec[]);
    setStages(asList(j.stages, ["stages"]) as Rec[]);
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div data-testid="auto-document-templates">
    <Card title="Документы">
      <p className="eds-type-helper">Шаблоны комплектности. Регистрация — настраиваемый операционный перечень, не юридическая норма.</p>
      {canAdmin ? (
        <form
          className="mt-2 flex flex-wrap gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            void autoOpsPost("/documents/templates", { name, stage, document_type: "other", required: true }, headers).then(() => {
              setName("");
              void load();
            });
          }}
        >
          <select className="eds-input rounded border px-2 py-1" value={stage} onChange={(e) => setStage(e.target.value)}>
            {stages.map((s) => (
              <option key={String(s.id)} value={String(s.id)}>{String(s.name)}</option>
            ))}
          </select>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Название пункта" />
          <Button type="submit" size="sm">Добавить пункт</Button>
        </form>
      ) : (
        <p className="eds-type-helper">Изменять шаблоны может администратор.</p>
      )}
      <ul className="mt-3 space-y-1">
        {items.filter((i) => i.active !== false).map((i) => (
          <li key={String(i.id)}>{pick(i, "stage_name", "stage")} · {pick(i, "name")} {i.required ? "(обязательно)" : ""}</li>
        ))}
      </ul>
    </Card>
    </div>
  );
}
