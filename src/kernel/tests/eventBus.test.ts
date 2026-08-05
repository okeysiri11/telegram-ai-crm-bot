import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import {
  createEventBus,
  EventBus,
  Event,
  EventFilter,
  EventHistory,
  StandardEventTypes,
  resetSequenceForTests,
} from "../event_bus/index.js";
import { createKernel } from "../Kernel.js";
import type { ADOSEvent } from "../event_bus/types.js";

describe("Event", () => {
  beforeEach(() => resetSequenceForTests());

  it("creates immutable events with sequence", () => {
    const a = Event.create({ type: StandardEventTypes.TaskCreated, payload: { id: 1 } });
    const b = Event.create({ type: StandardEventTypes.TaskAssigned, mode: "sync" });
    expect(a.sequence).toBe(1);
    expect(b.sequence).toBe(2);
    expect(a.type).toBe("TaskCreated");
  });

  it("requires delayMs for delayed mode", () => {
    expect(() =>
      Event.create({ type: "X", mode: "delayed" }),
    ).toThrow(/delayMs/);
  });
});

describe("EventFilter", () => {
  it("matches wildcards", () => {
    expect(EventFilter.matchesWildcard("Task*", "TaskCreated")).toBe(true);
    expect(EventFilter.matchesWildcard("Task*", "AgentStarted")).toBe(false);
    expect(EventFilter.matchesWildcard("*", "Anything")).toBe(true);
  });
});

describe("EventHistory", () => {
  it("ring-buffers at capacity", () => {
    const history = new EventHistory(3);
    for (let i = 0; i < 5; i += 1) {
      history.append(
        Event.create({ type: "E", payload: i, mode: "sync" }),
      );
    }
    expect(history.length).toBe(3);
    expect(history.totalPublished).toBe(5);
    const list = history.list();
    expect(list.map((e) => e.payload)).toEqual([2, 3, 4]);
  });
});

