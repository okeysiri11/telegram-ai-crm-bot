import { describe, expect, it, beforeEach } from "vitest";
import { createAiOrchestrator } from "@ados/orchestrator";
import { createProviderGateway } from "@ados/providers";
import { createChatBridge } from "@ados/chat-bridge";
import {
  createIntentDetector,
  createWakeWord,
  createVoiceGateway,
  createVoiceService,
  VOICE_SERVICE_ID,
  createSpeechRecognizer,
} from "../index.js";

describe("IntentDetector", () => {
  const detector = createIntentDetector();

  it("detects generate_code", () => {
    const m = detector.detect("Generate code for login page");
    expect(m.intent).toBe("generate_code");
    expect(m.confidence).toBeGreaterThan(0.8);
  });

  it("detects open_crm", () => {
    expect(detector.detect("Open the CRM").intent).toBe("open_crm");
  });

  it("detects run_workflow", () => {
    expect(detector.detect("Run workflow enterprise delivery").intent).toBe(
      "run_workflow",
    );
  });
});

describe("WakeWord", () => {
  it("uses configurable phrase", () => {
    const w = createWakeWord("Hey ADOS", true);
    const hit = w.match("Hey ADOS generate code for dashboard");
    expect(hit.matched).toBe(true);
    expect(hit.remainder.toLowerCase()).toContain("generate");
  });

  it("rejects non-matching when enabled", () => {
    const w = createWakeWord("Hey ADOS", true);
    expect(w.match("please open crm").matched).toBe(false);
  });

  it("can be reconfigured", () => {
    const w = createWakeWord("Hey ADOS");
    w.configure("Okay ADOS");
    expect(w.match("Okay ADOS open marketplace").matched).toBe(true);
  });
});

describe("SpeechRecognizer", () => {
  it("transcribes textHint via whisper mock", async () => {
    const stt = createSpeechRecognizer("stt.whisper.mock");
    await stt.connect();
    const r = await stt.transcribe({ textHint: "Open AI Studio" });
    expect(r.text).toBe("Open AI Studio");
    expect(r.providerId).toBe("stt.whisper.mock");
  });
});

describe("VoiceGateway pipeline", () => {
  const orch = createAiOrchestrator();
  const providers = createProviderGateway();

  beforeEach(async () => {
    orch.registry.clear();
    orch.stop();
    providers.registry.clear();
    providers.stop();
    orch.start(true);
    providers.start(true);
    await providers.connect();
  });

  it("starts session, processes voice into ChatGPT Bridge task", async () => {
    const bridge = createChatBridge({
      orchestrator: orch,
      gateway: providers,
    });
    const voice = createVoiceGateway({
      bridge,
      settings: { wakeWordEnabled: false, autoExecute: true },
    });

    await voice.start();
    const result = await voice.process({
      text: "Generate code for voice status badge",
      bypassWakeWord: true,
    });

    expect(result.intent).toBe("generate_code");
    expect(result.executed).toBe(true);
    expect(result.chatTaskId).toBeTruthy();
    expect(result.command.status).toBe("completed");
    expect(result.speech?.audioBase64).toBeTruthy();
    expect(voice.history().length).toBeGreaterThan(0);
    expect(voice.status().implemented).toBe(true);

    await voice.stop();
  }, 30_000);

  it("opens CRM without chat task", async () => {
    const bridge = createChatBridge({
      orchestrator: orch,
      gateway: providers,
    });
    const voice = createVoiceGateway({
      bridge,
      settings: { wakeWordEnabled: false, autoExecute: false },
    });
    await voice.start();
    const result = await voice.process({
      text: "Open the CRM",
      bypassWakeWord: true,
    });
    expect(result.intent).toBe("open_crm");
    expect(result.navigation?.path).toBe("/crm");
    expect(result.chatTaskId).toBeUndefined();
  });

  it("VoiceService registers as ados.voice", async () => {
    const bridge = createChatBridge({
      orchestrator: orch,
      gateway: providers,
    });
    const svc = createVoiceService({ bridge });
    expect(svc.id).toBe(VOICE_SERVICE_ID);
    await svc.initialize();
    await svc.start();
    expect(svc.health().status).toBe("healthy");
    await svc.stop();
  });
});
