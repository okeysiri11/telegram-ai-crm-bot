import type { ReactNode } from "react";
import { FullLayout } from "./FullLayout";
import { useWorkspaceStore } from "@/workspace/workspaceStore";
import { Badge } from "@/ui";

export function WorkspaceLayout({ children }: { children: ReactNode }) {
  const ws = useWorkspaceStore((s) => s.workspace);
  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap gap-2 text-sm">
        <Badge>{ws.company}</Badge>
        <Badge>{ws.department}</Badge>
        <Badge>{ws.project}</Badge>
      </div>
      {children}
    </FullLayout>
  );
}
