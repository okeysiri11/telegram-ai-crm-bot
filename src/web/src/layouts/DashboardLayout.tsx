import type { ReactNode } from "react";
import { FullLayout } from "./FullLayout";

export function DashboardLayout({ children }: { children: ReactNode }) {
  return <FullLayout>{children}</FullLayout>;
}
