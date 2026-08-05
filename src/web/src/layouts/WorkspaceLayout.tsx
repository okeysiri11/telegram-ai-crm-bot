import type { ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { FullLayout } from "./FullLayout";

/**
 * Workspace shell — Sprint 32.3.6 / 27.7 embed mode for Desktop windows.
 * Chrome (context + quick switch) lives in FullLayout for all pages.
 * When ?embed=1 (or embed prop), render page content only — no double shell.
 */
export function WorkspaceLayout({
  children,
  embed,
}: {
  children: ReactNode;
  embed?: boolean;
}) {
  const [params] = useSearchParams();
  const isEmbed = embed === true || params.get("embed") === "1";
  if (isEmbed) {
    return <div className="edt-embed-root">{children}</div>;
  }
  return <FullLayout>{children}</FullLayout>;
}
