import { describe, expect, it, beforeEach } from "vitest";
import { createAiOrchestrator } from "@ados/orchestrator";
import { createProviderGateway } from "@ados/providers";
import {
  createChatBridge,
  createPromptParser,
  createChatBridgeService,
  CHAT_BRIDGE_SERVICE_ID,
} from "../index.js";

describe("PromptParser", () => {
  const parser = createPromptParser();

  it("classifies architecture prompts", () => {
    const p = parser.parse("Design the system architecture for CRM modules");
    expect(p.kind).toBe("architecture");
    expect(p.preferredAgent).toBe("agent.architect");
  });

  it("classifies bug fixes", () => {
    const p = parser.parse("Fix null reference crash in login");
    expect(p.kind).toBe("bugfix");
  });

  it("extracts file paths", () => {
    const p = parser.parse("Update src/kernel/main.ts and platform_console/src/App.tsx");
    expect(p.files.length).toBeGreaterThan(0);
  });
});

describe("ChatBridge", () => {
  const orch = createAiOrchestrator();
  const gateway = createProviderGateway();

  beforeEach(async () => {
    orch.registry.clear();
    orch.stop();
    gateway.registry.clear();
    gateway.stop();
    orch.start(true);
    gateway.start(true);
    await gateway.connect();
  });

  it("ingests ChatGPT prompt into queued task with context", () => {
    const bridge = createChatBridge({ orchestrator: orch, gateway });
    const task = bridge.createTask({
      prompt: "Implement a feature to export workflow timeline as JSON",
      autoRun: false,
    });
    expect(task.status).toBe("Queued");
    expect(task.kind).toBe("code");
    expect(task.preferredAgent).toBe("agent.developer");
    expect(task.context.sprint).toBe("ADOS OS 4.0");
    expect(task.context.repository).toBe("TelegramBotCourse");
    expect(bridge.queue.list().length).toBe(1);
  });

  it("runs end-to-end through Orchestrator and Cursor Provider", async () => {
    const bridge = createChatBridge({ orchestrator: orch, gateway });
    const task = bridge.createTask({
      prompt: "Implement login page component in src/web/auth/Login.tsx",
      autoRun: false,
    });
    const done = await bridge.run(task.id);
    expect(["Done", "PartialSuccess"]).toContain(done.status);
    expect(done.generatedFiles.length).toBeGreaterThan(0);
    expect(done.durationMs).toBeGreaterThan(0);
    expect(bridge.history.list().length).toBeGreaterThan(0);
    expect(bridge.sessions.get().generatedFiles.length).toBeGreaterThan(0);
  }, 30_000);

  it("supports cancel and rollback", async () => {
    const bridge = createChatBridge({ orchestrator: orch, gateway });
    const task = bridge.createTask({
      prompt: "Research competitor CRM systems",
      autoRun: false,
    });
    await bridge.cancel(task.id);
    expect(bridge.queue.get(task.id)?.status).toBe("Cancelled");
    const rolled = await bridge.rollback(task.id);
    expect(rolled.status).toBe("Queued");
  });
});

describe("ChatBridgeService", () => {
  it("registers as kernel service", async () => {
    const orch = createAiOrchestrator();
    const gateway = createProviderGateway();
    orch.start(true);
    gateway.start(true);
    await gateway.connect();
    const svc = createChatBridgeService({ orchestrator: orch, gateway });
    expect(svc.id).toBe(CHAT_BRIDGE_SERVICE_ID);
    await svc.initialize();
    await svc.start();
    expect(svc.getLifecycleState()).toBe("Started");
    expect(svc.health().status).toBe("healthy");
    expect(svc.bridge.voice.supported).toBe(true);
    await svc.stop();
  });
});
