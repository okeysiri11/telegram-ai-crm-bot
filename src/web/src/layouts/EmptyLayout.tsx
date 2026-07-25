import type { ReactNode } from "react";

export function EmptyLayout({ children }: { children: ReactNode }) {
  return <div className="min-h-full p-6">{children}</div>;
}
