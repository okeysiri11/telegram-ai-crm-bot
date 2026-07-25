import type { ReactNode } from "react";

export function Table({ headers, children }: { headers: string[]; children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-md border border-[var(--ew-border)]">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-[var(--ew-brand-soft)]/40">
          <tr>
            {headers.map((h) => (
              <th key={h} className="px-3 py-2 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
