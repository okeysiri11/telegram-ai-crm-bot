/**
 * AGRO 1.1 — generic right-side dossier for logistics / markets / warehouses.
 */

import { useEffect, useState } from "react";
import { Button } from "@/ui";
import { agroOpsFileUrl, agroOpsGet, agroOpsPost, agroOpsUpload, pick } from "../business-ops/opsApi";
import { DOC_TYPES, ENTITY_TYPES, ru, ruStatus } from "./agroLabels";

type Row = Record<string, unknown>;

export function AgroOpsDrawer({
  kind,
  itemId,
  headers,
  canOperate,
  onClose,
  onChanged,
}: {
  kind: string;
  itemId: string;
  headers: Record<string, string>;
  canOperate: boolean;
  onClose: () => void;
  onChanged?: () => void;
}) {
  const [item, setItem] = useState<Row | null>(null);
  const [files, setFiles] = useState<Row[]>([]);
  const [activity, setActivity] = useState<Row[]>([]);
  const [related, setRelated] = useState<Record<string, Row[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "documents" | "history" | "links">("overview");
  const [actionMsg, setActionMsg] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await agroOpsGet(`/entities/${kind}/${itemId}`, headers);
      const rel = await agroOpsGet(`/entities/${kind}/${itemId}/related`, headers);
      if (cancelled) return;
      if (!res.ok) {
        setError("Не удалось загрузить карточку");
        return;
      }
      const body = res.json as { item?: Row; files?: Row[]; activity?: Row[] };
      setItem(body.item || null);
      setFiles(body.files || []);
      setActivity(body.activity || []);
      if (rel.ok) {
        const rb = rel.json as { related?: Record<string, Row[]> };
        setRelated(rb.related || {});
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [kind, itemId, headers]);

  const title = item ? String(pick(item, "name", "title", "full_name", "plate") || "Карточка") : "Загрузка…";

  return (
    <div
      className="fixed inset-y-0 right-0 z-40 w-full max-w-xl overflow-y-auto border-l border-[var(--ew-border)] bg-[var(--eds-surface,var(--ew-surface,#0f1420))] p-4 shadow-xl"
      data-testid="agro-ops-drawer"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <p className="eds-type-small text-[var(--ew-muted)]">{ENTITY_TYPES[kind] || kind}</p>
          <h3 className="font-semibold">{title}</h3>
        </div>
        <div className="flex gap-1">
          {canOperate ? (
            <Button
              size="sm"
              variant="ghost"
              onClick={async () => {
                const r = await agroOpsPost(`/entities/${kind}/${itemId}/archive`, {}, headers);
                const j = r.json as { ok?: boolean; message_ru?: string };
                setActionMsg(j.ok ? "В архиве" : j.message_ru || "Не удалось архивировать");
                if (j.ok) {
                  onChanged?.();
                  onClose();
                }
              }}
            >
              Архивировать
            </Button>
          ) : null}
          <Button size="sm" variant="ghost" onClick={onClose}>
            Закрыть
          </Button>
        </div>
      </div>
      {error ? <p className="eds-type-small text-[var(--ew-danger)]">{error}</p> : null}
      <div className="mb-3 flex flex-wrap gap-1">
        {(
          [
            ["overview", "Обзор"],
            ["links", "Связи"],
            ["documents", "Документы"],
            ["history", "История"],
          ] as const
        ).map(([id, label]) => (
          <Button key={id} size="sm" variant={tab === id ? "secondary" : "ghost"} onClick={() => setTab(id)}>
            {label}
          </Button>
        ))}
      </div>
      {tab === "overview" && item ? (
        <dl className="grid gap-1 eds-type-small" data-testid="agro-ops-overview">
          {Object.entries(item)
            .filter(([k, v]) => !["id", "organization_id", "tenant_id", "payload", "created_by"].includes(k) && v != null && String(v).trim())
            .slice(0, 24)
            .map(([k, v]) => (
              <div key={k}>
                {k === "status" ? `Статус: ${ruStatus(String(v))}` : `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`}
              </div>
            ))}
        </dl>
      ) : null}
      {tab === "overview" && kind === "trip" && item && canOperate ? (
        <div className="mt-3 flex flex-wrap gap-2">
          <Button
            size="sm"
            onClick={async () => {
              const r = await agroOpsPost(
                "/warehouses/receive",
                {
                  trip_id: itemId,
                  warehouse_id: item.warehouse_id,
                  commodity: item.crop || item.cargo,
                  quantity: item.weight_actual || item.weight_planned,
                  deal_id: item.deal_id,
                  vehicle_id: item.vehicle_id,
                  driver_id: item.driver_id,
                },
                headers,
              );
              const j = r.json as { ok?: boolean; message_ru?: string };
              setActionMsg(j.ok ? "Принято на склад" : j.message_ru || "Укажите склад в рейсе");
              if (j.ok) onChanged?.();
            }}
          >
            Принять на склад
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={async () => {
              const r = await agroOpsPost(
                "/warehouses/issue",
                {
                  trip_id: itemId,
                  warehouse_id: item.warehouse_id,
                  lot_id: item.lot_id,
                  commodity: item.crop || item.cargo,
                  quantity: item.weight_actual || item.weight_planned,
                  deal_id: item.deal_id,
                },
                headers,
              );
              const j = r.json as { ok?: boolean; message_ru?: string };
              setActionMsg(j.ok ? "Расход подтверждён" : j.message_ru || "Укажите склад и партию");
              if (j.ok) onChanged?.();
            }}
          >
            Подтвердить расход
          </Button>
          {actionMsg ? <p className="eds-type-small w-full">{actionMsg}</p> : null}
        </div>
      ) : null}
      {tab === "links" ? (
        <div className="eds-type-small grid gap-2" data-testid="agro-ops-links">
          {[
            ["deals", "Сделка"],
            ["counterparties", "Контрагент"],
            ["documents", "Документы"],
            ["trips", "Транспорт / рейсы"],
            ["vehicles", "Транспорт"],
            ["lots", "Склад / партии"],
            ["warehouse_operations", "Складские операции"],
            ["payments", "Платежи"],
            ["tasks", "Задачи"],
          ].map(([key, label]) => (
            <div key={key}>
              <p className="eds-type-caption text-[var(--ew-muted)]">{label}</p>
              {(related[key] || []).length ? (
                (related[key] || []).slice(0, 8).map((r) => (
                  <p key={pick(r, "id")}>{pick(r, "title", "name", "filename", "plate")}</p>
                ))
              ) : (
                <p>Нет данных</p>
              )}
            </div>
          ))}
        </div>
      ) : null}
      {tab === "documents" ? (
        <div>
          {files.length ? (
            files.map((f) => (
              <a key={pick(f, "id")} className="block eds-type-small underline" href={agroOpsFileUrl(pick(f, "id"))} target="_blank" rel="noreferrer">
                {pick(f, "filename")} · {ru(DOC_TYPES, pick(f, "doc_type"))}
              </a>
            ))
          ) : (
            <p className="eds-type-small text-[var(--ew-muted)]">Документов пока нет</p>
          )}
          {canOperate ? (
            <input
              className="mt-2 eds-type-small"
              type="file"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.jpg,.jpeg,.png"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const res = await agroOpsUpload("/files", file, { entity_type: kind, entity_id: itemId, doc_type: "other" }, headers);
                if (res.ok) onChanged?.();
              }}
            />
          ) : null}
        </div>
      ) : null}
      {tab === "history" ? (
        activity.length ? (
          <ul className="eds-type-small">
            {activity.slice(0, 20).map((a) => (
              <li key={pick(a, "id")} className="border-b border-[var(--ew-border)] py-1">
                {pick(a, "summary")} · {pick(a, "created_at")}
              </li>
            ))}
          </ul>
        ) : (
          <p className="eds-type-small text-[var(--ew-muted)]">Истории пока нет</p>
        )
      ) : null}
    </div>
  );
}
