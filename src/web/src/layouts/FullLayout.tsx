import type { ReactNode } from "react";
import { Sidebar } from "@/navigation/Sidebar";
import { TopNavigation } from "@/navigation/TopNavigation";

export function FullLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopNavigation />
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
