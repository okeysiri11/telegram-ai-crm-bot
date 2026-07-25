import { applicationRegistry } from "./applicationRegistry";
import { workspaceFederation } from "./workspaceFederation";
import { navigationHistory } from "./navigationHistory";

export type QuickSwitchTarget = "applications" | "dashboards" | "workspaces" | "ai_chats" | "documents";

type SwitchItem = { id: string; label: string; route: string };

let cursor = 0;
let target: QuickSwitchTarget = "applications";

function pool(t: QuickSwitchTarget): SwitchItem[] {
  if (t === "applications") {
    return applicationRegistry.list().slice(0, 8).map((a) => ({ id: a.id, label: a.name, route: a.route }));
  }
  if (t === "workspaces") {
    return workspaceFederation.list().map((w) => ({ id: w.id, label: w.name, route: w.route }));
  }
  if (t === "dashboards") {
    return [{ id: "dash_main", label: "Personal Dashboard", route: "/workspace/dashboards" }];
  }
  if (t === "ai_chats") {
    return [{ id: "ai_ops", label: "Ops Copilot", route: "/workspace/ai" }];
  }
  return [{ id: "doc_sec", label: "Security Policy", route: "/workspace/docs/security" }];
}

export const quickSwitcher = {
  targets(): QuickSwitchTarget[] {
    return ["applications", "dashboards", "workspaces", "ai_chats", "documents"];
  },
  setTarget(t: QuickSwitchTarget) {
    target = t;
    cursor = 0;
  },
  currentTarget(): QuickSwitchTarget {
    return target;
  },
  step(delta = 1): SwitchItem {
    const items = pool(target);
    cursor = (cursor + delta + items.length) % items.length;
    const selected = items[cursor]!;
    navigationHistory.push({ kind: "page", label: selected.label, path: selected.route });
    return selected;
  },
  list(): SwitchItem[] {
    return pool(target);
  },
};
