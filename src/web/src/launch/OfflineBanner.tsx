/**
 * Offline / reconnect banner — Sprint 32.3.7.
 * Lightweight UX only; no service worker / new engine.
 */

import { useEffect, useState } from "react";
import { Button } from "@/ui";

export function OfflineBanner() {
  const [online, setOnline] = useState(
    typeof navigator === "undefined" ? true : navigator.onLine,
  );

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  if (online) return null;

  return (
    <div className="launch-offline eds-anim-slide" role="alert">
      <div>
        <p className="font-medium">Нет соединения</p>
        <p className="eds-type-small text-[var(--eds-text-muted)]">
          Offline / timeout — данные могут быть устаревшими. Проверьте сеть и обновите.
        </p>
      </div>
      <Button size="sm" variant="secondary" onClick={() => window.location.reload()}>
        Retry
      </Button>
    </div>
  );
}
