/**
 * Public Vanguard career application — recruiting PROJECT website, not a vertical.
 */

import { useEffect, useMemo, useState } from "react";
import { Button, Card, Input } from "@/ui";
import { postWithRetry } from "./trackingRetry";

const APPLY = "/api/vanguard-site/v1/applications";
const EVENTS = "/api/vanguard-site/v1/events";

function visitorId(): string {
  const key = "vanguard_visitor_id";
  try {
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const next = crypto.randomUUID();
    localStorage.setItem(key, next);
    return next;
  } catch {
    return crypto.randomUUID();
  }
}

function sessionId(): string {
  const key = "vanguard_session_id";
  try {
    const existing = sessionStorage.getItem(key);
    if (existing) return existing;
    const next = crypto.randomUUID();
    sessionStorage.setItem(key, next);
    return next;
  } catch {
    return crypto.randomUUID();
  }
}

function utmFromSearch(): Record<string, string> {
  const params = new URLSearchParams(typeof window === "undefined" ? "" : window.location.search);
  const out: Record<string, string> = {};
  for (const key of ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "campaign_id"]) {
    const value = params.get(key);
    if (value) out[key] = value;
  }
  return out;
}

async function track(eventType: string, extra: Record<string, string> = {}) {
  const eventId = extra.event_id || crypto.randomUUID();
  const body = {
    event_type: eventType,
    event_id: eventId,
    visitor_id: visitorId(),
    session_id: sessionId(),
    timestamp: new Date().toISOString(),
    page: typeof window === "undefined" ? "/vanguard" : window.location.pathname + window.location.search,
    referrer: typeof document === "undefined" ? "" : document.referrer,
    landing_page: "/vanguard",
    ...utmFromSearch(),
    ...extra,
  };
  const result = await postWithRetry(EVENTS, body);
  if (!result.ok) {
    console.warn("vanguard tracking FAILED", eventType, result.delivery_status);
  }
}

function applicationIdempotencyKey(): string {
  const key = "vanguard_apply_idempotency";
  try {
    const existing = sessionStorage.getItem(key);
    if (existing) return existing;
    const next = crypto.randomUUID();
    sessionStorage.setItem(key, next);
    return next;
  } catch {
    return crypto.randomUUID();
  }
}

export function VanguardCareerPage() {
  const utm = useMemo(() => utmFromSearch(), []);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    country: "",
    preferred_language: "ru",
    unit: "",
    program: "",
    message: "",
  });
  const [started, setStarted] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [reference, setReference] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void track("page_view");
    void track("application_open");
  }, []);

  function markStart() {
    if (started) return;
    setStarted(true);
    void track("application_start");
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setStatus("Отправка…");
    const idempotencyKey = applicationIdempotencyKey();
    const payload = {
      ...form,
      unit_of_interest: form.unit,
      program_of_interest: form.program,
      application_message: form.message,
      source: "vanguard",
      project_key: "vanguard",
      visitor_id: visitorId(),
      session_id: sessionId(),
      page: "/vanguard",
      referrer: typeof document === "undefined" ? "" : document.referrer,
      landing_page: "/vanguard",
      submitted_at: new Date().toISOString(),
      idempotency_key: idempotencyKey,
      ...utm,
    };
    void track("application_submit");
    const res = await fetch(APPLY, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(payload),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok || json.ok === false) {
      setError(String(json.message_ru || json.error || "Заявка не принята рекрутингом"));
      setStatus(null);
      return;
    }
    try {
      sessionStorage.removeItem("vanguard_apply_idempotency");
    } catch {
      /* ignore */
    }
    setReference(String(json.reference || json.item?.external_id || ""));
    setStatus("APPLICATION RECEIVED");
    void track("application_success");
  }

  return (
    <main className="mx-auto max-w-xl p-6" data-testid="vanguard-career-page">
      <p className="eds-type-caption">Vanguard · Recruiting project website</p>
      <h1 className="eds-type-title mt-1">Заявка Vanguard</h1>
      <p className="eds-type-helper mt-2">
        Это публичный сайт проекта внутри Рекрутинга, не отдельная бизнес-вертикаль. Заявка уходит в Recruiting.
      </p>
      {reference ? (
        <Card title="Заявка принята" className="mt-4">
          <p data-testid="vanguard-application-received">APPLICATION RECEIVED</p>
          <p>
            Номер заявки: <strong data-testid="vanguard-reference">{reference}</strong>
          </p>
        </Card>
      ) : (
        <Card title="Анкета" className="mt-4">
          <form data-testid="vanguard-apply-form" className="grid gap-2" onSubmit={(e) => void onSubmit(e)}>
            <Input
              placeholder="Имя"
              value={form.first_name}
              onChange={(e) => {
                markStart();
                setForm({ ...form, first_name: e.target.value });
              }}
              required
            />
            <Input placeholder="Фамилия" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            <Input
              placeholder="Email"
              type="email"
              value={form.email}
              onChange={(e) => {
                markStart();
                setForm({ ...form, email: e.target.value });
              }}
              required
            />
            <Input placeholder="Страна" value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
            <Input placeholder="Язык" value={form.preferred_language} onChange={(e) => setForm({ ...form, preferred_language: e.target.value })} />
            <Input placeholder="Подразделение" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
            <Input placeholder="Программа / вакансия" value={form.program} onChange={(e) => setForm({ ...form, program: e.target.value })} />
            <Input placeholder="Почему вы откликаетесь" value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
            <Button type="submit" data-testid="vanguard-apply-submit">
              Отправить заявку
            </Button>
          </form>
          {status ? <p className="mt-2 eds-type-helper">{status}</p> : null}
          {error ? (
            <p className="mt-2 eds-type-body text-[var(--eds-danger,#b91c1c)]" data-testid="vanguard-apply-error">
              {error}
            </p>
          ) : null}
        </Card>
      )}
    </main>
  );
}
