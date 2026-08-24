/**
 * Sprint Lawyer 3.2 — AI-юрист workspace + draft editor + context inspector.
 */

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { legalOpsGet, legalOpsPost, pick } from "../business-ops/opsApi";

type Mode = { id: string; label_ru: string };

export function LawyerAiLawyerPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  clients: Record<string, unknown>[];
  cases: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  onRefresh: () => void;
  initial?: {
    clientId?: string;
    caseId?: string;
    prompt?: string;
    documentIds?: string[];
    contractId?: string;
    hearingId?: string;
    changeId?: string;
    contextLabels?: string[];
  };
}) {
  const [modes, setModes] = useState<Mode[]>([]);
  const [mode, setMode] = useState("consult");
  const [clientId, setClientId] = useState(props.initial?.clientId || "");
  const [caseId, setCaseId] = useState(props.initial?.caseId || "");
  const [docIds, setDocIds] = useState<string[]>(props.initial?.documentIds || []);
  const [prompt, setPrompt] = useState(props.initial?.prompt || "");
  const [exclude, setExclude] = useState<string[]>([]);
  const [context, setContext] = useState<Record<string, unknown> | null>(null);
  const [reply, setReply] = useState<Record<string, unknown> | null>(null);
  const [draftContent, setDraftContent] = useState("");
  const [draftId, setDraftId] = useState("");
  const [draftStatus, setDraftStatus] = useState("ai_draft");
  const [fileB64, setFileB64] = useState<string | null>(null);
  const [filename, setFilename] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);

  // sync handoff context arriving after mount (Lawyer 3.6 drawer handoff)
  useEffect(() => {
    if (!props.initial) return;
    if (props.initial.clientId) setClientId(props.initial.clientId);
    if (props.initial.caseId) setCaseId(props.initial.caseId);
    if (props.initial.documentIds?.length) setDocIds(props.initial.documentIds);
    if (props.initial.prompt) setPrompt(props.initial.prompt);
  }, [props.initial]);

  useEffect(() => {
    void legalOpsGet("/ai/catalog", props.headers).then((r) => {
      const items = (r as { modes?: Mode[] })?.modes;
      if (Array.isArray(items)) setModes(items);
    });
  }, [props.headers]);

  useEffect(() => {
    if (!clientId && !caseId) {
      setContext(null);
      return;
    }
    void legalOpsPost(
      "/ai/context",
      {
        client_id: clientId || undefined,
        case_id: caseId || undefined,
        document_ids: docIds,
        contract_id: props.initial?.contractId || undefined,
        hearing_id: props.initial?.hearingId || undefined,
        change_id: props.initial?.changeId || undefined,
        exclude_sources: exclude,
      },
      props.headers,
    ).then((r) => setContext(r as Record<string, unknown>));
  }, [clientId, caseId, docIds, exclude, props.headers, props.initial]);

  const inspector = (context?.inspector || {}) as Record<string, number>;
  const sources = Array.isArray(context?.sources) ? (context?.sources as { id: string; label: string; kind: string }[]) : [];

  async function run() {
    setBusy(true);
    setMsg("");
    try {
      const r = (await legalOpsPost(
        "/ai/lawyer/run",
        {
          mode,
          prompt,
          client_id: clientId || undefined,
          case_id: caseId || undefined,
          document_ids: docIds,
          contract_id: props.initial?.contractId || undefined,
          hearing_id: props.initial?.hearingId || undefined,
          change_id: props.initial?.changeId || undefined,
          exclude_sources: exclude,
          file_base64: fileB64 || undefined,
          filename: filename || undefined,
        },
        props.headers,
      )) as {
        ok?: boolean;
        reply?: Record<string, unknown>;
        draft?: { document_id?: string; content?: string; status?: string };
        message_ru?: string;
      };
      if (!r?.ok) {
        setMsg(r?.message_ru || "Ошибка AI-юриста");
        return;
      }
      setReply(r.reply || null);
      if (r.draft?.content) {
        setDraftContent(String(r.draft.content));
        setDraftId(String(r.draft.document_id || ""));
        setDraftStatus(String(r.draft.status || "ai_draft"));
      }
      props.onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function saveDraft(asNew: boolean) {
    if (!draftId && !asNew) {
      setMsg("Нет черновика");
      return;
    }
    if (asNew || !draftId) {
      const r = (await legalOpsPost(
        "/documents",
        {
          title: `AI Draft (сохранён)`,
          doc_type: "custom",
          status: draftStatus || "ai_draft",
          case_id: caseId || undefined,
          client_id: clientId || undefined,
          content: draftContent,
          payload: { content: draftContent, ai_draft: true, doc_status: draftStatus || "ai_draft" },
        },
        props.headers,
      )) as { ok?: boolean; item?: { id?: string }; message_ru?: string };
      setMsg(r?.ok ? "Сохранено как новый документ" : r?.message_ru || "Ошибка");
      if (r?.item?.id) setDraftId(String(r.item.id));
    } else {
      const r = (await legalOpsPost(
        `/ai/drafts/${draftId}`,
        { content: draftContent, status: draftStatus, confirm_overwrite: true, case_id: caseId || undefined, client_id: clientId || undefined },
        props.headers,
      )) as { ok?: boolean; message_ru?: string };
      setMsg(r?.ok ? "Черновик сохранён" : r?.message_ru || "Ошибка");
    }
    props.onRefresh();
  }

  async function regen() {
    if (!draftId) return;
    const sel = window.getSelection()?.toString() || "";
    const r = (await legalOpsPost(
      `/ai/drafts/${draftId}/regenerate`,
      { fragment: sel, instruction: "Переформулируй яснее" },
      props.headers,
    )) as { ok?: boolean; preview_content?: string; message_ru?: string };
    if (r?.preview_content) setDraftContent(String(r.preview_content));
    setMsg(r?.message_ru || "Фрагмент перегенерирован (не сохранён)");
  }

  const sourcesPanel = (reply?.sources_panel || {}) as {
    note_ru?: string;
    internal_documents?: unknown[];
    case_data?: unknown[];
    external_legal?: unknown[];
  };
  const classification = (reply?.source_classification || null) as {
    ados_facts?: string[];
    user_provided?: string[];
    external_note_ru?: string;
    data_gaps?: string[];
  } | null;

  return (
    <div className="grid gap-3" data-testid="lawyer-ai-lawyer-panel">
      <Card title="AI-юрист">
        <p className="eds-type-small mb-2 text-[var(--ew-muted)]">
          Диалоговый помощник с контекстом клиента, дела и документов. Создаёт AI Draft — не финальный юридический документ.
        </p>
        {props.initial?.contextLabels?.length ? (
          <div className="mb-2 rounded-md border border-[var(--ew-border)] p-2 eds-type-small" data-testid="lawyer-ai-handoff-context">
            <p className="font-medium">Контекст:</p>
            {props.initial.contextLabels.map((l) => (
              <div key={l}>✓ {l}</div>
            ))}
          </div>
        ) : null}
        <div className="grid gap-2 sm:grid-cols-3" data-testid="lawyer-ai-lawyer-context">
          <label className="eds-type-small">
            Клиент
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
            >
              <option value="">—</option>
              {props.clients.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Дело
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
            >
              <option value="">—</option>
              {props.cases.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "title", "case_number")}
                </option>
              ))}
            </select>
          </label>
          <label className="eds-type-small">
            Документы
            <select
              multiple
              className="mt-1 min-h-[64px] w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={docIds}
              onChange={(e) => setDocIds(Array.from(e.target.selectedOptions).map((o) => o.value))}
            >
              {props.documents
                .filter((d) => !caseId || pick(d, "case_id") === caseId || !pick(d, "case_id"))
                .map((d) => (
                  <option key={pick(d, "id")} value={pick(d, "id")}>
                    {pick(d, "title")}
                  </option>
                ))}
            </select>
          </label>
        </div>

        <div className="mt-3 flex flex-wrap gap-2" data-testid="lawyer-ai-lawyer-modes">
          {(modes.length ? modes : [{ id: "consult", label_ru: "Консультация" }]).map((m) => (
            <Button key={m.id} size="sm" variant={mode === m.id ? "secondary" : "ghost"} onClick={() => setMode(m.id)}>
              {m.label_ru}
            </Button>
          ))}
        </div>

        <label className="eds-type-small mt-3 block">
          Что необходимо сделать?
          <Input className="mt-1" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Подготовь проект претензии…" />
        </label>
        <label className="eds-type-small mt-2 block">
          Вложение
          <input
            type="file"
            className="mt-1 block w-full text-sm"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,.txt,text/*,image/*,application/pdf"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (!f) return;
              setFilename(f.name);
              const reader = new FileReader();
              reader.onload = () => {
                const s = String(reader.result || "");
                setFileB64(s.includes(",") ? s.split(",")[1] : s);
              };
              reader.readAsDataURL(f);
            }}
          />
        </label>
        <div className="mt-3">
          <Button data-testid="lawyer-ai-lawyer-run" disabled={!props.canOperate || busy || !prompt.trim()} onClick={() => void run()}>
            Запустить AI-юриста
          </Button>
        </div>
        {msg ? <p className="eds-type-small mt-2">{msg}</p> : null}
      </Card>

      <Card title="AI использует:">
        <div className="eds-type-small" data-testid="lawyer-ai-context-inspector">
          {caseId ? <div>Дело выбрано</div> : <div>Дело не выбрано</div>}
          <div>{inspector.documents || 0} документ(ов)</div>
          <div>{inspector.contracts || 0} договор(ов)</div>
          <div>{inspector.tasks || 0} задач</div>
          <div>{inspector.hearings || 0} заседаний</div>
          <div>{inspector.ai_analyses || 0} сохранённых AI-анализов</div>
        </div>
        <ul className="mt-2 max-h-40 overflow-auto eds-type-small">
          {sources.map((s) => (
            <li key={s.id} className="flex items-center justify-between gap-2 border-b border-[var(--ew-border)] py-1">
              <span>{s.label}</span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setExclude((ex) => (ex.includes(s.id) ? ex.filter((x) => x !== s.id) : [...ex, s.id]))}
              >
                {exclude.includes(s.id) ? "Вернуть" : "Убрать"}
              </Button>
            </li>
          ))}
        </ul>
      </Card>

      {reply ? (
        <Card title="Ответ / Sources">
          <p className="whitespace-pre-wrap eds-type-small">{String(reply.answer || "")}</p>
          <p className="eds-type-small mt-2 text-[var(--ew-muted)]">{String(reply.disclaimer || "")}</p>
          <div className="mt-3 eds-type-small" data-testid="lawyer-ai-sources-panel">
            <div className="font-medium">Sources / Evidence</div>
            <div>Внутренние документы: {Array.isArray(sourcesPanel.internal_documents) ? sourcesPanel.internal_documents.length : 0}</div>
            <div>Данные дела: {Array.isArray(sourcesPanel.case_data) ? sourcesPanel.case_data.length : 0}</div>
            <div>Внешние юридические источники: не подключены</div>
            <div className="text-[var(--ew-muted)]">{sourcesPanel.note_ru}</div>
          </div>
          {classification ? (
            <div className="mt-3 grid gap-2 eds-type-small sm:grid-cols-2" data-testid="lawyer-ai-source-classification">
              <div>
                <div className="font-medium">Факты из данных ADOS</div>
                {(classification.ados_facts || []).slice(0, 10).map((f) => (
                  <div key={f}>• {f}</div>
                ))}
                {!(classification.ados_facts || []).length ? <div className="text-[var(--ew-muted)]">Нет</div> : null}
              </div>
              <div>
                <div className="font-medium">Данные, предоставленные пользователем</div>
                {(classification.user_provided || []).map((f) => (
                  <div key={f}>• {f}</div>
                ))}
              </div>
              <div>
                <div className="font-medium">Внешние проверенные данные</div>
                <div className="text-[var(--ew-muted)]">{classification.external_note_ru || "Не подключены"}</div>
              </div>
              <div>
                <div className="font-medium">Недостающая информация (DATA GAP)</div>
                {(classification.data_gaps || []).map((f) => (
                  <div key={f}>• {f}</div>
                ))}
              </div>
            </div>
          ) : null}
        </Card>
      ) : null}

      {draftContent ? (
        <Card title="Редактор AI Draft">
          <div className="mb-2 flex flex-wrap gap-2">
            <select
              className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small"
              value={draftStatus}
              onChange={(e) => setDraftStatus(e.target.value)}
            >
              <option value="ai_draft">AI Draft</option>
              <option value="in_review">На проверке</option>
              <option value="approved">Одобрено</option>
              <option value="archived">Архив</option>
            </select>
            <Button size="sm" disabled={!props.canOperate} onClick={() => void regen()}>
              Перегенерировать выбранный фрагмент
            </Button>
            <Button size="sm" disabled={!props.canOperate} onClick={() => void saveDraft(false)}>
              Сохранить
            </Button>
            <Button size="sm" disabled={!props.canOperate} onClick={() => void saveDraft(true)}>
              Сохранить как новый документ
            </Button>
            <Button
              size="sm"
              disabled={!props.canOperate || !draftId}
              onClick={() =>
                void legalOpsPost(`/ai/drafts/${draftId}`, { case_id: caseId, client_id: clientId, confirm_overwrite: true }, props.headers).then(() =>
                  props.onRefresh(),
                )
              }
            >
              Прикрепить к делу / клиенту
            </Button>
          </div>
          <textarea
            data-testid="lawyer-ai-draft-editor"
            className="min-h-[220px] w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-2 font-mono text-sm"
            value={draftContent}
            onChange={(e) => setDraftContent(e.target.value)}
          />
        </Card>
      ) : null}
    </div>
  );
}

export function LawyerAiHistoryPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  items: Record<string, unknown>[];
  onRefresh: () => void;
  onOpen?: (item: Record<string, unknown>) => void;
}) {
  const [selected, setSelected] = useState<Record<string, unknown> | null>(null);

  async function archive(id: string) {
    await legalOpsPost(`/ai/analyses/${id}/archive`, { archive_reason: "user" }, props.headers);
    props.onRefresh();
  }

  async function replay(item: Record<string, unknown>) {
    const wk = pick(item, "workspace_kind");
    if (wk === "lawyer") {
      await legalOpsPost(
        "/ai/lawyer/run",
        {
          mode: pick(item, "mode") || "consult",
          prompt: pick(item, "question"),
          client_id: pick(item, "client_id") || undefined,
          case_id: pick(item, "case_id") || undefined,
        },
        props.headers,
      );
    } else {
      await legalOpsPost(
        "/ai/analyze",
        {
          action: pick(item, "action") || "summarize",
          target_type: pick(item, "target_type"),
          target_id: pick(item, "target_id"),
          question: pick(item, "question"),
          case_id: pick(item, "case_id") || undefined,
          client_id: pick(item, "client_id") || undefined,
        },
        props.headers,
      );
    }
    props.onRefresh();
  }

  return (
    <div data-testid="lawyer-ai-history-panel">
      <Card title="История AI-анализов">
        <div className="grid gap-2">
          {props.items.length === 0 ? <p className="eds-type-small">Пока нет сохранённых анализов</p> : null}
          {props.items.map((a) => (
            <div key={pick(a, "id")} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--ew-border)] p-2">
              <div className="eds-type-small">
                <div className="font-medium">
                  {pick(a, "workspace_kind") === "lawyer" ? "AI-юрист" : "AI-анализ"} · {pick(a, "action", "mode") || "—"}
                </div>
                <div className="text-[var(--ew-muted)]">{pick(a, "created_at")}</div>
                <div>{pick(a, "question")}</div>
              </div>
              <div className="flex gap-1">
                <Button size="sm" variant="ghost" onClick={() => { setSelected(a); props.onOpen?.(a); }}>
                  Открыть
                </Button>
                <Button size="sm" variant="ghost" disabled={!props.canOperate} onClick={() => void replay(a)}>
                  Повторить
                </Button>
                <Button size="sm" variant="ghost" disabled={!props.canOperate} onClick={() => void archive(pick(a, "id"))}>
                  Архивировать
                </Button>
              </div>
            </div>
          ))}
        </div>
        {selected ? (
          <pre className="eds-type-small mt-3 max-h-60 overflow-auto whitespace-pre-wrap rounded-md border border-[var(--ew-border)] p-2">
            {JSON.stringify(selected.result || selected, null, 2)}
          </pre>
        ) : null}
      </Card>
    </div>
  );
}
