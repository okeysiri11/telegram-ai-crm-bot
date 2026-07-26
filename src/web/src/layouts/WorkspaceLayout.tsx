import type { ReactNode } from "react";
import { FullLayout } from "./FullLayout";

/**
 * Workspace shell — Sprint 32.3.6.
 * Chrome (context + quick switch) lives in FullLayout for all pages.
 */
export function WorkspaceLayout({ children }: { children: ReactNode }) {
  return <FullLayout>{children}</FullLayout>;
}
