/**
 * Enterprise Event Bus — Sprint 36.1.
 * Live events, topics, subscribers, DLQ, replay, statistics, traffic.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const EVENT_BUS_API = "/api/event-bus";

type SectionId =
  | "live"
  | "topics"
  | "subscribers"
  | "dlq"
  | "replay"
  | "statistics"
  | "traffic"
  | "inspector";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "live", label: "Live Events" },
  { id: "topics", label: "Topics" },
  { id: "subscribers", label: "Subscribers" },
  { id: "dlq", label: "Dead Letter Queue" },
  { id: "replay", label: "Replay" },
  { id: "statistics", label: "Statistics" },
  { id: "traffic", label: "Traffic Monitor" },
  { id: "inspector", label: "Event Inspector" },
];

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${EVENT_BUS_API}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function EventBusPage() {
  const [section, setSection] = useState<SectionId>("live");
  const [events, setEvents] = useState<Array<Record<string, unknown>>>([]);
  const [topics, setTopics] = useState<Array<Record<string, unknown>>>([]);
  const [subscribers, setSubscribers] = useState<Array<Record<string, unknown>>>([]);
  const [dlq, setDlq] = useState<Array<Record<string, unknown>>>([]);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [traffic, setTraffic] = useState<Record<string, unknown> | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [inspect, setInspect] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [publishType, setPublishType] = useState("demo.ping");
  const [wsStatus, setWsStatus] = useState("disconnected");

  const refresh = useCallback(async () => {
    setError(null);
    const [ev, tp, sub, dead, st, tr] = await Promise.all([
      api<{ events: Array<Record<string, unknown>> }>("/events?limit=50"),
      api<{ topics: Array<Record<string, unknown>> }>("/topics"),
      api<{ subscribers: Array<Record<string, unknown>> }>("/subscribers"),
      api<{ items: Array<Record<string, unknown>> }>("/dead-letter"),
      api<Record<string, unknown>>("/statistics"),
      api<Record<string, unknown>>("/traffic"),
    ]);
    setEvents(ev.events || []);
    setTopics(tp.topics || []);
    setSubscribers(sub.subscribers || []);
    setDlq(dead.items || []);
    setStats(st);
    setTraffic(tr);
    if (!selectedId && ev.events?.length) {
      setSelectedId(String(ev.events[ev.events.length - 1].event_id));
    }
  }, [selectedId]);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/api/event-bus/ws`);
    ws.onopen = () => setWsStatus("connected");
    ws.onclose = () => setWsStatus("disconnected");
    ws.onerror = () => setWsStatus("error");
    ws.onmessage = (msg) => {
      try {
        const payload = JSON.parse(msg.data);
        if (payload.type === "event" && payload.data) {
          setEvents((prev) => [...prev.slice(-99), payload.data]);
        }
      } catch {
        /* ignore */
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    if (section !== "inspector" || !selectedId) return;
    api<Record<string, unknown>>(`/events/${selectedId}`)
      .then(setInspect)
      .catch((e) => setError(String(e.message || e)));
  }, [section, selectedId]);

  async function publishDemo() {
    setBusy(true);
    try {
      await api("/publish", {
        method: "POST",
        body: JSON.stringify({
          event_type: publishType,
          category: "platform",
          topic: "platform",
          source_service: "event_bus_ui",
          priority: "normal",
          payload: { ping: true, at: Date.now() },
        }),
      });
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  async function replaySelected() {
    if (!selectedId) return;
    setBusy(true);
    try {
      await api("/replay", { method: "POST", body: JSON.stringify({ event_id: selectedId }) });
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  async function retryDlq(id: string) {
    setBusy(true);
    try {
      await api("/retry", { method: "POST", body: JSON.stringify({ dlq_id: id }) });
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  }

  const trafficCards = useMemo(() => {
    const t = traffic || {};
    return [
      { label: "events/sec", value: t.events_per_sec ?? 0 },
      { label: "active subscribers", value: t.active_subscribers ?? 0 },
      { label: "queued events", value: t.queued_events ?? 0 },
      { label: "failed events", value: t.failed_events ?? 0 },
      { label: "retry count", value: t.retry_count ?? 0 },
      { label: "latency ms", value: t.latency_ms ?? 0 },
      { label: "throughput", value: t.throughput ?? 0 },
      { label: "memory MB", value: t.memory_usage_mb ?? 0 },
    ];
  }, [traffic]);

  return (
    <PlatformBuilderLayout
      title="Enterprise Event Bus"
      subtitle="Central asynchronous messaging — topics, replay, DLQ, live stream. SoR: PlatformEventBus."
    >
      <div className="flex flex-wrap items-center gap-2">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSection(s.id)}
            className={`rounded-md border px-3 py-1.5 text-xs transition ${
              section === s.id
                ? "border-[var(--eds-primary)] bg-[var(--eds-primary)]/10"
                : "border-[var(--eds-border)] bg-[var(--eds-surface)] text-[var(--eds-text-muted)]"
            }`}
          >
            {s.label}
          </button>
        ))}
        <Badge tone={wsStatus === "connected" ? "success" : "warning"}>WS {wsStatus}</Badge>
        <Button type="button" size="sm" onClick={() => refresh()} disabled={busy}>
          Refresh
        </Button>
      </div>

      {error ? (
        <Card className="border-[var(--eds-danger)]/40 bg-[var(--eds-danger)]/5 p-3 text-sm text-[var(--eds-danger)]">
          {error}
        </Card>
      ) : null}

      {(section === "live" || section === "replay") && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Input value={publishType} onChange={(e) => setPublishType(e.target.value)} className="max-w-xs" />
            <Button type="button" disabled={busy} onClick={publishDemo}>
              Publish
            </Button>
            {section === "replay" ? (
              <Button type="button" disabled={busy || !selectedId} onClick={replaySelected}>
                Replay selected
              </Button>
            ) : null}
          </div>
          <div className="max-h-[480px] space-y-2 overflow-auto">
            {events
              .slice()
              .reverse()
              .map((ev) => (
                <button
                  key={String(ev.event_id)}
                  type="button"
                  className="block w-full rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] p-3 text-left text-xs"
                  onClick={() => {
                    setSelectedId(String(ev.event_id));
                    setSection("inspector");
                  }}
                >
                  <div className="flex flex-wrap gap-2">
                    <Badge>{String(ev.topic)}</Badge>
                    <span className="font-medium">{String(ev.event_type)}</span>
                    <Badge tone="default">{String(ev.priority)}</Badge>
                    <span className="text-[var(--eds-text-muted)]">{String(ev.source_service)}</span>
                    <span className="text-[var(--eds-text-muted)]">{String(ev.event_id)}</span>
                  </div>
                </button>
              ))}
          </div>
        </div>
      )}

      {section === "topics" && (
        <div className="grid gap-3 md:grid-cols-3">
          {topics.map((t) => (
            <Card key={String(t.name)} className="space-y-1 p-4">
              <h3 className="eds-type-h3">{String(t.name)}</h3>
              <p className="text-xs text-[var(--eds-text-muted)]">{String(t.description || "")}</p>
              <p className="text-xs">
                events {String(t.event_count)} · subscribers {String(t.subscriber_count)}
              </p>
            </Card>
          ))}
        </div>
      )}

      {section === "subscribers" && (
        <Card className="space-y-2 p-4">
          {subscribers.length === 0 ? (
            <p className="text-sm text-[var(--eds-text-muted)]">No active subscriptions.</p>
          ) : (
            subscribers.map((s) => (
              <div key={String(s.subscription_id)} className="border-b border-[var(--eds-border)] py-2 text-xs">
                <div className="flex flex-wrap gap-2">
                  <Badge>{String(s.subscriber_id)}</Badge>
                  <span>{String(s.topic || "*")}</span>
                  <span>{String(s.event_type || s.wildcard || s.regex || "*")}</span>
                  <Badge tone={s.active ? "success" : "warning"}>{s.active ? "active" : "inactive"}</Badge>
                </div>
              </div>
            ))
          )}
        </Card>
      )}

      {section === "dlq" && (
        <Card className="space-y-2 p-4">
          {dlq.length === 0 ? (
            <p className="text-sm text-[var(--eds-text-muted)]">Dead letter queue is empty.</p>
          ) : (
            dlq
              .slice()
              .reverse()
              .map((item) => (
                <div key={String(item.dlq_id)} className="flex items-center justify-between border-b border-[var(--eds-border)] py-2 text-xs">
                  <div>
                    <p className="font-medium">{String(item.dlq_id)}</p>
                    <p className="text-[var(--eds-text-muted)]">{String(item.reason)}</p>
                  </div>
                  <Button type="button" size="sm" disabled={busy || Boolean(item.retried)} onClick={() => retryDlq(String(item.dlq_id))}>
                    Retry
                  </Button>
                </div>
              ))
          )}
        </Card>
      )}

      {section === "statistics" && stats && (
        <Card className="space-y-3 p-4">
          <p className="text-sm">Total stored events: {String(stats.total)}</p>
          <pre className="overflow-auto rounded-md bg-[var(--eds-surface)] p-3 text-xs">
            {JSON.stringify(stats, null, 2)}
          </pre>
        </Card>
      )}

      {section === "traffic" && (
        <div className="grid gap-3 md:grid-cols-4">
          {trafficCards.map((c) => (
            <Card key={c.label} className="p-4">
              <p className="eds-type-caption text-[var(--eds-text-muted)]">{c.label}</p>
              <p className="eds-type-h2">{String(c.value)}</p>
            </Card>
          ))}
        </div>
      )}

      {section === "inspector" && (
        <Card className="space-y-3 p-4">
          <h3 className="eds-type-h3">Event Inspector — {selectedId || "—"}</h3>
          {inspect ? (
            <pre className="max-h-[520px] overflow-auto rounded-md bg-[var(--eds-surface)] p-3 text-xs">
              {JSON.stringify(inspect, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-[var(--eds-text-muted)]">Select an event from Live Events.</p>
          )}
        </Card>
      )}
    </PlatformBuilderLayout>
  );
}

export default EventBusPage;
