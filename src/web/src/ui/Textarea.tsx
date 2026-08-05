import type { TextareaHTMLAttributes } from "react";
import { cn } from "@/utils/cn";

type Props = TextareaHTMLAttributes<HTMLTextAreaElement> & {
  invalid?: boolean;
};

export function Textarea({ className, invalid, ...rest }: Props) {
  return (
    <textarea
      className={cn("eds-control", invalid && "border-[var(--eds-danger)]", className)}
      aria-invalid={invalid || undefined}
      {...rest}
    />
  );
}
