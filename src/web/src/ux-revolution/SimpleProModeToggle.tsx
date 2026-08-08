/**
 * Sprint 33.1 / 42.3 — Simple | Pro toggle (RU labels for Human-First).
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
      aria-label="Простой или профессиональный режим"
      data-testid="simple-pro-toggle"
    >
      {(["simple", "pro"] as ExperienceMode[]).map((m) => (
        <button
          key={m}
          type="button"
          className={cn(
            "eds-anim-micro rounded px-2.5 py-1 text-xs font-semibold tracking-wide",
            mode === m
              ? "bg-[var(--eds-accent)] text-[var(--eds-accent-fg,white)]"
              : "text-[var(--eds-text-muted)] hover:text-[var(--eds-text)]",
          )}
          aria-pressed={mode === m}
          onClick={() => setMode(m)}
          data-testid={m === "simple" ? "mode-simple" : "mode-pro"}
        >
          {m === "simple" ? "Простой режим" : "Профессиональный режим"}
        </button>
      ))}
    </div>
  );
}
