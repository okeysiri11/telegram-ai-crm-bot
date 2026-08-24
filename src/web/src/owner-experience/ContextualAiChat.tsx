/**
 * Sprint 46.3 — AI Concierge chat: real Command Center path + human UX.
 */

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { Button } from "@/ui";
import { getVertical } from "@/vertical-workspace/catalog";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { useModeStore } from "@/platform-modes/modeStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import {
  buildSessionId,
  classifyConciergeIntent,
  contextLabelForUser,
  localConciergeReply,
  promptForQuickAction,
  quickActionFollowUps,
  sanitizeConciergeReply,
  STATUS_COPY,
  type ConciergeMsgKind,
  type TaskUiStatus,
} from "./conciergeChatLogic";

type ExecutionMeta = {
  planId?: string;
  steps?: string[];
  status?: string;
  durationSec?: number;
  cost?: number;
  herculesJobIds?: string[];
  agents?: string[];
  vertical?: string;
};

type Msg = {
  id: string;
  role: "user" | "ai";
  text: string;
  kind: ConciergeMsgKind;
  taskStatus?: TaskUiStatus;
  executionMeta?: ExecutionMeta;
};

function specialistLabel(verticalId: string): string {
  const v = getVertical(verticalId);
  if (!v) return "AI Консьерж";
  const map: Record<string, string> = {
    crm: "CRM AI",
    auto: "Auto AI",
    crypto: "Crypto AI",
    drone: "Drone AI",
    travel: "Travel AI",
    construction: "Construction AI",
    production: "Production AI",
    agro: "Агро-помощник",
    knowledge: "Knowledge AI",
    marketplace: "Marketing AI",
    owner: "Owner AI",
    ai_studio: "AI Studio",
    documents: "Documents AI",
  };
  return map[verticalId] || `${v.label} AI`;
}

/** Exported for Sprint 42.9 tests — vertical → specialist mapping (Owner/debug). */
export function specialistForVertical(verticalId: string): string {
  return specialistLabel(verticalId);
}

const CHIPS = [
  "Создай клиента",
  "Покажи сделки",
  "Найди документы",
  "Запусти рекламу",
  "Построй отчёт",
  "Создай AI-задачу",
] as const;

const REQUEST_TIMEOUT_MS = 45_000;

function newId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

async function callCommandCenter(
  text: string,
  opts: {
    sessionId: string;
    signal: AbortSignal;
    role: string;
    vertical: string;
  },
): Promise<{
  reply: string;
  meta: ExecutionMeta;
  status: string;
}> {
  const { sessionId, signal, role, vertical } = opts;
  const res = await fetch("/management/v1/ai-command/chat", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      channel: "web",
      session_id: sessionId,
      // Sprint 47.0 (CC-3) — the server resolves the real, authoritative
      // role/vertical from the caller's server-side session and does not trust
      // these; sent only as a best-effort hint/fallback for callers with no
      // server-side session (e.g. pure API-key access), and to keep this request
      // honest about what the UI actually shows the user instead of a hardcoded
      // "owner" that no longer reflects reality once Beauty/Auto/Agro/Crypto
      // switching landed.
      role,
      vertical,
      max_steps: 3,
    }),
    signal,
  });
  const json = await res.json().catch(() => ({}));
  const data = json?.data || json || {};
  const raw =
    data.reply_ru ||
    json?.reply_ru ||
    (res.ok ? "✅ Готово." : "Не удалось выполнить задачу. Попробовать ещё раз?");
  return {
    reply: sanitizeConciergeReply(String(raw)),
    status: String(data.status || (res.ok ? "completed" : "failed")),
    meta: {
      planId: data.plan_id,
      steps: data.steps,
      status: data.status,
      durationSec: data.duration_sec,
      cost: data.cost,
      herculesJobIds: data.hercules_job_ids,
      agents: data.route?.agents,
      vertical: data.route?.vertical,
    },
  };
}

