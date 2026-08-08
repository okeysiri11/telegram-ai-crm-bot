/**
 * Sprint 46.4 — единая строка «Что хотите сделать?» (Unified Intent Bar).
 * После submit input всегда очищается; задача уходит в историю со статусом.
 */

import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { useModeStore } from "@/platform-modes/modeStore";
import { startVoiceDictate, type VoiceDictateStatus } from "@/human-first/useVoiceDictate";
import { STATUS_LABEL_RU, type IntentInteraction } from "./unifiedIntentTypes";
import { EMPTY_EXAMPLES, QUICK_HINTS } from "./unifiedIntentRouter";
import { resolveVerticalIntentConfig } from "./verticalIntentConfig";
import { useUnifiedIntentStore } from "./unifiedIntentStore";
import { executeUnifiedIntent } from "./executeUnifiedIntent";
import { TaskInboxPanel } from "./TaskInboxPanel";
import "./unifiedIntentBar.css";

export type UnifiedIntentBarProps = {
  verticalId?: string;
  /** Compact header embedding */
  compact?: boolean;
  className?: string;
  sessionId?: string;
  showQuickHints?: boolean;
  showRecent?: boolean;
  onOpenAiChat?: () => void;
};

function formatTime(ts: number): string {
  try {
    return new Date(ts).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function statusLine(it: IntentInteraction): string {
  if (it.progressLabel) return it.progressLabel;
  if (it.status === "completed" && it.resultCount != null) {
    return `Найдено ${it.resultCount}`;
  }
  if (it.status === "completed" && it.reply) {
    return it.reply.split("\n")[0] || STATUS_LABEL_RU.completed;
  }
  return STATUS_LABEL_RU[it.status];
}

export function UnifiedIntentBar({
  verticalId = "owner",
  compact = false,
  className = "",
  sessionId,
  showQuickHints = true,
  showRecent = true,
  onOpenAiChat,
}: UnifiedIntentBarProps) {
  const navigate = useNavigate();
  const cfg = resolveVerticalIntentConfig(verticalId);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const voiceRef = useRef<{ stop: () => void } | null>(null);
  const labelId = useId();

  const [draft, setDraft] = useState("");
  const [voiceStatus, setVoiceStatus] = useState<VoiceDictateStatus>("idle");
  const [voicePreview, setVoicePreview] = useState<string | null>(null);
  const [lastResultId, setLastResultId] = useState<string | null>(null);

  const hydrate = useUnifiedIntentStore((s) => s.hydrate);
  const recent = useUnifiedIntentStore((s) => s.recent(5));
  const inboxOpen = useUnifiedIntentStore((s) => s.inboxOpen);
  const setInboxOpen = useUnifiedIntentStore((s) => s.setInboxOpen);
  const showTech = useUnifiedIntentStore((s) => s.showTech);
  const items = useUnifiedIntentStore((s) => s.items);
  const mode = useModeStore((s) => s.mode);

  const session =
    sessionId ||
    (typeof window !== "undefined"
      ? `uib-${verticalId}-${window.location.pathname}`
      : `uib-${verticalId}`);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    return () => {
      voiceRef.current?.stop();
    };
  }, []);

  const lastResult = lastResultId ? items.find((i) => i.id === lastResultId) : recent[0];

  function focusInput() {
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  async function submitText(raw: string) {
    const text = raw.trim();
    if (!text) return;

    // Acceptance: clear immediately — never leave submitted text in the input.
    setDraft("");
    setVoicePreview(null);
    focusInput();

    const item = await executeUnifiedIntent(text, {
      verticalId: cfg.verticalId,
      navigate,
      openAiChat: onOpenAiChat,
      sessionId: session,
    });
    setLastResultId(item.id);
    focusInput();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Escape") {
      e.preventDefault();
      setDraft("");
      setVoicePreview(null);
      return;
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submitText(draft);
    }
  }

  async function toggleVoice() {
    if (voiceStatus === "listening") {
      voiceRef.current?.stop();
      voiceRef.current = null;
      setVoiceStatus("processing");
      return;
    }
    const handle = startVoiceDictate({
      onStatus: setVoiceStatus,
      onPartial: (partial) => setDraft(partial),
      demoFallbackText: "Покажи сделки за неделю",
    });
    voiceRef.current = handle;
    const transcript = await handle.done;
    voiceRef.current = null;
    setVoiceStatus("idle");
    if (!transcript) return;

    // Human Mode: confirm preview. AI/Voice: auto-send.
    if (mode === "human") {
      setDraft("");
      setVoicePreview(transcript);
      return;
    }
    await submitText(transcript);
  }

  const listening = voiceStatus === "listening";

  return (
    <section
      className={`uib ${compact ? "uib--compact" : ""} ${className}`.trim()}
      data-testid="unified-intent-bar"
      data-vertical={cfg.verticalId}
      aria-labelledby={labelId}
    >
      {!compact ? (
        <div className="uib__title-row">
          <h2 id={labelId} className="eds-type-section">
            Что хотите сделать?
          </h2>
          <span className="uib__context eds-type-caption">Контекст: {cfg.contextLabel}</span>
        </div>
      ) : (
        <span id={labelId} className="sr-only">
          Что хотите сделать?
        </span>
      )}

      <div className="uib__composer">
        <textarea
          ref={inputRef}
          className="uib__input"
          rows={compact ? 1 : 2}
          placeholder="Напишите или скажите задачу…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          aria-label="Что хотите сделать?"
          data-testid="unified-intent-input"
        />
        <div className="uib__actions">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className={`uib__mic ${listening ? "is-listening" : ""}`}
            onClick={() => void toggleVoice()}
            aria-label={listening ? "Остановить запись" : "Голос"}
            aria-pressed={listening}
            data-testid="unified-intent-mic"
            title="Голосовой ввод"
          >
            {listening ? "⏹" : "🎤"}
          </Button>
          <Button
            type="button"
            size="sm"
            className="ews-primary-cta uib__send"
            onClick={() => void submitText(draft)}
            data-testid="unified-intent-send"
            aria-label="Отправить"
          >
            ➤
          </Button>
        </div>
      </div>

      {voicePreview ? (
        <div className="uib__voice-preview" data-testid="unified-intent-voice-preview">
          <p className="eds-type-small">
            <strong>Распознано:</strong> {voicePreview}
          </p>
          <div className="uib__voice-btns">
            <Button
              size="sm"
              className="ews-primary-cta"
              onClick={() => void submitText(voicePreview)}
              data-testid="unified-intent-voice-send"
            >
              Отправить
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                setDraft(voicePreview);
                setVoicePreview(null);
                focusInput();
              }}
            >
              Изменить
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setVoicePreview(null);
                focusInput();
              }}
            >
              Отмена
            </Button>
          </div>
        </div>
      ) : null}

      {showQuickHints && !compact ? (
        <div className="uib__hints" data-testid="unified-intent-hints">
          {QUICK_HINTS.map((h) => (
            <button
              key={h.id}
              type="button"
              className="uib__hint"
              onClick={() => {
                setDraft(h.draft);
                focusInput();
              }}
            >
              {h.label}
            </button>
          ))}
          <Button size="sm" variant="secondary" onClick={() => setInboxOpen(true)}>
            История
          </Button>
        </div>
      ) : null}

      {compact ? (
        <div className="uib__compact-meta">
          <span className="eds-type-caption text-[var(--eds-text-muted)]">
            Контекст: {cfg.contextLabel}
          </span>
          <button type="button" className="uib__link" onClick={() => setInboxOpen(true)}>
            История
          </button>
        </div>
      ) : null}

      {showRecent && recent.length === 0 && !compact ? (
        <div className="uib__empty" data-testid="unified-intent-empty">
          <p className="eds-type-body font-medium">С чего начать?</p>
          <ul>
            {EMPTY_EXAMPLES.map((ex) => (
              <li key={ex}>
                <button
                  type="button"
                  className="uib__example"
                  onClick={() => void submitText(ex)}
                >
                  {ex}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {showRecent && recent.length > 0 ? (
        <div className="uib__history" data-testid="unified-intent-history">
          {!compact ? <p className="eds-type-caption font-semibold">Последние действия</p> : null}
          <ul>
            {recent.slice(0, compact ? 3 : 5).map((it) => {
              const running = ["received", "routing", "running", "waiting_user"].includes(
                it.status,
              );
              return (
                <li key={it.id} data-status={it.status}>
                  <span aria-hidden>{running ? "⏳" : it.status === "failed" ? "!" : "✓"}</span>
                  <div>
                    <p className="uib__hist-text">{it.text}</p>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">
                      {statusLine(it)}
                      {it.status === "completed" ? ` · ${formatTime(it.updatedAt)}` : ""}
                    </p>
                    {showTech && it.debug ? (
                      <pre className="uib-tech">{JSON.stringify(it.debug)}</pre>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {lastResult &&
      (lastResult.status === "completed" || lastResult.status === "failed") &&
      lastResult.reply &&
      !compact ? (
        <div
          className={`uib__result ${lastResult.status === "failed" ? "is-error" : ""}`}
          data-testid="unified-intent-result"
        >
          <p className="eds-type-caption font-semibold">
            {lastResult.status === "failed" ? "Не удалось выполнить задачу." : "AI Консьерж"}
          </p>
          <p className="eds-type-body whitespace-pre-wrap">{lastResult.reply}</p>
          {lastResult.status === "failed" ? (
            <div className="uib__voice-btns mt-2">
              <Button size="sm" variant="secondary" onClick={() => void submitText(lastResult.text)}>
                Повторить
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  setDraft(lastResult.text);
                  focusInput();
                }}
              >
                Изменить запрос
              </Button>
            </div>
          ) : null}
          {lastResult.hits?.length ? (
            <ul className="uib__hits">
              {lastResult.hits.map((h) => (
                <li key={h.id}>
                  <button type="button" className="uib__hit" onClick={() => navigate(h.path)}>
                    <span>{h.title}</span>
                    <span className="eds-type-caption">{h.categoryLabel}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      {inboxOpen ? (
        <div className="uib-inbox-overlay" role="presentation" onClick={() => setInboxOpen(false)}>
          <div
            className="uib-inbox-sheet"
            role="presentation"
            onClick={(e) => e.stopPropagation()}
          >
            <TaskInboxPanel onClose={() => setInboxOpen(false)} />
          </div>
        </div>
      ) : null}
    </section>
  );
}
