/**
 * Sprint 33.1 — Simple | Pro toggle for top navigation.
 */

import { useExperienceModeStore, type ExperienceMode } from "./experienceModeStore";
import { cn } from "@/utils/cn";

export function SimpleProModeToggle({ className }: { className?: string } = {}) {
  const mode = useExperienceModeStore((s) => s.mode);
  const setMode = useExperienceModeStore((s) => s.setMode);

  return (
    <div
      className={cn("ews-mode-toggle inline-flex rounded-md border border-[var(--ew-border)] p-0.5", className)}
      role="group"
      aria-label="Режим интерфейса Simple или Pro"
    >
      {(["simple", "pro"] as ExperienceMode[]).map((m) => (
        <button
          key={m}
          type="button"
          className={cn(
            "eds-anim-micro rounded px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
            mode === m
              ? "bg-[var(--eds-accent)] text-[var(--eds-accent-fg,white)]"
              : "text-[var(--eds-text-muted)] hover:text-[var(--eds-text)]",
          )}
          aria-pressed={mode === m}
          onClick={() => setMode(m)}
        >
          {m === "simple" ? "Simple" : "Pro"}
        </button>
      ))}
    </div>
  );
}
