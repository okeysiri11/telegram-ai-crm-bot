import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

export function Table({
  headers,
  children,
  empty,
  className,
}: {
  headers: string[];
  children: ReactNode;
  empty?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("eds-table-wrap", className)}>
      <table className="eds-table">
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
      {empty ? <div className="eds-table__empty">{empty}</div> : null}
    </div>
  );
}
