/**
 * One universal Agro create sheet. Existing entity forms are rendered as children.
 */

import type { ReactNode } from "react";
import { Button } from "@/ui";
import { OPERATION_QUICK_ACTIONS } from "./AgroOperation360";

export const QUICK_CREATE_ACTIONS: { id: string; label: string; create?: boolean; finance?: boolean }[] = [
  { id: "operation", label: "+ Операция", create: true },
  { id: "counterparty", label: "+ Контрагент", create: true },
  { id: "deal", label: "+ Сделка", create: true },
  { id: "shipment", label: "+ Поставка", create: true },
  { id: "documents", label: "+ Документ" },
  { id: "payment", label: "+ Платёж", finance: true },
  { id: "task", label: "+ Задача" },
  { id: "warehouse_op", label: "+ Складская операция", create: true },
  { id: "price", label: "+ Цена", create: true },
  { id: "calendar", label: "+ Напоминание" },
];

export function AgroQuickCreateSheet(props: {
  open: boolean;
  kind: string | null;
  canCreate: boolean;
  canFinance: boolean;
  insideOperation?: boolean;
  onSelect: (id: string) => void;
  onClose: () => void;
  children?: ReactNode;
}) {
  if (!props.open) return null;
  const base = QUICK_CREATE_ACTIONS.filter((a) => {
    if (a.finance && !props.canFinance) return false;
    if (a.create && !props.canCreate && !a.finance) return false;
    if (a.id === "documents" || a.id === "task" || a.id === "calendar") return true;
    return true;
  });
  const actions = props.insideOperation
    ? OPERATION_QUICK_ACTIONS.filter((a) => (a.id === "expense" ? props.canFinance || props.canCreate : props.canCreate || a.id === "documents" || a.id === "task"))
    : base;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-3 sm:items-center" data-testid="agro-quick-sheet">
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface,#0f1420)] p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h3 className="font-semibold">Быстрые действия</h3>
          <Button size="sm" variant="ghost" onClick={props.onClose} className="min-h-11 min-w-11">
            Закрыть
          </Button>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3" data-testid="agro-quick-actions">
          {actions.map((a) => (
            <Button
              key={a.id}
              size="sm"
              variant={props.kind === a.id ? "primary" : "secondary"}
              className="min-h-11"
              onClick={() => props.onSelect(a.id)}
            >
              {a.label}
            </Button>
          ))}
        </div>
        <div className="mt-4">{props.children}</div>
      </div>
    </div>
  );
}
