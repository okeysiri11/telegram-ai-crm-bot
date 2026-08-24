/**
 * AGRO 1.2 — deliveries with partial progress.
 */

import { useState } from "react";
import { Button, Card, Input } from "@/ui";
import { agroOpsPost, pick } from "../business-ops/opsApi";
import { ruStatus } from "./agroLabels";

type Row = Record<string, unknown>;

export function AgroDeliveriesPanel(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  shipments: Row[];
  counterparties: Row[];
  onChanged: () => void;
  onOpen: (id: string) => void;
  onAttach: (id: string) => void;
}) {
  const [form, setForm] = useState<Row>({ title: "Поставка пшеницы", crop: "Пшеница", quantity: "600" });
  const [partial, setPartial] = useState<Row>({ quantity: "200" });
  const [msg, setMsg] = useState("");

  return (
    <div className="grid gap-3" data-testid="agro-deliveries-panel">
      {!props.shipments.length ? (
        <Card title="Поставок ещё нет.">
          {props.canCreate ? <Button size="sm" onClick={() => undefined}>Добавить поставку</Button> : null}
          <p className="eds-type-small mt-2">Поставка появляется только после сохранения. Прогресс не выдумывается.</p>
        </Card>
      ) : (
        <ul className="eds-type-small" data-testid="agro-delivery-list">
          {props.shipments.map((s) => (
            <li key={pick(s, "id")} className="flex items-center justify-between border-b border-[var(--ew-border)] py-1">
              <button type="button" className="underline" onClick={() => props.onOpen(pick(s, "id"))}>
                {pick(s, "title")} · {String(s.quantity_delivered ?? 0)} / {String(s.quantity_planned ?? s.quantity ?? 0)} · {String(s.progress_pct ?? 0)}% · {ruStatus(pick(s, "status"))}
              </button>
              <Button size="sm" variant="ghost" onClick={() => props.onAttach(pick(s, "id"))}>📎</Button>
            </li>
          ))}
        </ul>
      )}
      {props.canCreate ? (
        <Card title="Добавить поставку">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Название" value={String(form.title || "")} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
            <Input placeholder="Культура" value={String(form.crop || "")} onChange={(e) => setForm((f) => ({ ...f, crop: e.target.value }))} />
            <Input placeholder="План, т" value={String(form.quantity || "")} onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))} />
            <Input type="date" value={String(form.deadline_at || "")} onChange={(e) => setForm((f) => ({ ...f, deadline_at: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.counterparty_id || "")} onChange={(e) => setForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
              <option value="">Контрагент</option>
              {props.counterparties.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </div>
          <Button
            className="mt-2"
            size="sm"
            onClick={async () => {
              const r = await agroOpsPost("/entities/shipment", form, props.headers);
              const j = r.json as { ok?: boolean; message_ru?: string };
              setMsg(j.ok ? "Поставка создана" : j.message_ru || "Ошибка");
              if (j.ok) props.onChanged();
            }}
          >
            Сохранить поставку
          </Button>
        </Card>
      ) : null}
      {props.canCreate && props.shipments.length ? (
        <Card title="Частичная поставка">
          <div className="grid gap-2 sm:grid-cols-2">
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(partial.shipment_id || "")} onChange={(e) => setPartial((f) => ({ ...f, shipment_id: e.target.value }))}>
              <option value="">Поставка</option>
              {props.shipments.map((s) => (
                <option key={pick(s, "id")} value={pick(s, "id")}>
                  {pick(s, "title")}
                </option>
              ))}
            </select>
            <Input placeholder="Объём, т" value={String(partial.quantity || "")} onChange={(e) => setPartial((f) => ({ ...f, quantity: e.target.value }))} />
          </div>
          <Button
            className="mt-2"
            size="sm"
            onClick={async () => {
              const r = await agroOpsPost(`/deliveries/${partial.shipment_id}/progress`, { quantity: partial.quantity }, props.headers);
              const j = r.json as { ok?: boolean; message_ru?: string };
              setMsg(j.ok ? "Прогресс обновлён" : j.message_ru || "Ошибка");
              if (j.ok) props.onChanged();
            }}
          >
            Зафиксировать
          </Button>
        </Card>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
