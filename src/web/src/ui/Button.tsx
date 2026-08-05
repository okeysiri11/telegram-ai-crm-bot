import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "success" | "icon";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  toolbar?: boolean;
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  toolbar = false,
  className,
  children,
  disabled,
  ...rest
}: Props) {
  const busy = loading || undefined;
  return (
    <button
      className={cn(
        "eds-btn eds-focus-ring eds-type-button",
        size === "sm" && "h-8 px-3 text-[0.8125rem]",
        size === "md" && "h-10 px-4",
        size === "lg" && "h-11 px-5 text-base",
        toolbar && "eds-btn--toolbar",
        variant === "primary" &&
          "bg-[var(--eds-primary)] text-white hover:bg-[var(--eds-primary-hover)] active:bg-[var(--eds-primary-active)]",
        variant === "secondary" &&
          "border border-[var(--eds-border)] bg-[var(--eds-surface)] hover:border-[var(--eds-primary)] hover:bg-[var(--eds-primary-soft)]",
        variant === "ghost" && "bg-transparent hover:bg-[var(--eds-primary-soft)]",
        variant === "danger" && "bg-[var(--eds-danger)] text-white hover:brightness-105",
        variant === "success" && "eds-btn--success",
        variant === "icon" && "eds-btn--icon border border-[var(--eds-border)] bg-[var(--eds-surface)] hover:bg-[var(--eds-primary-soft)]",
        className,
      )}
      aria-busy={busy}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <span className="eds-anim-loading" aria-hidden /> : null}
      {children}
    </button>
  );
}
