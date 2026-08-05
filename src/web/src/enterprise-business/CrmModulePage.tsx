/**
 * Sprint 30.8 — CRM module (Russian): clients, companies, contacts, leads, deals, pipeline, timeline, notes, attachments.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import {
  PIPELINE_STAGES,
  addCrmAttachment,
  addCrmNote,
  createCrmClient,
  createCrmDeal,
  createCrmLead,
  hydrateCrm,
  readCrmCache,
  upsertLocalCompany,
  upsertLocalContact,
  type CrmState,
} from "./crmApi";

const TABS = [
  { id: "clients", label: "Клиенты" },
  { id: "companies", label: "Компании" },
  { id: "contacts", label: "Контакты" },
  { id: "leads", label: "Лиды" },
  { id: "deals", label: "Сделки" },
  { id: "pipelines", label: "Воронка" },
  { id: "activity", label: "Активность" },
  { id: "notes", label: "Заметки" },
  { id: "attachments", label: "Вложения" },
] as const;

export function CrmModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "clients";
  const [state, setState] = useState<CrmState>(() => readCrmCache());
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ a: "", b: "", c: "", d: "" });

  const refresh = useCallback(async () => {
    setBusy(true);
    const next = await hydrateCrm();
    setState(next);
    setBusy(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const active = TABS.some((t) => t.id === view) ? view : "clients";

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  const pipelineGroups = useMemo(() => {
    const map: Record<string, typeof state.deals> = {};
    for (const s of PIPELINE_STAGES) map[s] = [];
    for (const d of state.deals) {
      const key = PIPELINE_STAGES.includes(d.stage as (typeof PIPELINE_STAGES)[number]) ? d.stage : "prospect";
      map[key] = [...(map[key] || []), d];
    }
    return map;
  }, [state.deals]);

  return (
    <BusinessModuleShell
      title="CRM"
      subtitle="Клиенты · компании · лиды · сделки · воронка"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source={state.source === "api" ? "API · /api/auto/v1/crm" : "Workspace cache"}
      testId="crm-module"
      actions={
        <Button size="sm" variant="secondary" disabled={busy} onClick={() => void refresh()}>
          {busy ? "Синхронизация…" : "Обновить"}
        </Button>
      }
    >
      {active === "clients" ? (
        <section className="space-y-3">
          <Card title="Новый клиент">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Имя" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Фамилия" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Input placeholder="Email" value={form.c} onChange={(e) => setForm({ ...form, c: e.target.value })} />
              <Input placeholder="Телефон" value={form.d} onChange={(e) => setForm({ ...form, d: e.target.value })} />
              <Button
                size="sm"
                onClick={async () => {
                  if (!form.a.trim()) return;
                  await createCrmClient({
                    firstName: form.a.trim(),
                    lastName: form.b.trim(),
                    email: form.c.trim(),
                    phone: form.d.trim(),
                  });
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Создать
              </Button>
            </div>
          </Card>
          <div className="eds-grid eds-grid--dashboard">
            {state.clients.map((c) => (
              <Card key={c.id} title={`${c.firstName} ${c.lastName}`.trim() || c.id}>
                <p className="eds-type-helper">{c.email || "—"} · {c.phone || "—"}</p>
                <Badge>{c.segment}</Badge>
              </Card>
            ))}
            {!state.clients.length ? <p className="eds-type-helper">Нет клиентов — создайте первого или подключите API.</p> : null}
          </div>
        </section>
      ) : null}

      {active === "companies" ? (
        <section className="space-y-3">
          <Card title="Новая компания">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Отрасль" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim()) return;
                  upsertLocalCompany(form.a.trim(), form.b.trim() || undefined);
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Создать
              </Button>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.companies.map((c) => (
              <li key={c.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                <strong>{c.name}</strong>
                {c.industry ? <span className="eds-type-helper"> · {c.industry}</span> : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {active === "contacts" ? (
        <section className="space-y-3">
          <Card title="Новый контакт">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Имя" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Email" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Input placeholder="Телефон" value={form.c} onChange={(e) => setForm({ ...form, c: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim()) return;
                  upsertLocalContact({ name: form.a.trim(), email: form.b.trim(), phone: form.c.trim() });
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Создать
              </Button>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.contacts.map((c) => (
              <li key={c.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                <strong>{c.name}</strong> · {c.email} · {c.phone}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {active === "leads" ? (
        <section className="space-y-3">
          <Card title="Новый лид">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Источник" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Input placeholder="Заметки" value={form.c} onChange={(e) => setForm({ ...form, c: e.target.value })} />
              <Button
                size="sm"
                onClick={async () => {
                  if (!form.a.trim()) return;
                  await createCrmLead({ title: form.a.trim(), source: form.b.trim() || "web", notes: form.c.trim() });
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Создать
              </Button>
            </div>
          </Card>
          <div className="eds-grid eds-grid--dashboard">
            {state.leads.map((l) => (
              <Card key={l.id} title={l.title} status={<Badge>{l.status}</Badge>}>
                <p className="eds-type-helper">{l.source} · score {l.score}</p>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      {active === "deals" ? (
        <section className="space-y-3">
          <Card title="Новая сделка">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Название" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Input placeholder="Сумма" value={form.b} onChange={(e) => setForm({ ...form, b: e.target.value })} />
              <Button
                size="sm"
                onClick={async () => {
                  if (!form.a.trim()) return;
                  await createCrmDeal({
                    title: form.a.trim(),
                    stage: "prospect",
                    amount: Number(form.b) || 0,
                  });
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Создать
              </Button>
            </div>
          </Card>
          <div className="eds-grid eds-grid--dashboard">
            {state.deals.map((d) => (
              <Card key={d.id} title={d.title} status={<Badge>{d.stage}</Badge>}>
                <p className="eds-type-helper">{d.amount.toLocaleString("ru-RU")} ₽</p>
              </Card>
            ))}
          </div>
        </section>
      ) : null}

      {active === "pipelines" ? (
        <section className="grid gap-3 lg:grid-cols-3 xl:grid-cols-4">
          {PIPELINE_STAGES.map((stage) => (
            <Card key={stage} title={stage}>
              <ul className="space-y-2 eds-type-small">
                {(pipelineGroups[stage] || []).map((d) => (
                  <li key={d.id} className="rounded border border-[var(--eds-border)] px-2 py-1">
                    {d.title}
                  </li>
                ))}
                {!(pipelineGroups[stage] || []).length ? <li className="eds-type-helper">Пусто</li> : null}
              </ul>
            </Card>
          ))}
        </section>
      ) : null}

      {active === "activity" ? (
        <ul className="space-y-2">
          {state.activities.map((a) => (
            <li key={a.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
              <Badge>{a.kind}</Badge> {a.title}
              <span className="block eds-type-helper">{new Date(a.at).toLocaleString("ru-RU")}</span>
            </li>
          ))}
          {!state.activities.length ? <p className="eds-type-helper">Лента пуста</p> : null}
        </ul>
      ) : null}

      {active === "notes" ? (
        <section className="space-y-3">
          <Card title="Заметка">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Текст" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim()) return;
                  addCrmNote("crm", "workspace", form.a.trim());
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Добавить
              </Button>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.notes.map((n) => (
              <li key={n.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                {n.body}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {active === "attachments" ? (
        <section className="space-y-3">
          <Card title="Вложение">
            <div className="flex flex-wrap gap-2">
              <Input placeholder="Имя файла" value={form.a} onChange={(e) => setForm({ ...form, a: e.target.value })} />
              <Button
                size="sm"
                onClick={() => {
                  if (!form.a.trim()) return;
                  addCrmAttachment("crm", "workspace", form.a.trim());
                  setForm({ a: "", b: "", c: "", d: "" });
                  setState(readCrmCache());
                }}
              >
                Прикрепить
              </Button>
            </div>
          </Card>
          <ul className="space-y-2">
            {state.attachments.map((a) => (
              <li key={a.id} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                {a.name}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </BusinessModuleShell>
  );
}
