/**
 * Candidate email composer — templates, preview, send. Password never shown.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { recruitingOpsGet, recruitingOpsPost } from "../business-ops/opsApi";

type Template = { id?: string; label_ru?: string; subject?: string; body?: string };
type HistoryItem = { id?: string; status?: string; subject?: string; body?: string; to?: string; delivered?: boolean };

type Props = {
  candidateId: string;
  candidateName?: string;
  candidateEmail?: string;
  headers: Record<string, string>;
  campaignId?: string;
};

function asRecord(json: unknown): Record<string, unknown> {
  return json && typeof json === "object" ? (json as Record<string, unknown>) : {};
}

export function CandidateEmailComposer({ candidateId, candidateName, candidateEmail, headers, campaignId }: Props) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templateId, setTemplateId] = useState("intro");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [to, setTo] = useState(candidateEmail || "");
  const [preview, setPreview] = useState("");
  const [sendState, setSendState] = useState<"idle" | "sending" | "sent" | "failed">("idle");
  const [failure, setFailure] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const approvalRequired = Boolean(campaignId);

  const load = useCallback(async () => {
    const [tpl, hist] = await Promise.all([
      recruitingOpsGet("/email/templates", headers),
      recruitingOpsGet(`/candidates/${candidateId}/emails`, headers),
    ]);
    const tplJson = asRecord(tpl.json);
    const items = Array.isArray(tplJson.items) ? (tplJson.items as Template[]) : [];
    setTemplates(items);
    const histJson = asRecord(hist.json);
    setHistory(Array.isArray(histJson.items) ? (histJson.items as HistoryItem[]) : []);
  }, [candidateId, headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const selected = useMemo(() => templates.find((t) => t.id === templateId) || templates[0], [templates, templateId]);

  const runPreview = async () => {
    const res = await recruitingOpsPost(
      "/email/preview",
      { template_id: templateId, candidate_id: candidateId, context: { name: candidateName, vacancy: "" } },
      headers,
    );
    const json = asRecord(res.json);
    setSubject(String(json.subject || selected?.subject || ""));
    setBody(String(json.body || selected?.body || ""));
    setPreview(String(json.body || selected?.body || ""));
  };

  const send = async () => {
    if (approvalRequired) return;
    setSendState("sending");
    setFailure(null);
    const res = await recruitingOpsPost(
      `/candidates/${candidateId}/email`,
      { to, subject, body, template_id: templateId, campaign_id: campaignId || undefined },
      headers,
    );
    const json = asRecord(res.json);
    if (json.ok && (json.item as { status?: string } | undefined)?.status === "SENT") {
      setSendState("sent");
    } else {
      setSendState("failed");
      setFailure(String(json.message_ru || "Отправка не удалась"));
    }
    await load();
  };

  return (
    <Card title="Письмо кандидату">
      <div className="grid gap-3" data-testid="candidate-email-composer">
        <label className="eds-type-small">
          Шаблон
          <select
            className="mt-1 w-full rounded-md border border-[var(--ew-border)] bg-[var(--eds-surface)] p-2"
            data-testid="email-template-select"
            value={templateId}
            onChange={(ev) => setTemplateId(ev.target.value)}
          >
            {(templates.length ? templates : [{ id: "intro", label_ru: "Знакомство" }, { id: "interview", label_ru: "Интервью" }]).map((tpl) => (
              <option key={tpl.id} value={tpl.id}>
                {tpl.label_ru || tpl.id}
              </option>
            ))}
          </select>
        </label>
        <label className="eds-type-small">
          Получатель
          <Input value={to} onChange={(ev) => setTo(ev.target.value)} autoComplete="off" />
        </label>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" onClick={() => void runPreview()}>
            Предпросмотр
          </Button>
        </div>
        <div data-testid="email-preview" className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small whitespace-pre-wrap">
          {preview || subject || "Предпросмотр появится здесь."}
        </div>
        {approvalRequired ? (
          <p className="eds-type-helper" data-testid="email-campaign-approval">
            Рассылка кампании требует согласования. Отправка заблокирована до Approve.
          </p>
        ) : (
          <Button size="sm" data-testid="email-send" onClick={() => void send()} disabled={sendState === "sending"}>
            Отправить
          </Button>
        )}
        <div data-testid="email-send-state">
          {sendState === "sending" ? "Отправка..." : null}
          {sendState === "sent" ? <Badge tone="success">SMTP принял письмо. Доставка не подтверждена.</Badge> : null}
        </div>
        {sendState === "failed" || failure ? (
          <p className="eds-type-body text-[var(--eds-danger,#b91c1c)]" data-testid="email-failure-state">
            {failure || "Ошибка отправки"}
          </p>
        ) : null}
        <div data-testid="email-history">
          <p className="eds-type-caption">История</p>
          {history.length === 0 ? <p className="eds-type-helper">Писем ещё нет.</p> : null}
          {history.map((item) => (
            <p key={item.id} className="eds-type-small">
              {item.status} — {item.subject || item.body} {item.delivered ? "DELIVERED" : "не DELIVERED"}
            </p>
          ))}
        </div>
      </div>
    </Card>
  );
}
