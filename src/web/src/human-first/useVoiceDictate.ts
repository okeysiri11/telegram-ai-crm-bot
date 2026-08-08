/**
 * Sprint 42.3 — browser speech-to-text with demo fallback (no new backend).
 */

export type VoiceDictateStatus = "idle" | "listening" | "processing" | "unsupported";

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((ev: { results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }> }) => void) | null;
  onerror: ((ev: { error?: string }) => void) | null;
  onend: (() => void) | null;
};

function getSpeechRecognitionCtor(): (new () => SpeechRecognitionLike) | null {
  const w = window as unknown as {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function isVoiceDictateSupported(): boolean {
  return typeof window !== "undefined" && Boolean(getSpeechRecognitionCtor());
}

/**
 * Start voice dictate. Resolves with transcript (or demo phrase on fallback).
 * Call `stop()` from the returned handle to end early.
 */
export function startVoiceDictate(opts: {
  lang?: string;
  demoFallbackText?: string;
  onPartial?: (text: string) => void;
  onStatus?: (status: VoiceDictateStatus) => void;
}): { stop: () => void; done: Promise<string> } {
  const Ctor = getSpeechRecognitionCtor();
  let settled = false;
  let rec: SpeechRecognitionLike | null = null;
  let fallbackTimer: ReturnType<typeof setTimeout> | null = null;

  const done = new Promise<string>((resolve) => {
    const finish = (text: string) => {
      if (settled) return;
      settled = true;
      opts.onStatus?.("idle");
      resolve(text.trim());
    };

    if (!Ctor) {
      opts.onStatus?.("processing");
      fallbackTimer = setTimeout(() => {
        finish(opts.demoFallbackText || "Добавь автомобиль");
      }, 1200);
      opts.onStatus?.("listening");
      return;
    }

    try {
      rec = new Ctor();
      rec.lang = opts.lang || "ru-RU";
      rec.continuous = false;
      rec.interimResults = true;
      opts.onStatus?.("listening");

      rec.onresult = (ev) => {
        let interim = "";
        let finalText = "";
        for (let i = 0; i < ev.results.length; i++) {
          const row = ev.results[i];
          if (!row) continue;
          const t = row[0]?.transcript || "";
          if (row.isFinal) finalText += t;
          else interim += t;
        }
        if (interim) opts.onPartial?.(interim);
        if (finalText) {
          opts.onStatus?.("processing");
          finish(finalText);
        }
      };

      rec.onerror = () => {
        opts.onStatus?.("processing");
        finish(opts.demoFallbackText || "Добавь автомобиль");
      };

      rec.onend = () => {
        if (!settled) {
          opts.onStatus?.("processing");
          finish(opts.demoFallbackText || "Добавь автомобиль");
        }
      };

      rec.start();
    } catch {
      opts.onStatus?.("processing");
      fallbackTimer = setTimeout(() => finish(opts.demoFallbackText || "Добавь автомобиль"), 800);
    }
  });

  return {
    done,
    stop: () => {
      if (fallbackTimer) clearTimeout(fallbackTimer);
      try {
        rec?.stop();
      } catch {
        /* ignore */
      }
    },
  };
}
