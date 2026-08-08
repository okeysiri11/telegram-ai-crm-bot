import { beforeEach, describe, expect, it } from "vitest";
import {
  DEFAULT_MODE_SETTINGS,
  MODE_INDICATORS,
  MODE_STORAGE_KEY,
  useModeStore,
} from "./modeStore";

describe("platform-modes store", () => {
  beforeEach(() => {
    localStorage.removeItem(MODE_STORAGE_KEY);
    useModeStore.setState({
      mode: "human",
      settings: DEFAULT_MODE_SETTINGS,
      indicator: MODE_INDICATORS.human,
    });
  });

  it("defaults to human", () => {
    expect(useModeStore.getState().mode).toBe("human");
    expect(useModeStore.getState().isHuman()).toBe(true);
    expect(useModeStore.getState().canAutoAgents()).toBe(false);
  });

  it("switches to AI and Voice exclusively", () => {
    useModeStore.getState().setMode("ai");
    expect(useModeStore.getState().mode).toBe("ai");
    expect(useModeStore.getState().indicator).toBe("🟢 AI ACTIVE");
    expect(useModeStore.getState().canAutoAgents()).toBe(true);

    useModeStore.getState().setMode("voice");
    expect(useModeStore.getState().mode).toBe("voice");
    expect(useModeStore.getState().isVoice()).toBe(true);
    expect(useModeStore.getState().isAi()).toBe(false);
  });

  it("setVoice toggles voice/human", () => {
    useModeStore.getState().setVoice(true);
    expect(useModeStore.getState().mode).toBe("voice");
    useModeStore.getState().setVoice(false);
    expect(useModeStore.getState().mode).toBe("human");
  });

  it("persists settings", () => {
    useModeStore.getState().updateSettings({ speak_answers: false, start_in_ai: true });
    expect(useModeStore.getState().settings.speak_answers).toBe(false);
    expect(useModeStore.getState().settings.start_in_ai).toBe(true);
    const raw = localStorage.getItem(MODE_STORAGE_KEY);
    expect(raw).toContain("speak_answers");
  });

  it("rememberDefault stores current mode", () => {
    useModeStore.getState().setMode("ai");
    useModeStore.getState().rememberDefault();
    expect(useModeStore.getState().settings.default_mode).toBe("ai");
  });

  it("restore respects start flags", () => {
    useModeStore.getState().updateSettings({
      remember_last_mode: false,
      start_in_human: false,
      start_in_ai: true,
      start_voice_after_login: false,
    });
    useModeStore.getState().restore();
    expect(useModeStore.getState().mode).toBe("ai");
  });
});
