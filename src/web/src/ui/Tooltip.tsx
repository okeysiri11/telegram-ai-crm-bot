import type { ReactNode } from "react";

export function Tooltip({ label, children }: { label: string; children: ReactNode }) {
  return (
    <span className="group relative inline-flex">
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 z-10 mb-1 hidden -translate-x-1/2 whitespace-nowrap rounded bg-black px-2 py-1 text-xs text-white group-hover:block">
        {label}
      </span>
    </span>
  );
}
