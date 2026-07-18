import type { RealtimeMessage } from '../types/api';

export type RealtimeStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

type MessageHandler = (msg: RealtimeMessage) => void;
type StatusHandler = (status: RealtimeStatus) => void;

const REALTIME_PATH =
  import.meta.env.VITE_REALTIME_PATH || '/management/realtime/ws';

const DEFAULT_CHANNELS = [
  'dashboard',
  'system',
  'requests',
  'managers',
  'workflows',
  'notifications',
  'health',
];

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempt = 0;
  private messageHandlers = new Set<MessageHandler>();
  private statusHandlers = new Set<StatusHandler>();
  private subscribedChannels = new Set<string>(DEFAULT_CHANNELS);
  private intentionalClose = false;

  get status(): RealtimeStatus {
    if (!this.ws) return 'disconnected';
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      default:
        return 'disconnected';
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onStatus(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    handler(this.status);
    return () => this.statusHandlers.delete(handler);
  }

  connect(): void {
    this.intentionalClose = false;
    this.emitStatus('connecting');

    const actorId = localStorage.getItem('actor_telegram_id');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_WS_HOST || window.location.host;
    const params = new URLSearchParams();
    if (actorId) params.set('actor_telegram_id', actorId);

    const url = `${protocol}//${host}${REALTIME_PATH}?${params.toString()}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.emitStatus('connected');
      this.subscribe([...this.subscribedChannels]);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string) as RealtimeMessage;
        if (msg.type === 'ping') {
          this.send({ type: 'pong', timestamp: msg.timestamp });
          return;
        }
        this.messageHandlers.forEach((h) => h(msg));
      } catch {
        /* ignore malformed */
      }
    };

    this.ws.onclose = (event) => {
      this.emitStatus('disconnected');
      if (!this.intentionalClose && event.code === 4000) {
        this.scheduleReconnect();
      } else if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => this.emitStatus('error');
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
    this.emitStatus('disconnected');
  }

  subscribe(channels: string[]): void {
    channels.forEach((c) => this.subscribedChannels.add(c));
    this.send({ type: 'subscribe', channels });
  }

  unsubscribe(channels: string[]): void {
    channels.forEach((c) => this.subscribedChannels.delete(c));
    this.send({ type: 'unsubscribe', channels });
  }

  private send(payload: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  private scheduleReconnect(): void {
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, 30000);
    this.reconnectAttempt += 1;
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }

  private emitStatus(status: RealtimeStatus): void {
    this.statusHandlers.forEach((h) => h(status));
  }
}

export const realtimeClient = new RealtimeClient();
