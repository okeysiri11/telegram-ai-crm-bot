import type { SelectHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

type Props = SelectHTMLAttributes<HTMLSelectElement> & {
  sizeVariant?: "sm" | "md" | "lg";
  invalid?: boolean;
};

export function Select({ className, children, sizeVariant = "md", invalid, ...rest }: Props) {
  return (
    <select
      className={cn(
        "eds-control",
        sizeVariant === "sm" && "eds-control--sm",
        sizeVariant === "lg" && "eds-control--lg",
        invalid && "border-[var(--eds-danger)]",
        className,
      )}
      aria-invalid={invalid || undefined}
      {...rest}
    >
      {children}
    </select>
  );
}
