import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/utils/cn";
import { quickSwitcher, type QuickSwitchTarget } from "../managers/quickSwitcher";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function QuickSwitcher({ open, onClose }: Props) {
  const navigate = useNavigate();
  const [target, setTarget] = useState<QuickSwitchTarget>("applications");
  const [active, setActive] = useState(0);
  const items = quickSwitcher.list();

  useEffect(() => {
    if (!open) return;
    quickSwitcher.setTarget(target);
    setActive(0);
  }, [open, target]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown" || (e.key === "Tab" && !e.shiftKey && !e.ctrlKey)) {
        e.preventDefault();
        setActive((i) => Math.min(i + 1, items.length - 1));
      }
      if (e.key === "ArrowUp" || (e.key === "Tab" && e.shiftKey)) {
        e.preventDefault();
        setActive((i) => Math.max(i - 1, 0));
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const item = items[active];
        if (item) {
          navigate(item.route);
          onClose();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, items, active, navigate, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[var(--eds-z-modal,50)] flex items-start justify-center bg-black/40 p-4 pt-[14vh]" role="dialog" aria-modal="true" aria-label="Quick switcher">
      <div className="w-full max-w-lg overflow-hidden rounded-[var(--eds-radius-lg)] bg-[var(--eds-surface)] shadow-[var(--eds-shadow-lg)] eds-anim-scale">
        <div className="flex flex-wrap gap-1 border-b border-[var(--eds-border)] p-2">
          {quickSwitcher.targets().map((t) => (
            <button
              key={t}
              type="button"
              className={cn(
                "rounded-md px-2 py-1 eds-type-caption capitalize",
                target === t ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "text-[var(--eds-text-muted)]",
              )}
              onClick={() => setTarget(t)}
            >
              {t.replace("_", " ")}
            </button>
          ))}
        </div>
        <ul className="max-h-72 overflow-auto p-2">
          {items.map((item, i) => (
            <li key={item.id}>
              <button
                type="button"
                className={cn(
                  "flex w-full items-center justify-between rounded-md px-3 py-2 text-left eds-type-small",
                  i === active ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "hover:bg-[var(--eds-primary-soft)]/50",
                )}
                onMouseEnter={() => setActive(i)}
                onClick={() => {
                  navigate(item.route);
                  onClose();
                }}
              >
                <span>{item.label}</span>
                <span className="eds-type-caption">{item.route}</span>
              </button>
            </li>
          ))}
        </ul>
        <p className="border-t border-[var(--eds-border)] px-3 py-2 eds-type-caption text-[var(--eds-text-muted)]">
          Ctrl+Tab · Switch applications, dashboards, workspaces, AI chats, documents
        </p>
      </div>
    </div>
  );
}
