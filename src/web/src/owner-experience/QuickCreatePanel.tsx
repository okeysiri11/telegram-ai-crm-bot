/**
 * Sprint 42.9 — большая панель «Создать».
 */

import { Link } from "react-router-dom";
import { Button } from "@/ui";

export const CREATE_ITEMS = [
  { label: "Клиента", route: "/crm?view=clients&action=create" },
  { label: "Документ", route: "/documents?action=create" },
  { label: "Проект", route: "/tasks?action=create" },
  { label: "AI-задачу", route: "/ai-tasks?action=create" },
  { label: "Напоминание", route: "/calendar?action=reminder" },
  { label: "Сделку", route: "/crm?view=deals&action=create" },
  { label: "Контакт", route: "/crm?view=contacts&action=create" },
] as const;

export function QuickCreatePanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  if (!open) return null;

  return (
    <div className="oe-create-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="oe-create-panel ews-glass"
        role="dialog"
        aria-label="Создать"
        data-testid="quick-create-panel"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between gap-2">
          <div>
            <p className="eds-type-caption text-[var(--eds-text-muted)]">Быстрые действия</p>
            <h2 className="eds-type-title text-xl">Создать</h2>
          </div>
          <Button size="sm" variant="ghost" onClick={onClose}>
            Закрыть
          </Button>
        </header>
        <div className="oe-create-grid">
          {CREATE_ITEMS.map((item) => (
            <Link
              key={item.label}
              to={item.route}
              className="oe-create-card"
              onClick={onClose}
            >
              <span className="eds-type-section">{item.label}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
