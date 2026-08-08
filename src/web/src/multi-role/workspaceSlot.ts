/**
 * Sprint 42.1 — workspace slot + scoped localStorage keys.
 * Parallel ports (3000–3003+) isolate sessions by origin; slot prefix
 * also isolates when VITE_WORKSPACE_SLOT is set.
 */

export const WORKSPACE_PORT_SLOTS: Record<string, string> = {
  "3000": "owner",
  "3001": "travel",
  "3002": "crypto",
  "3003": "build",
  "3004": "drone",
  "3005": "auto",
  "3006": "legal",
  "3007": "agro",
  "3008": "seller",
};

export type WorkspaceSlotId =
  | "default"
  | "owner"
  | "travel"
  | "crypto"
  | "build"
  | "drone"
  | "auto"
  | "legal"
  | "agro"
  | "seller"
  | string;

export function getWorkspaceSlot(): WorkspaceSlotId {
  try {
    const env = (import.meta as ImportMeta & { env?: Record<string, string> }).env?.VITE_WORKSPACE_SLOT;
    if (env && String(env).trim()) return String(env).trim();
  } catch {
    /* ignore */
  }
  if (typeof window !== "undefined") {
    const port = window.location.port;
    if (port && WORKSPACE_PORT_SLOTS[port]) return WORKSPACE_PORT_SLOTS[port]!;
  }
  return "default";
}

/** Prefix storage keys when not on the default (5180) workspace. */
export function wsKey(base: string): string {
  const slot = getWorkspaceSlot();
  if (!slot || slot === "default") return base;
  return `ews_ws_${slot}__${base}`;
}

export function workspaceSlotLabel(slot: WorkspaceSlotId = getWorkspaceSlot()): string {
  const labels: Record<string, string> = {
    default: "Default",
    owner: "Owner",
    travel: "Travel Agency",
    crypto: "Crypto OTC",
    build: "Construction",
    drone: "Drone Company",
    auto: "Auto Dealer",
    legal: "Law Office",
    agro: "Agro Company",
    seller: "Marketplace Seller",
  };
  return labels[slot] || slot;
}
