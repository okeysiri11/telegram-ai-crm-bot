/**
 * Sprint 30.8 — Notifications center: inbox, activity, history, read/unread, priority.
 * Extends notificationStore; optionally hydrates from /api/enterprise-comms/v1/center.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import {
  filterByBucket,
  useNotificationStore,
  type AppNotification,
  type NotificationBucket,
} from "@/notifications/notificationStore";
import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";

const TABS = [
  { id: "inbox", label: "Входящие" },
  { id: "activity", label: "Активность" },
  { id: "history", label: "История" },
  { id: "unread", label: "Непрочитанные" },
  { id: "priority", label: "Приоритет" },
] as const;

function priorityScore(n: AppNotification): number {
  if (n.kind === "error" || n.level === "error") return 3;
  if (n.kind === "warning" || n.level === "warning" || n.kind === "alert") return 2;
  if (n.kind === "ai" || n.kind === "task") return 1;
  return 0;
}

export function NotificationsModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "inbox";
  const items = useNotificationStore((s) => s.items);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);
  const push = useNotificationStore((s) => s.push);
  const [source, setSource] = useState("notificationStore");
  const active = TABS.some((t) => t.id === view) ? view : "inbox";

  const hydrate = useCallback(async () => {
    try {
      const res = await apiFetch(`${webConfig.commsPrefix}/center`);
      if (!res.ok) return;
      const json = (await res.json()) as { items?: Array<Record<string, unknown>>; events?: Array<Record<string, unknown>> };
      const list = json.items || json.events || [];
      for (const raw of list.slice(0, 20)) {
        push({
          kind: "system",
          level: "system",
          title: String(raw.title || raw.subject || "Уведомление"),
          body: String(raw.body || raw.message || raw.detail || ""),
        });
      }
      setSource("comms API");
    } catch {
      setSource("notificationStore");
    }
  }, [push]);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  const list = useMemo(() => {
    if (active === "unread") return filterByBucket(items, "unread" as NotificationBucket);
    if (active === "activity") return filterByBucket(items, "jobs" as NotificationBucket).concat(filterByBucket(items, "mentions"));
    if (active === "history") return [...items].filter((n) => n.read);
    if (active === "priority") return [...items].sort((a, b) => priorityScore(b) - priorityScore(a));
    return items;
  }, [items, active]);

  return (
    <BusinessModuleShell
      title="Уведомления"
      subtitle="Центр · входящие · активность · история · приоритет"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source={source}
      testId="notifications-module"
      actions={
        <>
          <Button size="sm" variant="secondary" onClick={() => markAllRead()}>
            Прочитать все
          </Button>
          <Button size="sm" variant="ghost" onClick={() => void hydrate()}>
            Синхронизация
          </Button>
        </>
      }
    >
      <div className="space-y-2">
        {list.map((n) => (
          <Card key={n.id} title={n.title} status={<Badge tone={n.read ? "default" : "warning"}>{n.read ? "прочитано" : "новое"}</Badge>}>
            <p className="eds-type-helper">{n.body}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge>{n.kind}</Badge>
              <span className="eds-type-helper">{new Date(n.createdAt).toLocaleString("ru-RU")}</span>
              {!n.read ? (
                <Button size="sm" variant="ghost" onClick={() => markRead(n.id)}>
                  Прочитано
                </Button>
              ) : null}
            </div>
          </Card>
        ))}
        {!list.length ? <p className="eds-type-helper">Пусто</p> : null}
      </div>
    </BusinessModuleShell>
  );
}
