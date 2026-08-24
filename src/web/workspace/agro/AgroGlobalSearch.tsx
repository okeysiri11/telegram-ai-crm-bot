/**
 * Global Agro search overlay — counterparties, deals, docs, shipments, etc.
 */

import { useEffect, useState } from "react";
import { Button, Input } from "@/ui";
import { agroOpsGet, pick } from "../business-ops/opsApi";

type Hit = { id: string; kind: string; title: string; subtitle?: string; view?: string };
type Group = { id: string; label_ru: string; items: Hit[] };

export function AgroGlobalSearch(props: {
  open: boolean;
  headers: Record<string, string>;
  onClose: () => void;
  onOpen: (view: string, kind: string, id: string) => void;
}) {
  const [q, setQ] = useState("");
  const [groups, setGroups] = useState<Group[]>([]);
  const [msg, setMsg] = useState("Введите запрос");

  useEffect(() => {
    if (!props.open) return;
    const t = window.setTimeout(async () => {
      const query = q.trim();
      if (!query) {
        setGroups([]);
        setMsg("Введите запрос");
        return;
      }
      const r = await agroOpsGet(`/search?q=${encodeURIComponent(query)}`, props.headers);
      const body = (r.json || {}) as { ok?: boolean; groups?: Group[] };
      setGroups(body.groups || []);
      setMsg(body.groups?.length ? "" : "Нет данных");
    }, 250);
    return () => window.clearTimeout(t);
  }, [q, props.open, props.headers]);

  if (!props.open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-3 pt-16" data-testid="agro-global-search">
      <div className="w-full max-w-lg rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface,#0f1420)] p-4">
        <div className="flex gap-2">
          <Input
            autoFocus
            placeholder="Операция, сделка, госномер, водитель, партия, ЕДРПОУ"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Глобальный поиск Агро"
            className="min-h-11"
          />
          <Button size="sm" variant="ghost" className="min-h-11" onClick={props.onClose}>
            Закрыть
          </Button>
        </div>
        {msg ? <p className="eds-type-small mt-3 text-[var(--ew-muted)]">{msg}</p> : null}
        <div className="mt-3 grid gap-3">
          {groups.map((g) => (
            <div key={g.id}>
              <p className="eds-type-caption text-[var(--ew-muted)]">{g.label_ru}</p>
              <ul>
                {g.items.map((item) => (
                  <li key={`${item.kind}-${item.id}`}>
                    <button
                      type="button"
                      className="min-h-11 w-full py-2 text-left underline"
                      onClick={() => props.onOpen(item.view || "home", item.kind, pick(item as Record<string, unknown>, "id"))}
                    >
                      {item.title}
                      {item.subtitle ? <span className="text-[var(--ew-muted)]"> · {item.subtitle}</span> : null}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
