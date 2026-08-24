import { useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";

export function MobileActionButton({
  to,
  onClick,
  children,
  disabled,
  disabledReason,
  testId,
  variant = "primary",
  className,
}: {
  to?: string;
  onClick?: () => void | Promise<void>;
  children: ReactNode;
  disabled?: boolean;
  disabledReason?: string;
  testId?: string;
  variant?: "primary" | "secondary" | "ghost";
  className?: string;
}) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (disabled) return;
    setError(null);
    setBusy(true);
    try {
      if (onClick) await onClick();
      if (to) navigate(to);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось открыть");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <Button
        type="button"
        variant={variant}
        className={className || "w-full"}
        disabled={disabled || busy}
        loading={busy}
        onClick={() => void run()}
        data-testid={testId}
        title={disabled ? disabledReason : undefined}
      >
        {children}
      </Button>
      {disabled && disabledReason ? (
        <p className="mt-1 eds-type-caption text-[var(--eds-text-muted)]">{disabledReason}</p>
      ) : null}
      {error ? <p className="mt-1 eds-type-caption text-[var(--eds-danger)]">{error}</p> : null}
    </div>
  );
}
