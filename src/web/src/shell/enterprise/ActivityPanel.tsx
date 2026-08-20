/**
 * Sprint 42.2 — Activity panel: Expanded · Compact · Hidden (no manual resize).
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useNotificationStore } from "@/notifications/notificationStore";
import { Badge, Button } from "@/ui";
import {
  ACTIVITY_TABS,
  SHELL_ACTIVITY_SEED,
  type ActivityTabId,
} from "./activityCatalog";
import { buildActivityTimeline } from "./activityTimeline";
import { useI18n } from "@/i18n";
import { useAdaptiveShellStore } from "./adaptiveShellStore";
import { cn } from "@/utils/cn";

function relTime(iso: string, justNow: string) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60_000));
  if (mins < 1) return justNow;
  if (mins < 60) return `${mins}м`;
  const h = Math.round(mins / 60);
  return `${h}ч`;
}

export function ActivityPanel() {
  const t = useI18n((s) => s.t);
  const mode = useAdaptiveShellStore((s) => s.activityMode);
  const setActivityMode = useAdaptiveShellStore((s) => s.setActivityMode);
  const cycleActivity = useAdaptiveShellStore((s) => s.cycleActivity);
  const notifications = useNotificationStore((s) => s.items);
  const [tab, setTab] = useState<ActivityTabId>("notifications");
  const [pinned, setPinned] = useState(false);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const clientTabs = useMemo(
    () => ACTIVITY_TABS.filter((x) => ["notifications", "recent", "ai", "system"].includes(x.id)),
    [],
  );

  useEffect(() => {
    if (mode === "hidden" || pinned) return;

    function onKey(e: KeyboardEvent) {
      if (e.key !== "Escape") return;
      setActivityMode("hidden");
    }

    function onPointer(e: MouseEvent) {
      const el = panelRef.current;
      if (!el) return;
      if (el.contains(e.target as Node)) return;
      const target = e.target as HTMLElement | null;
      if (target?.closest?.("[data-testid='enterprise-toolbar']")) return;
      setActivityMode("hidden");
    }

    window.addEventListener("keydown", onKey);
    const timer = window.setTimeout(() => window.addEventListener("mousedown", onPointer), 0);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [mode, pinned, setActivityMode]);

  const entries = useMemo(() => {
    if (tab === "notifications") {
      const fromStore = notifications.slice(0, mode === "compact" ? 5 : 12).map((n) => ({
        id: n.id,
        title: n.title || t("nav.notifications"),
        detail: n.body || "",
        at: n.createdAt || new Date().toISOString(),
        tone: (n.read ? "info" : "warn") as "info" | "warn" | "ok",
      }));
      if (fromStore.length) return fromStore;
      return [];
    }
    if (tab === "recent") {
      const timeline = buildActivityTimeline(mode === "compact" ? 6 : 16).map((e) => ({
        id: e.id,
        title: e.title,
        detail: e.detail,
        at: e.at,
        tone: (e.kind === "error" ? "warn" : e.kind === "ai" ? "ok" : "info") as
          | "info"
          | "warn"
          | "ok",
      }));
      if (timeline.length) return timeline;
      return [];
    }
    if (import.meta.env.DEV && import.meta.env.VITE_DEBUG_NOTIFICATIONS === "true") {
      return SHELL_ACTIVITY_SEED.filter((e) => e.tab === tab).slice(0, mode === "compact" ? 4 : 12);
    }
    return [];
  }, [tab, notifications, t, mode]);

  if (mode === "hidden") return null;

  return (
    <div
      ref={panelRef}
      className={cn(
        "ews-activity-host ews-activity-panel ews-activity--anim ews-glass",
        mode === "compact" && "ews-activity-panel--compact",
        mode === "expanded" && "ews-activity-panel--expanded",
      )}
      data-mode={mode}
      data-testid="activity-panel"
      aria-label={t("activity.title")}
    >
      <div className="ews-dock-head">
        <div>
          <p className="eds-type-section">{t("activity.title")}</p>
          {mode === "expanded" ? <p className="eds-type-helper">{t("activity.subtitle")}</p> : null}
        </div>
        <div className="ews-dock-actions">
          <Button
            size="sm"
            variant="ghost"
            aria-pressed={pinned}
            onClick={() => setPinned((v) => !v)}
            aria-label={pinned ? t("iface.panel.unpin") : t("iface.panel.pin")}
          >
            {pinned ? t("dock.pinned") : t("dock.pin")}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => cycleActivity()}
            aria-label={t("shell.activity.cycle")}
            data-testid="activity-cycle"
            title={t("shell.activity.cycle")}
          >
            {mode === "expanded" ? "▸" : "◂"}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setActivityMode("hidden")}
            aria-label={t("shell.activity.hide")}
          >
            ×
          </Button>
        </div>
      </div>

      {mode === "expanded" ? (
        <div className="ews-activity-tabs" role="tablist">
          {clientTabs.map((tabDef) => (
            <button
              key={tabDef.id}
              type="button"
              role="tab"
              aria-selected={tab === tabDef.id}
              className={tab === tabDef.id ? "is-active" : undefined}
              onClick={() => setTab(tabDef.id)}
            >
              {t(tabDef.labelKey)}
            </button>
          ))}
        </div>
      ) : null}

      <ul className="ews-activity-list">
        {entries.map((e) => (
          <li key={e.id} className="ews-activity-item">
            <span className={`ews-dot ews-dot--${e.tone || "info"}`} aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="ews-activity-title">{e.title}</p>
              {mode === "expanded" ? <p className="eds-type-helper truncate">{e.detail}</p> : null}
              <p className="eds-type-helper text-[var(--eds-text-muted)]">
                {relTime(e.at, t("activity.justNow"))}
              </p>
            </div>
            {mode === "expanded" ? (
              <Badge tone={e.tone === "warn" ? "warning" : e.tone === "ok" ? "success" : "info"}>
                {t(`activity.tone.${e.tone || "info"}` as "activity.tone.info")}
              </Badge>
            ) : null}
          </li>
        ))}
      </ul>
      <div className="mt-3 px-1">
        <Link className="eds-type-caption text-[var(--eds-accent)]" to="/notifications">
          {t("nav.notifications")} →
        </Link>
      </div>
    </div>
  );
}