export function ContextualAiChat({
  open,
  onClose,
  verticalId: forcedVertical,
}: {
  open: boolean;
  onClose: () => void;
  verticalId?: string;
}) {
  const storeVertical = useVerticalWorkspaceStore((s) => s.verticalId);
  const verticalId = forcedVertical || storeVertical;
  const vertical = getVertical(verticalId);
  const contextLabel = contextLabelForUser(vertical?.label, verticalId);
  const workMode = useModeStore((s) => s.mode);
  const activeRoleId = useRoleSwitcher((s) => s.activeRoleId);
  const titleId = useId();

  const [sessionId] = useState(() => buildSessionId());
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [followUps, setFollowUps] = useState<string[] | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [voicePreview, setVoicePreview] = useState<string | null>(null);
  const [stickToBottom, setStickToBottom] = useState(true);
  const [showJump, setShowJump] = useState(false);
  const [lastMeta, setLastMeta] = useState<ExecutionMeta | null>(null);

  const [messages, setMessages] = useState<Msg[]>(() => [
    {
      id: newId("welcome"),
      role: "ai",
      kind: "chat",
      text: `Здравствуйте. Я AI Консьерж.\nКонтекст: ${contextLabel}.\nЧем помочь?`,
    },
  ]);

  const logRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const lastUserTaskRef = useRef<string>("");

  const scrollToBottom = useCallback(() => {
    const el = logRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
    setShowJump(false);
    setStickToBottom(true);
  }, []);

  useEffect(() => {
    if (!open) return;
    if (stickToBottom) scrollToBottom();
    else setShowJump(true);
  }, [messages, open, stickToBottom, scrollToBottom]);

  const onLogScroll = () => {
    const el = logRef.current;
    if (!el) return;
    const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
    const atBottom = dist < 48;
    setStickToBottom(atBottom);
    if (atBottom) setShowJump(false);
  };

  const append = useCallback((msg: Msg) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const replaceMsg = useCallback((id: string, patch: Partial<Msg>) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));
  }, []);

  const runAction = useCallback(
    async (userText: string) => {
      lastUserTaskRef.current = userText;
      const statusId = newId("status");
      append({
        id: statusId,
        role: "ai",
        kind: "status",
        taskStatus: "running",
        text: STATUS_COPY.running,
      });
      setBusy(true);
      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      const timer = window.setTimeout(() => ctrl.abort(), REQUEST_TIMEOUT_MS);

      try {
        const { reply, meta, status } = await callCommandCenter(userText, {
          sessionId,
          signal: ctrl.signal,
          role: activeRoleId,
          vertical: verticalId,
        });
        setLastMeta(meta);
        const clarify = status === "clarify" || /уточните|напишите название/i.test(reply);
        replaceMsg(statusId, {
          kind: clarify ? "chat" : "result",
          taskStatus: clarify ? "waiting_for_user" : "completed",
          text: clarify ? reply : `${STATUS_COPY.completed}\n\n${reply}`,
          executionMeta: meta,
        });
      } catch (err) {
        const timedOut = err instanceof DOMException && err.name === "AbortError";
        replaceMsg(statusId, {
          kind: "error",
          taskStatus: timedOut ? "timeout" : "failed",
          text: timedOut ? STATUS_COPY.timeout : STATUS_COPY.failed,
        });
      } finally {
        window.clearTimeout(timer);
        setBusy(false);
      }
    },
    [append, replaceMsg, sessionId, activeRoleId, verticalId],
  );

  const send = useCallback(
    async (raw: string) => {
      const q = raw.trim();
      if (!q || busy) return;
      setText("");
      setVoicePreview(null);
      setFollowUps(null);
      append({ id: newId("user"), role: "user", kind: "chat", text: q });

      const intent = classifyConciergeIntent(q);
      if (intent === "QUESTION" || intent === "CHAT") {
        const reply = localConciergeReply(q, { contextLabel, intent });
        append({ id: newId("ai"), role: "ai", kind: "chat", text: reply });
        // Soft marketing: stay in clarify; next concrete ACTION will hit API
        if (/реклам/i.test(q) && intent === "CHAT") {
          setFollowUps(["Сделай рекламу кофейни в Одессе", "Black Coffee, Одесса"]);
        }
        return;
      }

      await runAction(q);
    },
    [append, busy, contextLabel, runAction],
  );

  const onChip = (chip: string) => {
    if (/реклам/i.test(chip)) {
      append({ id: newId("user"), role: "user", kind: "chat", text: chip });
      append({
        id: newId("ai"),
        role: "ai",
        kind: "chat",
        text: promptForQuickAction(chip),
      });
      setFollowUps(quickActionFollowUps(chip));
      return;
    }
    void send(chip);
  };

  const onFollowUp = (label: string) => {
    if (/одесс|black coffee|сделай рекламу/i.test(label)) {
      void send(label);
      return;
    }
    void send(`Рекламируем: ${label.toLowerCase()}`);
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void send(text);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send(text);
    }
  };

  const onVoice = () => {
    if (workMode === "voice" || workMode === "ai") {
      const draft = text.trim() || "Создай рекламу";
      void send(draft);
      return;
    }
    // HUMAN mode: preview then confirm
    const sample = text.trim() || "Хочу рекламировать кафе";
    setVoicePreview(sample);
  };

  const cancelRunning = () => {
    abortRef.current?.abort();
    setBusy(false);
  };

  const chips = useMemo(() => [...CHIPS], []);

  if (!open) return null;

  return (
    <div className="oe-ai-chat-backdrop" role="presentation" onMouseDown={onClose}>
      <div
        className="oe-ai-chat ews-glass"
        role="dialog"
        aria-labelledby={titleId}
        aria-modal="true"
        data-testid="contextual-ai-chat"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="oe-ai-chat-head">
          <div>
            <p className="eds-type-caption text-[var(--eds-text-muted)]">AI Консьерж</p>
            <h2 id={titleId} className="eds-type-section">
              Поговорить с AI
            </h2>
            <p className="eds-type-helper oe-ai-chat-context">Контекст: {contextLabel}</p>
            <button
              type="button"
              className="oe-ai-chat-details-toggle"
              onClick={() => setShowDetails((v) => !v)}
            >
              {showDetails ? "▾ Скрыть выполнение" : "▸ Подробнее"}
            </button>
            {showDetails && lastMeta && (
              <div className="oe-ai-chat-exec" data-testid="concierge-execution-details">
                <p>Статус: {lastMeta.status || "—"}</p>
                {lastMeta.steps?.length ? <p>Шаги: {lastMeta.steps.join(" → ")}</p> : null}
                {typeof lastMeta.durationSec === "number" ? (
                  <p>Время: {lastMeta.durationSec.toFixed(1)} сек</p>
                ) : null}
              </div>
            )}
          </div>
          <Button size="sm" variant="ghost" onClick={onClose}>
            Закрыть
          </Button>
        </header>

        <div className="oe-ai-chat-chips" data-testid="concierge-quick-actions">
          {chips.map((c) => (
            <button key={c} type="button" className="oe-ai-chip" onClick={() => onChip(c)}>
              {c}
            </button>
          ))}
        </div>

        {followUps && (
          <div className="oe-ai-chat-chips oe-ai-chat-followups">
            {followUps.map((f) => (
              <button key={f} type="button" className="oe-ai-chip is-follow" onClick={() => onFollowUp(f)}>
                {f}
              </button>
            ))}
          </div>
        )}

        <div className="oe-ai-chat-log-wrap">
          <div
            className="oe-ai-chat-log"
            data-testid="ai-chat-log"
            ref={logRef}
            onScroll={onLogScroll}
          >
            {messages.map((m) => (
              <div
                key={m.id}
                className={`oe-ai-msg is-${m.role} kind-${m.kind}`}
                data-kind={m.kind}
              >
                <p className="oe-ai-msg-label">
                  {m.role === "user" ? "Вы" : "AI Консьерж"}
                </p>
                <p className="oe-ai-msg-body">{m.text}</p>
                {m.taskStatus === "running" && busy && (
                  <button type="button" className="oe-ai-cancel" onClick={cancelRunning}>
                    Остановить
                  </button>
                )}
                {(m.taskStatus === "failed" || m.taskStatus === "timeout") && (
                  <div className="oe-ai-msg-actions">
                    {m.taskStatus === "timeout" && (
                      <button
                        type="button"
                        className="oe-ai-chip"
                        onClick={() => void runAction(lastUserTaskRef.current)}
                      >
                        Продолжить ожидание
                      </button>
                    )}
                    <button
                      type="button"
                      className="oe-ai-chip"
                      onClick={() => void runAction(lastUserTaskRef.current)}
                    >
                      Повторить
                    </button>
                    <button type="button" className="oe-ai-chip" onClick={cancelRunning}>
                      Остановить
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
          {showJump && (
            <button type="button" className="oe-ai-jump" onClick={scrollToBottom}>
              ↓ Новые сообщения
            </button>
          )}
        </div>

        {voicePreview && (
          <div className="oe-ai-voice-preview" data-testid="voice-preview">
            <p className="eds-type-small">Голосовой черновик: «{voicePreview}»</p>
            <div className="oe-ai-msg-actions">
              <button type="button" className="oe-ai-chip" onClick={() => void send(voicePreview)}>
                Отправить
              </button>
              <button type="button" className="oe-ai-chip" onClick={() => setVoicePreview(null)}>
                Отмена
              </button>
            </div>
          </div>
        )}

        <form className="oe-ai-chat-form" onSubmit={onSubmit}>
          <button
            type="button"
            className="oe-ai-icon-btn"
            aria-label="Вложение"
            title="Вложение"
            disabled={busy}
          >
            +
          </button>
          <textarea
            className="oe-ai-composer"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Напишите Консьержу…"
            aria-label="Сообщение AI"
            rows={1}
            disabled={busy}
          />
          <button
            type="button"
            className="oe-ai-icon-btn"
            aria-label="Голос"
            title="Голос"
            onClick={onVoice}
            disabled={busy}
          >
            🎤
          </button>
          <Button type="submit" className="ews-primary-cta" disabled={busy || !text.trim()}>
            Отправить
          </Button>
        </form>
      </div>
    </div>
  );
}
