/**
 * Sprint Lawyer 3.2 — AI-анализ panel (object/document analysis).
 */

import { useEffect, useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { legalOpsGet, legalOpsPost, pick } from "../business-ops/opsApi";

type Action = { id: string; label_ru: string };

const SECTIONS: { key: string; label: string }[] = [
  { key: "summary", label: "Краткий вывод" },
  { key: "facts", label: "Факты" },
  { key: "key_terms", label: "Ключевые условия" },
  { key: "risks", label: "Риски" },
  { key: "deadlines", label: "Сроки" },
  { key: "obligations", label: "Обязательства" },
  { key: "contradictions", label: "Противоречия" },
  { key: "missing_data", label: "Нехватающие данные" },
  { key: "sources", label: "Источники / основания" },
  { key: "recommended_actions", label: "Рекомендуемые действия" },
];

function renderValue(v: unknown): string {
  if (v == null) return "—";
  if (typeof v === "string") return v;
  if (Array.isArray(v)) {
    return v
      .map((x) => {
        if (typeof x === "string") return `• ${x}`;
        if (x && typeof x === "object") {
          const o = x as Record<string, unknown>;
          if (o.date) return `• ${o.date}${o.note || o.context ? ` — ${o.note || o.context}` : ""}`;
          if (o.label_ru) return `• ${o.label_ru}${o.note ? ` (${o.note})` : o.verified === false ? " (Источник не подтвержден)" : ""}`;
          return `• ${JSON.stringify(x)}`;
        }
        return `• ${String(x)}`;
      })
      .join("\n");
  }
  return JSON.stringify(v, null, 2);
}

export function LawyerAiAnalysisPanel(props: {
  headers: Record<string, string>;
  canOperate: boolean;
  clients: Record<string, unknown>[];
  cases: Record<string, unknown>[];
  contracts: Record<string, unknown>[];
  documents: Record<string, unknown>[];
  onRefresh: () => void;
  onHandoff?: (payload: { analysisId: string; caseId?: string; clientId?: string; question?: string }) => void;
}) {
  const [actions, setActions] = useState<Action[]>([]);
  const [targetType, setTargetType] = useState("case");
  const [targetId, setTargetId] = useState("");
  const [clientId, setClientId] = useState("");
  const [caseId, setCaseId] = useState("");
  const [question, setQuestion] = useState("");
  const [pasted, setPasted] = useState("");
  const [fileB64, setFileB64] = useState<string | null>(null);
  const [filename, setFilename] = useState("");
  const [mime, setMime] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [analysisId, setAnalysisId] = useState("");

  useEffect(() => {
    void legalOpsGet("/ai/catalog", props.headers).then((r) => {
      const items = (r as { actions?: Action[] })?.actions;
      if (Array.isArray(items)) setActions(items);
    });
  }, [props.headers]);

  const targetOptions = useMemo(() => {
    if (targetType === "contract") return props.contracts;
    if (targetType === "document") return props.documents;
    if (targetType === "client") return props.clients;
    if (targetType === "case") return props.cases;
    return [];
  }, [targetType, props]);

  async function run(actionId: string) {
    setBusy(true);
    setMsg("");
    try {
      const body: Record<string, unknown> = {
        action: actionId,
        target_type: targetType,
        target_id: targetId || undefined,
        client_id: clientId || undefined,
        case_id: caseId || (targetType === "case" ? targetId : undefined) || undefined,
        question: question || undefined,
        text: pasted || undefined,
        filename: filename || undefined,
        mime_type: mime || undefined,
        file_base64: fileB64 || undefined,
      };
      const r = (await legalOpsPost("/ai/analyze", body, props.headers)) as {
        ok?: boolean;
        analysis?: Record<string, unknown>;
        item?: { id?: string };
        message_ru?: string;
      };
      if (!r?.ok) {
        setMsg(r?.message_ru || "Ошибка анализа");
        return;
      }
      setAnalysis(r.analysis || null);
      setAnalysisId(String(r.item?.id || r.analysis?.analysis_id || ""));
      props.onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function followUp(action: string, extra: Record<string, unknown> = {}) {
    if (!analysisId) {
      setMsg("Сначала выполните анализ");
      return;
    }
    const r = (await legalOpsPost(
      `/ai/analyses/${analysisId}/actions`,
      { action, confirm: true, case_id: caseId || undefined, client_id: clientId || undefined, ...extra },
      props.headers,
    )) as { ok?: boolean; message_ru?: string };
    setMsg(r?.ok ? `Готово: ${action}` : r?.message_ru || "Ошибка");
    if (r?.ok) props.onRefresh();
    if (r?.ok && action === "handoff_lawyer" && props.onHandoff) {
      props.onHandoff({
        analysisId,
        caseId: caseId || undefined,
        clientId: clientId || undefined,
        question: question || undefined,
      });
    }
  }

  return (
    <div className="grid gap-3" data-testid="lawyer-ai-analysis-panel">
      <Card title="AI-анализ">
        <p className="eds-type-small mb-2 text-[var(--ew-muted)]">
          Анализ конкретного объекта или документа. Отличается от AI-юриста (диалоговый помощник с контекстом дела).
        </p>
        <div className="grid gap-2 sm:grid-cols-2" data-testid="lawyer-ai-form">
          <label className="eds-type-small">
            Источник
            <select
              className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={targetType}
              onChange={(e) => {
                setTargetType(e.target.value);
                setTargetId("");
              }}
            >
              <option value="case">Дело</option>
              <option value="client">Клиент</option>
              <option value="document">Документ</option>
              <option value="contract">Договор</option>
              <option value="text">Вставленный текст / файл</option>
            </select>
          </label>
          {targetType !== "text" ? (
            <label className="eds-type-small">
              Объект Legal CRM
              <select
                className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
              >
                <option value="">Выберите</option>
                {targetOptions.map((c) => (
                  <option key={pick(c, "id")} value={pick(c, "id")}>
                    {pick(c, "title", "name", "case_number") || pick(c, "id")}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <label className="eds-type-small">
            Клиент (опц.)
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
            Дело (опц.)
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
          <label className="eds-type-small sm:col-span-2">
            Вопрос
            <Input className="mt-1" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Что проверить?" />
          </label>
          <label className="eds-type-small sm:col-span-2">
            Вставить текст
            <textarea
              className="mt-1 min-h-[80px] w-full rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1"
              value={pasted}
              onChange={(e) => setPasted(e.target.value)}
            />
          </label>
          <label className="eds-type-small sm:col-span-2">
            Вложение (PDF/DOC/JPG/PNG/WebP/TXT)
            <input
              data-testid="lawyer-ai-attach"
              type="file"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.webp,.txt,.md,text/*,image/*,application/pdf"
              className="mt-1 block w-full text-sm"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (!f) {
                  setFileB64(null);
                  return;
                }
                setFilename(f.name);
                setMime(f.type);
                const reader = new FileReader();
                reader.onload = () => {
                  const s = String(reader.result || "");
                  const b64 = s.includes(",") ? s.split(",")[1] : s;
                  setFileB64(b64);
                };
                reader.readAsDataURL(f);
              }}
            />
          </label>
        </div>
        <div className="mt-3 flex flex-wrap gap-2" data-testid="lawyer-ai-actions">
          {(actions.length
            ? actions
            : [{ id: "summarize", label_ru: "Кратко объяснить" }]
          ).map((a) => (
            <Button
              key={a.id}
              size="sm"
              variant={a.id === "summarize" ? "secondary" : "ghost"}
              disabled={!props.canOperate || busy}
              data-testid={a.id === "summarize" ? "lawyer-ai-submit" : `lawyer-ai-action-${a.id}`}
              onClick={() => void run(a.id)}
            >
              {a.label_ru}
            </Button>
          ))}
        </div>
        {msg ? <p className="eds-type-small mt-2 text-[var(--ew-danger)]">{msg}</p> : null}
      </Card>

      {analysis ? (
        <Card title="Структурированный результат">
          <div className="grid gap-3" data-testid="lawyer-ai-structured">
            {SECTIONS.map((s) => (
              <div key={s.key}>
                <div className="eds-type-small font-medium uppercase tracking-wide">{s.label}</div>
                <pre className="eds-type-small mt-1 whitespace-pre-wrap text-[var(--ew-fg)]">
                  {renderValue(analysis[s.key])}
                </pre>
              </div>
            ))}
            <p className="eds-type-small text-[var(--ew-muted)]">{String(analysis.disclaimer || "")}</p>
          </div>
          <div className="mt-3 flex flex-wrap gap-2" data-testid="lawyer-ai-result-actions">
            <Button size="sm" disabled={!props.canOperate} onClick={() => void followUp("save")}>
              Сохранить анализ
            </Button>
            <Button size="sm" disabled={!props.canOperate} onClick={() => void followUp("attach_case", { case_id: caseId || targetId })}>
              Прикрепить к делу
            </Button>
            <Button
              size="sm"
              disabled={!props.canOperate}
              onClick={() => {
                const d = Array.isArray(analysis.deadlines) ? (analysis.deadlines[0] as { date?: string }) : null;
                void followUp("create_task", { title: `Срок: ${d?.date || "из анализа"}`, due_at: d?.date ? `${d.date}T12:00:00+00:00` : undefined, deadline: d });
              }}
            >
              Создать задачу
            </Button>
            <Button
              size="sm"
              data-testid="lawyer-ai-add-calendar"
              disabled={!props.canOperate}
              onClick={() => {
                const d = Array.isArray(analysis.deadlines) ? (analysis.deadlines[0] as { date?: string }) : null;
                const date = d?.date || "2026-08-20";
                void followUp("create_calendar", { date, title: `Срок AI: ${date}` });
              }}
            >
              Добавить срок в календарь
            </Button>
            <Button size="sm" disabled={!props.canOperate} onClick={() => void followUp("create_draft", { draft_kind: "custom" })}>
              Создать проект документа
            </Button>
            <Button size="sm" disabled={!props.canOperate} onClick={() => void followUp("handoff_lawyer")}>
              Передать AI-юристу
            </Button>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
