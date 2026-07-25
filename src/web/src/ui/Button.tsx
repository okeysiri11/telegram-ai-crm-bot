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
        "inline-flex items-center justify-center rounded-md font-medium transition disabled:opacity-50",
        size === "sm" && "h-8 px-3 text-sm",
        size === "md" && "h-10 px-4 text-sm",
        size === "lg" && "h-11 px-5 text-base",
        variant === "primary" && "bg-[var(--ew-brand)] text-white",
        variant === "secondary" && "border border-[var(--ew-border)] bg-[var(--ew-surface)]",
        variant === "ghost" && "bg-transparent hover:bg-[var(--ew-brand-soft)]",
        variant === "danger" && "bg-[var(--ew-danger)] text-white",
        className,
      )}
      {...rest}
    />
  );
}
