import { Button } from "@/ui";
import type { OpsRow } from "../business-ops/BusinessCabinetShell";

export function LawyerRowMenu({
  row,
  onOpen,
  onEdit,
  onArchive,
  extra,
}: {
  row: OpsRow;
  onOpen?: () => void;
  onEdit?: () => void;
  onArchive?: () => void;
  extra?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap gap-1" data-testid="lawyer-row-actions">
      {onOpen ? (
        <Button size="sm" variant="ghost" onClick={onOpen}>
          Открыть
        </Button>
      ) : null}
      {onEdit ? (
        <Button size="sm" variant="ghost" onClick={onEdit}>
          Изменить
        </Button>
      ) : null}
      {onArchive ? (
        <Button size="sm" variant="ghost" onClick={onArchive}>
          Удалить
        </Button>
      ) : null}
      {extra}
    </div>
  );
}

export function LawyerConfirm({
  open,
  text,
  confirmLabel = "Да, в архив",
  onYes,
  onNo,
}: {
  open: boolean;
  text: string;
  confirmLabel?: string;
  onYes: () => void;
  onNo: () => void;
}) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      data-testid="lawyer-archive-confirm"
    >
      <div className="w-full max-w-md rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-4">
        <p className="font-medium mb-1">Удалить объект?</p>
        <p className="eds-type-body">{text}</p>
        <div className="mt-3 flex gap-2">
          <Button size="sm" onClick={onYes}>
            {confirmLabel}
          </Button>
          <Button size="sm" variant="ghost" onClick={onNo}>
            Отмена
          </Button>
        </div>
      </div>
    </div>
  );
}
