import { getSocket } from "@/integrations/socket";
import { widgetManager } from "../managers";

export type LiveUpdate = {
  source: "websocket" | "event_bus" | "notification_center" | "poll";
  widgetIds: string[];
  at: string;
};

type Listener = (update: LiveUpdate) => void;
const listeners = new Set<Listener>();

export const liveUpdates = {
  sources: ["websocket", "event_bus", "notification_center", "live_dashboard_refresh"] as const,
  subscribe(listener: Listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  publish(source: LiveUpdate["source"] = "poll") {
    const update: LiveUpdate = {
      source,
      widgetIds: widgetManager.refreshRealtime(),
      at: new Date().toISOString(),
    };
    listeners.forEach((l) => l(update));
    return update;
  },
  connect() {
    const socket = getSocket();
    if (!socket) return { connected: false, reason: "socket_url_unset" };
    if (!socket.connected) socket.connect();
    socket.on("workspace:refresh", () => this.publish("websocket"));
    socket.on("event_bus:message", () => this.publish("event_bus"));
    socket.on("notifications:new", () => this.publish("notification_center"));
    return { connected: true };
  },
};
