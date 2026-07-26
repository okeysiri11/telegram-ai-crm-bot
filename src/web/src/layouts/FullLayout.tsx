import type { ReactNode } from "react";
import { useState } from "react";
import { Sidebar } from "@/navigation/Sidebar";
import { TopNavigation } from "@/navigation/TopNavigation";

/** Shared application shell — sidebar + top nav + workspace container. */
export function FullLayout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex min-h-full eds-shell">
      <Sidebar mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavigation onMenuToggle={() => setMobileOpen((v) => !v)} />
        <main className="eds-main flex-1 p-4 md:p-6 xl:p-8">
          <div className="eds-page eds-anim-page">{children}</div>
        </main>
      </div>
    </div>
  );
}