describe("Enterprise EventBus", () => {
  let bus: EventBus;

  beforeEach(() => {
    resetSequenceForTests();
    bus = createEventBus({ history: { capacity: 1000 } });
  });

  afterEach(async () => {
    await bus.dispose();
  });

  it("publish / subscribe works (sync)", async () => {
    const seen: ADOSEvent[] = [];
    bus.subscribe(StandardEventTypes.TaskCreated, (e) => {
      seen.push(e);
    });
    await bus.publish({
      type: StandardEventTypes.TaskCreated,
      payload: { taskId: "t1" },
      mode: "sync",
    });
    expect(seen).toHaveLength(1);
    expect(seen[0]?.payload).toEqual({ taskId: "t1" });
  });

  it("unsubscribe stops delivery", async () => {
    let count = 0;
    const sub = bus.subscribe("Ping", () => {
      count += 1;
    });
    await bus.publish({ type: "Ping", mode: "sync" });
    sub.unsubscribe();
    await bus.publish({ type: "Ping", mode: "sync" });
    expect(count).toBe(1);
  });

  it("once() delivers a single time", async () => {
    let count = 0;
    bus.once("OnceEvt", () => {
      count += 1;
    });
    await bus.publish({ type: "OnceEvt", mode: "sync" });
    await bus.publish({ type: "OnceEvt", mode: "sync" });
    expect(count).toBe(1);
  });

  it("priority orders handlers (higher first)", async () => {
    const order: number[] = [];
    bus.subscribe("P", () => order.push(1), { priority: 1 });
    bus.subscribe("P", () => order.push(10), { priority: 10 });
    bus.subscribe("P", () => order.push(5), { priority: 5 });
    await bus.publish({ type: "P", mode: "sync" });
    expect(order).toEqual([10, 5, 1]);
  });

  it("wildcard subscriptions match", async () => {
    const types: string[] = [];
    bus.subscribe("Task*", (e) => types.push(e.type));
    await bus.publish({ type: "TaskStarted", mode: "sync" });
    await bus.publish({ type: "TaskFailed", mode: "sync" });
    await bus.publish({ type: "AgentStarted", mode: "sync" });
    expect(types).toEqual(["TaskStarted", "TaskFailed"]);
  });

  it("sticky events deliver to late subscribers", async () => {
    await bus.publish({
      type: "ProviderConnected",
      sticky: true,
      mode: "sync",
      payload: { id: "openai" },
    });
    let got: unknown;
    bus.subscribe("ProviderConnected", (e) => {
      got = e.payload;
    });
    expect(got).toEqual({ id: "openai" });
  });

  it("history and replay work", async () => {
    await bus.publish({ type: "A", mode: "sync", payload: 1 });
    await bus.publish({ type: "B", mode: "sync", payload: 2 });
    expect(bus.getHistory()).toHaveLength(2);

    const replayed: string[] = [];
    bus.subscribe("*", (e) => replayed.push(e.type));
    const n = await bus.replay({ filter: { types: ["A", "B"] } });
    expect(n).toBe(2);
    expect(replayed).toEqual(["A", "B"]);
  });

  it("event filtering on subscribe", async () => {
    const seen: unknown[] = [];
    bus.subscribe(
      "TaskCompleted",
      (e) => seen.push(e.payload),
      {
        filter: (e) => (e.payload as { ok?: boolean }).ok === true,
      },
    );
    await bus.publish({
      type: "TaskCompleted",
      mode: "sync",
      payload: { ok: false },
    });
    await bus.publish({
      type: "TaskCompleted",
      mode: "sync",
      payload: { ok: true },
    });
    expect(seen).toEqual([{ ok: true }]);
  });

  it("delayed events fire after timeout", async () => {
    vi.useFakeTimers();
    try {
      const seen: string[] = [];
      bus.subscribe("Delayed", (e) => seen.push(e.type));
      await bus.publish({
        type: "Delayed",
        mode: "delayed",
        delayMs: 1000,
      });
      expect(seen).toEqual([]);
      await vi.advanceTimersByTimeAsync(1000);
      await Promise.resolve();
      await Promise.resolve();
      expect(seen).toEqual(["Delayed"]);
    } finally {
      vi.useRealTimers();
    }
  });

  it("async mode schedules without requiring handler completion before publish returns", async () => {
    let released!: () => void;
    const gate = new Promise<void>((r) => {
      released = r;
    });
    let started = false;
    bus.subscribe("AsyncEvt", async () => {
      started = true;
      await gate;
    });
    await bus.publish({ type: "AsyncEvt", mode: "async" });
    await Promise.resolve();
    await Promise.resolve();
    expect(started).toBe(true);
    released();
  });

  it("broadcast notifies additional subscribers", async () => {
    const types: string[] = [];
    bus.subscribe("Other", (e) => types.push(`other:${e.type}`));
    bus.subscribe("News", (e) => types.push(`news:${e.type}`));
    await bus.broadcast({ type: "News", mode: "sync", payload: true });
    expect(types).toContain("news:News");
    expect(types).toContain("other:News");
  });

  it("registers standard event types", () => {
    expect(bus.registry.exists(StandardEventTypes.SecurityAlert)).toBe(true);
    expect(bus.registry.exists(StandardEventTypes.SystemShutdown)).toBe(true);
    expect(bus.registry.exists(StandardEventTypes.KnowledgeUpdated)).toBe(true);
  });
});

describe("Kernel + Enterprise Event Bus", () => {
  it("BootCompleted flows through enterprise bus", async () => {
    const kernel = createKernel({ config: { environment: "test" } });
    let enterpriseSaw = false;
    kernel.enterpriseEventBus.subscribe("BootCompleted", () => {
      enterpriseSaw = true;
    });
    let typedSaw = false;
    kernel.eventBus.subscribe("BootCompleted", () => {
      typedSaw = true;
    });
    await kernel.start();
    expect(typedSaw).toBe(true);
    expect(enterpriseSaw).toBe(true);
    await kernel.dispose();
  });
});
