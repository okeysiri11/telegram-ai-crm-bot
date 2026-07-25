import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
};

export function Button({ variant = "primary", size = "md", className, ...rest }: Props) {
  return (
    <button
      className={cn(
        "eds-focus-ring eds-type-button inline-flex items-center justify-center transition disabled:opacity-[var(--eds-opacity-disabled)]",
        "rounded-[var(--eds-radius-md)]",
        size === "sm" && "h-8 px-3",
        size === "md" && "h-10 px-4",
        size === "lg" && "h-11 px-5 text-base",
        variant === "primary" && "bg-[var(--eds-primary)] text-white hover:bg-[var(--eds-primary-hover)] active:bg-[var(--eds-primary-active)]",
        variant === "secondary" && "border border-[var(--eds-border)] bg-[var(--eds-surface)]",
        variant === "ghost" && "bg-transparent hover:bg-[var(--eds-primary-soft)]",
        variant === "danger" && "bg-[var(--eds-danger)] text-white",
        className,
      )}
      {...rest}
    />
  );
}
