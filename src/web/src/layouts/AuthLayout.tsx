import type { ReactNode } from "react";

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full items-center justify-center bg-[linear-gradient(160deg,#0f6a5a_0%,#142033_55%,#0b1220_100%)] p-6">
      <div className="w-full max-w-md rounded-xl bg-[var(--ew-surface)] p-6 shadow-xl">{children}</div>
    </div>
  );
}
