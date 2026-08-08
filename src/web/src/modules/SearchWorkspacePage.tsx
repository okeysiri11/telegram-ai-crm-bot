import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { Button, Card } from "@/ui";
import { searchProvider } from "../../navigation/managers/searchProvider";
import { rememberModuleRoute } from "./lastModuleStore";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { useI18n } from "@/i18n";
import {
  UnifiedIntentBar,
  friendlyCategoryLabel,
  isChatCapabilityQuestion,
  CAPABILITY_REPLY_RU,
} from "@/workspace-chrome/unified-intent";

/**
 * Sprint 27.2 / 27.4 / 42.3 / 46.4 — Search Workspace (human-first results).
 */
export function SearchWorkspacePage() {
  const t = useI18n((s) => s.t);
  const [params] = useSearchParams();
  const q = (params.get("q") || "").trim();
  const navigate = useNavigate();
  const { openPalette } = useNavigationUi();

  useEffect(() => {
    document.title = "Поиск · ADOS Enterprise";
    rememberModuleRoute("/search");
  }, []);

  const isAiQuestion = q ? isChatCapabilityQuestion(q) : false;

  const groups = useMemo(() => (q && !isAiQuestion ? searchProvider.searchGrouped(q, 8) : []), [q, isAiQuestion]);
  const total = useMemo(() => groups.reduce((n, g) => n + g.hits.length, 0), [groups]);

  const categorySummary = useMemo(
    () =>
      groups.map((g) => ({
        category: g.category,
        label: friendlyCategoryLabel(g.category) || g.label,
        count: g.hits.length,
      })),
    [groups],
  );

  const [showTech, setShowTech] = useState(false);

  return (
    <WorkspaceLayout>
      <div className="edm-page space-y-4">
        <header className="ews-module-hero ews-glass">
          <h1 className="eds-type-title text-2xl">{t("search.workspaceTitle")}</h1>
          <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">
            {t("search.workspaceHint")}
          </p>
          <div className="mt-3">
            <UnifiedIntentBar verticalId="owner" showQuickHints showRecent={false} />
          </div>
          <div className="mt-2">
            <Button type="button" size="sm" variant="ghost" onClick={openPalette}>
              {t("search.openPalette")} · ⌘/Ctrl+K
            </Button>
          </div>
        </header>

        {isAiQuestion && q ? (
          <Card title="AI Консьерж">
            <p className="eds-type-body whitespace-pre-wrap">{CAPABILITY_REPLY_RU}</p>
          </Card>
        ) : null}

        {!isAiQuestion && q ? (
          <section className="space-y-3" data-testid="search-results-human">
            <h2 className="eds-type-section">
              {total > 0 ? `Нашёл ${total} результатов` : "Ничего не нашёл"}
            </h2>
            {categorySummary.length > 0 ? (
              <ul className="flex flex-wrap gap-2" aria-label="Категории">
                {categorySummary.map((c) => (
                  <li
                    key={c.category}
                    className="rounded-full border border-[var(--ew-border)] px-3 py-1 eds-type-caption"
                  >
                    {c.label} — {c.count}
                  </li>
                ))}
              </ul>
            ) : null}

            {groups.length ? (
              <div className="space-y-4">
                {groups.map((g) => (
                  <Card key={g.category} title={`${friendlyCategoryLabel(g.category) || g.label} — ${g.hits.length}`}>
                    <ul className="space-y-2">
                      {g.hits.map((h) => (
                        <li key={h.id || h.path + h.title}>
                          <button
                            type="button"
                            className="cc-action w-full text-left"
                            onClick={() => navigate(h.path)}
                          >
                            <span className="font-medium">{h.title}</span>
                            {showTech ? (
                              <span className="eds-type-helper">
                                {h.path} · {h.score}
                              </span>
                            ) : (
                              <span className="eds-type-helper">
                                {friendlyCategoryLabel(h.category)}
                              </span>
                            )}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Попробуйте уточнить запрос или спросите AI: «Что ты умеешь?»
              </p>
            )}

            <label className="eds-type-caption flex items-center gap-2 text-[var(--eds-text-muted)]">
              <input
                type="checkbox"
                checked={showTech}
                onChange={(e) => setShowTech(e.target.checked)}
              />
              Показать технические данные
            </label>
          </section>
        ) : null}

        {!q ? (
          <Card title="С чего начать?">
            <p className="eds-type-body text-[var(--eds-text-muted)]">
              Напишите задачу выше — система сама определит, нужен поиск, переход или ответ AI.
            </p>
          </Card>
        ) : null}
      </div>
    </WorkspaceLayout>
  );
}
