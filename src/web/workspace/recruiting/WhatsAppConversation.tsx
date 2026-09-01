/**
 * WhatsApp conversation — incoming/outgoing, statuses, human send. No secrets.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { recruitingOpsGet, recruitingOpsPost } from "./recruitingApi";

type Msg = {
  id?: string;
  direction?: string;
  body?: string;
  created_at?: string;
  send_status?: string;
  delivered?: boolean;
  read?: boolean;
  failed?: boolean;
  provider_error?: { title?: string } | null;
  unresolved?: boolean;
};

type Props = {
  candidateId: string;
  candidateName?: string;
  candidatePhone?: string;
  headers: Record<string, string>;
};

function asRecord(json: unknown): Record<string, unknown> {
  return json && typeof json === "object" ? (json as Record<string, unknown>) : {};
}

function statusLabel(item: Msg): string {
  if (item.failed) return "ошибка";
  if (item.read) return "прочитано";
  if (item.delivered) return "доставлено";
  if (item.send_status === "SENT" || item.send_status === "sent") return "принято";
  if (item.send_status === "APPROVAL_REQUIRED") return "нужно подтверждение";
  return item.send_status || "—";
}

export function WhatsAppConversation({ candidateId, candidateName, candidatePhone, headers }: Props) {
  const [items, setItems] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [to, setTo] = useState(candidatePhone || "");
  const [error, setError] = useState<string | null>(null);
  const [approval, setApproval] = useState(false);

  const load = useCallback(async () => {
    const res = await recruitingOpsGet(`/whatsapp/conversations?candidate_id=${encodeURIComponent(candidateId)}`, headers);
    const json = asRecord(res.json);
    setItems(Array.isArray(json.items) ? (json.items as Msg[]) : []);
  }, [candidateId, headers]);

  useEffect(() => {
    void load();
  }, [load]);

  const compose = async (confirm: boolean) => {
    setError(null);
    setApproval(false);
    const res = await recruitingOpsPost(
      `/candidates/${candidateId}/whatsapp`,
      { to, body: text, confirm },
      headers,
    );
    const json = asRecord(res.json);
    if (json.approval_required && !confirm) {
      setApproval(true);
      return;
    }
    if (json.ok === false) {
      setError(String(json.message_ru || "Отправка не удалась"));
    }
    await load();
  };

  const aiDraft = async () => {
    const res = await recruitingOpsPost("/whatsapp/ai-draft", { candidate_id: candidateId, name: candidateName }, headers);
    const json = asRecord(res.json);
    setText(String(json.body || ""));
  };

  const lastIncoming = useMemo(() => items.find((item) => item.direction === "incoming"), [items]);

  return (
    <Card title="WhatsApp">
      <div className="grid gap-3" data-testid="whatsapp-conversation">
        <span data-testid="whatsapp-provider-badge">
          <Badge tone="info">WhatsApp</Badge>
        </span>
        <div data-testid="whatsapp-thread" className="grid gap-2">
          {items.length === 0 ? <p className="eds-type-helper">Сообщений нет.</p> : null}
          {items.map((item) => (
            <div
              key={item.id}
              className="rounded-md border border-[var(--ew-border)] p-2 eds-type-small"
              data-testid={item.direction === "incoming" ? "whatsapp-incoming" : "whatsapp-outgoing"}
            >
              <p>{item.direction === "incoming" ? "Входящее" : "Исходящее"}</p>
              <p>{item.body}</p>
              <p data-testid="whatsapp-timestamp">{item.created_at || "—"}</p>
              <p data-testid="whatsapp-status">{statusLabel(item)}</p>
              {item.provider_error?.title ? <p>{item.provider_error.title}</p> : null}
              {item.unresolved ? <p>Отправитель не сопоставлен с кандидатом</p> : null}
            </div>
          ))}
        </div>
        <Input placeholder="Телефон" value={to} onChange={(ev) => setTo(ev.target.value)} autoComplete="off" />
        <textarea
          className="min-h-20 w-full rounded-md border border-[var(--ew-border)] bg-[var(--eds-surface)] p-2 eds-type-small"
          data-testid="whatsapp-compose-text"
          value={text}
          onChange={(ev) => setText(ev.target.value)}
        />
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="secondary" data-testid="whatsapp-write" onClick={() => setText(text || "Здравствуйте!")}>
            Написать
          </Button>
          <Button
            size="sm"
            variant="secondary"
            data-testid="whatsapp-reply"
            onClick={() => setText(lastIncoming ? `Ответ: ${lastIncoming.body || ""}` : text)}
          >
            Ответить
          </Button>
          <Button size="sm" variant="secondary" data-testid="whatsapp-ai-draft" onClick={() => void aiDraft()}>
            Создать с AI
          </Button>
          <Button size="sm" data-testid="whatsapp-send" onClick={() => void compose(false)}>
            Отправить
          </Button>
        </div>
        {approval ? (
          <div data-testid="whatsapp-human-confirm">
            <p className="eds-type-helper">Нужно подтверждение человеком. Сообщение ещё не отправлено.</p>
            <Button size="sm" data-testid="whatsapp-confirm-send" onClick={() => void compose(true)}>
              Подтвердить отправку
            </Button>
          </div>
        ) : null}
        {error ? (
          <p className="eds-type-body text-[var(--eds-danger,#b91c1c)]" data-testid="whatsapp-error">
            {error}
          </p>
        ) : null}
      </div>
    </Card>
  );
}
