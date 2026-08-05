/**
 * Health React binding — Sprint 28.1.
 * Subscribes to Health Service singleton (no polling).
 */

import { useEffect, useState } from "react";
import { healthService } from "./healthService";
import type { HealthLevel, RuntimeHealthItem } from "./types";
import type { StatusItemId, StatusSnapshot } from "@/shell/enterprise/statusCatalog";
import { STATUS_PROBES } from "@/shell/enterprise/statusCatalog";

/** Subscribe to singleton health — no per-component polling. */
export function useRuntimeHealth(_intervalMs?: number) {
  const [items, setItems] = useState<RuntimeHealthItem[]>(() => healthService.getItems());
  const [updatedAt, setUpdatedAt] = useState<string | null>(() => healthService.getUpdatedAt());
  const [level, setLevel] = useState<HealthLevel>(() => healthService.getLevel());

  useEffect(() => {
    return healthService.subscribe((next, nextLevel, at) => {
      setItems(next);
      setLevel(nextLevel);
      setUpdatedAt(at);
    });
  }, []);

  return {
    items,
    updatedAt,
    level,
    refresh: () => healthService.refresh(),
  };
}

export function toStatusSnapshots(items: RuntimeHealthItem[]): StatusSnapshot[] {
  return items
    .filter((i): i is RuntimeHealthItem & { id: StatusItemId } =>
      STATUS_PROBES.some((p) => p.id === i.id),
    )
    .map((i) => ({ id: i.id, label: i.label, tone: i.tone, detail: i.detail }));
}
