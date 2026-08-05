import type { InputHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  sizeVariant?: "sm" | "md" | "lg";
  invalid?: boolean;
};

export function Input({ className, sizeVariant = "md", invalid, ...rest }: Props) {
  return (
    <input
      className={cn(
        "eds-control",
        sizeVariant === "sm" && "eds-control--sm",
        sizeVariant === "lg" && "eds-control--lg",
        invalid && "border-[var(--eds-danger)]",
        className,
      )}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  );
}
