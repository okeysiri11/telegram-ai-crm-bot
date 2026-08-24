/**
 * AUTO 1.8.5 — admin/settings runtime status. Not shown on operational Auto screens.
 */

import { useEffect, useState } from "react";
import { Card } from "@/ui";
import { autoOpsGet } from "../business-ops/opsApi";

type Rec = Record<string, unknown>;

type Probe = {
  frontend: "online" | "offline";
  api: "online" | "offline";
  database: "online" | "offline";
  telegram: "online" | "offline";
  environment: string;
  version: string;
};

const VERSION = "AUTO 1.8.5";

function asOnline(flag: unknown): "online" | "offline" {
  return flag ? "online" : "offline";
}

export function AutoSystemStatus({ headers }: { headers: Record<string, string> }) {
  const [probe, setProbe] = useState<Probe>({
    frontend: typeof navigator === "undefined" || navigator.onLine ? "online" : "offline",
    api: "offline",
    database: "offline",
    telegram: "offline",
    environment: import.meta.env.MODE === "production" ? "production" : "development",
    version: VERSION,
  });

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const [ops, root, db] = await Promise.all([
        autoOpsGet("/health", headers),
        fetch("/health", { credentials: "include" })
          .then(async (res) => ({ ok: res.ok, json: (await res.json().catch(() => ({}))) as Rec }))
          .catch(() => ({ ok: false, json: {} as Rec })),
        fetch("/system/db-health", { credentials: "include" })
          .then(async (res) => ({ ok: res.ok, json: (await res.json().catch(() => ({}))) as Rec }))
          .catch(() => ({ ok: false, json: {} as Rec })),
      ]);
      if (cancelled) return;
      const opsJson = (ops.json || {}) as Rec;
      const telegram = (opsJson.telegram || {}) as Rec;
      const dbFromOps = (opsJson.database || {}) as Rec;
      const env =
        String(opsJson.environment || import.meta.env.MODE || "development").toLowerCase() === "production"
          ? "production"
          : "development";
      setProbe({
        frontend: typeof navigator === "undefined" || navigator.onLine ? "online" : "offline",
        api: ops.ok || root.ok ? "online" : "offline",
        database: asOnline(db.ok || dbFromOps.online || db.json.ok),
        telegram: asOnline(
          telegram.status === "live" || telegram.implemented === true || telegram.online === true,
        ),
        environment: env,
        version: String(opsJson.sprint || VERSION).replace("AUTO_", "AUTO "),
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [headers]);

  const row = (label: string, value: string, testId: string) => (
    <p data-testid={testId}>
      {label}: <strong>{value}</strong>
    </p>
  );

  return (
    <Card title="Состояние системы">
      <div className="space-y-1 eds-type-small" data-testid="auto-system-status">
        {row("Frontend", probe.frontend, "auto-status-frontend")}
        {row("API", probe.api, "auto-status-api")}
        {row("Database", probe.database, "auto-status-database")}
        {row("Telegram", probe.telegram, "auto-status-telegram")}
        {row("Environment", probe.environment, "auto-status-environment")}
        {row("Version", probe.version, "auto-status-version")}
      </div>
    </Card>
  );
}
