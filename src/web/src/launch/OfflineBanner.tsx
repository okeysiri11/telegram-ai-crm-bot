/**
 * Offline / reconnect banner — Sprint 32.3.7 / EP-07.
 * Lightweight UX only; no service worker / new engine.
 */

import { useEffect, useState } from "react";
import { Button } from "@/ui";
import { liveUpdates } from "../../workspace/realtime/liveUpdates";
import { reliabilityCopy } from "@/production";
import { telemetry } from "@/integrations/telemetry";

export function OfflineBanner() {
  const [online, setOnline] = useState(typeof navigator === "undefined" ? true : navigator.onLine);

  useEffect(() => {
    let hadOffline = !navigator.onLine;
    const on = () => {
      setOnline(true);
      if (hadOffline) {
        liveUpdates.publish("poll");
        void telemetry.log({ kind: "application", message: "network_online_resume" });
      }
      hadOffline = false;
    };
    const off = () => {
      setOnline(false);
      hadOffline = true;
      void telemetry.log({ kind: "application", message: "network_offline" });
    };
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  if (online) return null;

  const copy = reliabilityCopy("offline");

  return (
    <div className="launch-offline edm-notify-enter" role="alert">
      <div>
        <p className="font-medium">{copy.title}</p>
        <p className="eds-type-small text-[var(--eds-text-muted)]">{copy.happened}</p>
        <p className="eds-type-helper">{copy.action}</p>
        <p className="eds-type-helper">{copy.auto}</p>
      </div>
      <Button
        size="sm"
        variant="secondary"
        onClick={() => {
          if (navigator.onLine) {
            liveUpdates.publish("poll");
            setOnline(true);
          } else {
            window.location.reload();
          }
        }}
      >
        Retry connection
      </Button>
    </div>
  );
}
