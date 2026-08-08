/**
 * Epic 45.1 — Header / Desktop mode switcher.
 * ⚪ Human · 🟢 AI · 🎙 Voice — only one active.
 */

import { cn } from "@/utils/cn";
import { useModeStore, type WorkMode, MODE_INDICATORS } from "./modeStore";
import "./mode-switch.css";

const OPTIONS: { id: WorkMode; label: string; testId: string }[] = [
  { id: "human", label: "⚪ Human", testId: "mode-human" },
  { id: "ai", label: "🟢 AI", testId: "mode-ai" },
  { id: "voice", label: "🎙 Voice", testId: "mode-voice" },
];

export function ModeIndicator({ className }: { className?: string }) {
  const mode = useModeStore((s) => s.mode);
  const indicator = useModeStore((s) => s.indicator);
  return (
    <span
      className={cn(
        "ados-mode-indicator",
        mode === "ai" && "ados-mode-indicator--ai",
        mode === "voice" && "ados-mode-indicator--voice",
        mode === "human" && "ados-mode-indicator--human",
        className,
      )}
      data-testid="mode-indicator"
      data-mode={mode}
      title={indicator}
    >
      {MODE_INDICATORS[mode]}
      {mode === "voice" ? <span className="ados-mode-mic" aria-hidden /> : null}
    </span>
  );
}

export function ModeSwitch({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  const mode = useModeStore((s) => s.mode);
  const setMode = useModeStore((s) => s.setMode);

  return (
    <div
      className={cn("ados-mode-switch", compact && "ados-mode-switch--compact", className)}
      role="radiogroup"
      aria-label="Режим работы"
      data-testid="mode-switch"
      data-mode={mode}
    >
      {OPTIONS.map((opt) => {
        const active = mode === opt.id;
        return (
          <button
            key={opt.id}
            type="button"
            role="radio"
            aria-checked={active}
            data-testid={opt.testId}
            className={cn(
              "ados-mode-btn",
              active && "ados-mode-btn--active",
              active && opt.id === "ai" && "ados-mode-btn--ai",
              active && opt.id === "voice" && "ados-mode-btn--voice",
            )}
            onClick={() => setMode(opt.id)}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
