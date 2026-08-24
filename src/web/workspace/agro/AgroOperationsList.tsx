/**
 * AGRO 2.2 — grain operations list. Same /operations backend for web and mobile.
 */

import { useEffect, useMemo, useState } from "react";
import { Button, Input } from "@/ui";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { agroOpsGet } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

function n(v: unknown): string {
  if (v === null || v === undefined || v === "") return "Нет данных";
  return String(v);
}

export function AgroOperationsList(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  filter?: string;
  onOpen: (id: string) => void;
  onCreate: () => void;
}) {
  const mobile = useIsMobile();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState(props.filter || "");
  const [crop, setCrop] = useState("");
  const [items, setItems] = useState<Row[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  const query = useMemo(() => {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (status) p.set("status", status);
    if (crop) p.set("crop", crop);
    p.set("limit", "50");
    return p.toString();
  }, [q, status, crop]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await agroOpsGet(`/operations?${query}`, props.headers);
      if (cancelled) return;
      const body = res.json as { items?: Row[]; message_ru?: string };
      if (!res.ok) {
        setMsg(body.message_ru || "Не удалось загрузить операции");
        setItems([]);
        return;
      }
      setMsg(null);
      setItems(Array.isArray(body.items) ? body.items : []);
    })();
    return () => {
      cancelled = true;
    };
  }, [query, props.headers]);

  return (
    <div className="space-y-3" data-testid="agro-operations-list">
      <div className="flex flex-wrap gap-2">
        <Input placeholder="AG-2026-000142, культура" value={q} onChange={(e) => setQ(e.target.value)} className="min-w-[12rem] flex-1 min-h-11" />
        <Input placeholder="Культура" value={crop} onChange={(e) => setCrop(e.target.value)} className="w-32 min-h-11" />
        {props.canCreate ? (
          <Button size="sm" className="min-h-11" onClick={props.onCreate}>
            Создать операцию
          </Button>
        ) : null}
      </div>
      {msg ? <p className="eds-type-small text-[var(--ew-danger)]">{msg}</p> : null}
      {!items.length ? <p className="eds-type-small text-[var(--ew-muted)]">Нет данных</p> : null}
      {mobile ? (
        <div className="grid gap-2">
          {items.map((r) => (
            <button
              key={String(r.id)}
              type="button"
              className="min-h-11 rounded-lg border border-[var(--ew-border)] p-3 text-left"
              onClick={() => props.onOpen(String(r.id))}
              data-testid="agro-op-card"
            >
              <p className="font-semibold">{n(r.number)}</p>
              <p className="eds-type-small">
                {n(r.crop)} · {n(r.status_ru)}
              </p>
              <p className="eds-type-caption text-[var(--ew-muted)]">
                Закуплено {n(r.planned_qty)} · Принято {n(r.received_qty)} · Продано {n(r.sold_qty)} · Остаток {n(r.remaining_qty)}
              </p>
            </button>
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left eds-type-small">
            <thead>
              <tr>
                <th>Номер</th>
                <th>Культура</th>
                <th>Статус</th>
                <th>План</th>
                <th>Принято</th>
                <th>Продано</th>
                <th>Остаток</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={String(r.id)} className="border-t border-[var(--ew-border)]">
                  <td>
                    <button type="button" className="min-h-11 underline" onClick={() => props.onOpen(String(r.id))}>
                      {n(r.number)}
                    </button>
                  </td>
                  <td>{n(r.crop)}</td>
                  <td>{n(r.status_ru)}</td>
                  <td>{n(r.planned_qty)}</td>
                  <td>{n(r.received_qty)}</td>
                  <td>{n(r.sold_qty)}</td>
                  <td>{n(r.remaining_qty)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
