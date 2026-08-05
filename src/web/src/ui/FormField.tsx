import type { ReactNode } from "react";

/** Shared form field chrome — label + control + helper / error (EDL). */
export function FormField({
  label,
  htmlFor,
  helper,
  error,
  children,
}: {
  label: string;
  htmlFor?: string;
  helper?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-[var(--eds-space-2)]">
      <label htmlFor={htmlFor} className="eds-type-label text-[var(--eds-text)]">
        {label}
      </label>
      {children}
      {error ? (
        <p className="eds-type-helper text-[var(--eds-danger)]" role="alert">
          {error}
        </p>
      ) : helper ? (
        <p className="eds-type-helper">{helper}</p>
      ) : null}
    </div>
  );
}
