import { useEffect, useRef, useState } from "react";
import { RUNTIME_WS } from "../services/runtimeApi";

export type WsStatus = "connecting" | "open" | "closed" | "error";

export interface RuntimeWsMessage {
  type: string;
  payload?: unknown;
  version?: string;
  status?: string;
}

export function useRuntimeSocket(enabled = true) {
  const [status, setStatus] = useState<WsStatus>("closed");
  const [lastMessage, setLastMessage] = useState<RuntimeWsMessage | null>(null);
  const [events, setEvents] = useState<RuntimeWsMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let stopped = false;
    let retry: ReturnType<typeof setTimeout> | undefined;

    const connect = () => {
      setStatus("connecting");
      const ws = new WebSocket(RUNTIME_WS);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!stopped) setStatus("open");
        ws.send("ping");
      };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(String(ev.data)) as RuntimeWsMessage;
          setLastMessage(msg);
          if (
            msg.type === "event" ||
            msg.type === "status" ||
            String(msg.type).startsWith("provider.") ||
            String(msg.type).startsWith("agent.") ||
            String(msg.type).startsWith("workflow.")
          ) {
            setEvents((prev) => [msg, ...prev].slice(0, 200));
          }
        } catch {
          /* ignore non-json */
        }
      };
      ws.onerror = () => {
        if (!stopped) setStatus("error");
      };
      ws.onclose = () => {
        if (stopped) return;
        setStatus("closed");
        retry = setTimeout(connect, 2000);
      };
    };

    connect();
    return () => {
      stopped = true;
      if (retry) clearTimeout(retry);
      wsRef.current?.close();
    };
  }, [enabled]);

  return { status, lastMessage, events };
}
