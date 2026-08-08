/**
 * Sprint 46.4 — Task Inbox (лёгкая история действий).
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { STATUS_LABEL_RU } from "./unifiedIntentTypes";
import { useUnifiedIntentStore } from "./unifiedIntentStore";
import { intentKindLabel } from "./executeUnifiedIntent";

type Filter = "all" | "running" | "done" | "failed";

const FILTER_LABELS: Record<Filter, string> = {
  all: "Все",
  running: "Выполняются",
  done: "Готово",
  failed: "Ошибки",
};

export function TaskInboxPanel({
  onClose,
}: {
  onClose?: () => void;
} = {}) {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<Filter>("all");
  const items = useUnifiedIntentStore((s) => s.byFilter(filter));
  const showTech = useUnifiedIntentStore((s) => s.showTech);
  const setShowTech = useUnifiedIntentStore((s) => s.setShowTech);

  return (
    <div className="uib-inbox" data-testid="task-inbox" role="dialog" aria-label="История действий">
      <div className="uib-inbox__head">
        <h2 className="eds-type-section">Действия</h2>
        {onClose ? (
          <Button size="sm" variant="ghost" onClick={onClose} aria-label="Закрыть">
            ✕
          </Button>
        ) : null}
      </div>

      <div className="uib-inbox__filters" role="tablist">
        {(Object.keys(FILTER_LABELS) as Filter[]).map((f) => (
          <button
            key={f}
            type="button"
            role="tab"
            aria-selected={filter === f}
            className={filter === f ? "is-active" : undefined}
            onClick={() => setFilter(f)}
          >
            {FILTER_LABELS[f]}
          </button>
        ))}
      </div>

      <ul className="uib-inbox__list">
        {items.length === 0 ? (
          <li className="uib-inbox__empty eds-type-helper">Пока нет действий.</li>
        ) : (
          items.map((it) => {
            const running = ["received", "routing", "running", "waiting_user"].includes(it.status);
            const label = it.progressLabel || STATUS_LABEL_RU[it.status];
            return (
              <li key={it.id} className="uib-inbox__item" data-status={it.status}>
                <div className="uib-inbox__item-main">
                  <span className="uib-inbox__icon" aria-hidden>
                    {running ? "⏳" : it.status === "failed" ? "!" : "✓"}
                  </span>
                  <div>
                    <p className="uib-inbox__text">{it.text}</p>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">
                      {label}
                      {it.resultCount != null ? ` · ${it.resultCount} результатов` : ""}
                      {showTech ? ` · ${intentKindLabel(it.intent)}` : ""}
                    </p>
                    {it.reply && it.status === "completed" ? (
                      <p className="uib-inbox__reply eds-type-small">{it.reply.split("\n")[0]}</p>
                    ) : null}
                    {it.status === "failed" ? (
                      <div className="uib-inbox__actions">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => {
                            if (it.resultPath) navigate(it.resultPath);
                          }}
                          disabled={!it.resultPath}
                        >
                          Повторить
                        </Button>
                      </div>
                    ) : null}
                    {it.status === "completed" && it.resultPath ? (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="mt-1"
                        onClick={() => navigate(it.resultPath!)}
                      >
                        Посмотреть результат
                      </Button>
                    ) : null}
                    {showTech && it.debug ? (
                      <pre className="uib-tech">{JSON.stringify(it.debug, null, 2)}</pre>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })
        )}
      </ul>

      <label className="uib-inbox__tech eds-type-caption">
        <input
          type="checkbox"
          checked={showTech}
          onChange={(e) => setShowTech(e.target.checked)}
        />{" "}
        Показать технические данные
      </label>
    </div>
  );
}
