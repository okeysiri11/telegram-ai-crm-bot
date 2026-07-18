import { describe, it, expect, vi } from 'vitest';
import { RealtimeClient } from '../services/realtime';

class MockWebSocket {
  static OPEN = 1;
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: ((ev: { code: number }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0;
  sent: string[] = [];

  constructor(_url: string) {
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      this.readyState = 1;
      this.onopen?.();
    }, 0);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = 3;
    this.onclose?.({ code: 1000 });
  }
}

describe('RealtimeClient', () => {
  it('connects and responds to ping with pong', async () => {
    vi.stubGlobal('WebSocket', MockWebSocket);
    localStorage.setItem('actor_telegram_id', '42');

    const client = new RealtimeClient();
    const statuses: string[] = [];
    client.onStatus((s) => statuses.push(s));
    client.connect();

    await new Promise((r) => setTimeout(r, 10));
    expect(statuses).toContain('connected');

    const ws = MockWebSocket.instances.at(-1)!;
    ws.onmessage?.({
      data: JSON.stringify({ type: 'ping', timestamp: '2026-01-01T00:00:00Z' }),
    });

    expect(ws.sent.some((s) => s.includes('"type":"pong"'))).toBe(true);
    client.disconnect();
    vi.unstubAllGlobals();
  });
});
