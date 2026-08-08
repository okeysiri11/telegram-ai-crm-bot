/**
 * Sprint 42.4 — AI Конструктор AI Консьержа 2.0
 * Пошаговый мастер на русском: имя → роль → стиль → навыки → модули → права → тест.
 */

import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { PLATFORM_BUILDER_API } from "../types";
import { term } from "@/i18n/platformGlossary";
import {
  CONCIERGE_V2_STEPS,
  V2_AVATARS,
  V2_LANGUAGES,
  V2_MODULES,
  V2_PERMISSIONS,
  V2_ROLES,
  V2_SKILLS,
  V2_STYLES,
  V2_VOICES,
  emptyConciergeV2,
  previewReply,
  v2ToApiDraft,
  type ConciergeV2Draft,
} from "./catalogV2";

function toggleList(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

function ChipGrid({
  items,
  selected,
  onToggle,
  single,
  activeId,
  onSelect,
}: {
  items: Array<{ id: string; name: string; emoji?: string }>;
  selected?: string[];
  onToggle?: (id: string) => void;
  single?: boolean;
  activeId?: string;
  onSelect?: (id: string) => void;
}) {
  return (
    <div className="pb-chip-grid">
      {items.map((item) => {
        const on = single ? activeId === item.id : Boolean(selected?.includes(item.id));
        return (
          <button
            key={item.id}
            type="button"
            className={`pb-chip${on ? " is-on" : ""}`}
            onClick={() => (single ? onSelect?.(item.id) : onToggle?.(item.id))}
          >
            {item.emoji ? `${item.emoji} ` : ""}
            {item.name}
          </button>
        );
      })}
    </div>
  );
}

export function ConciergeWizard() {
  const [step, setStep] = useState(0);
  const [orgId] = useState("org_demo");
  const [draft, setDraft] = useState<ConciergeV2Draft>(emptyConciergeV2());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [created, setCreated] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testIn, setTestIn] = useState("");
  const [testOut, setTestOut] = useState("");

  const avatar = V2_AVATARS.find((a) => a.id === draft.avatar) || V2_AVATARS[0];
  const style = V2_STYLES.find((s) => s.id === draft.style) || V2_STYLES[0];
  const roleLabel =
    draft.role === "custom" && draft.roleCustom
      ? draft.roleCustom
      : V2_ROLES.find((r) => r.id === draft.role)?.name || "Консьерж";

  function patch(p: Partial<ConciergeV2Draft>) {
    setDraft((d) => ({ ...d, ...p }));
    setCreated(null);
  }

  const canNext = useMemo(() => {
    if (step === 0) return draft.name.trim().length >= 2;
    if (step === 1) return Boolean(draft.role) && (draft.role !== "custom" || draft.roleCustom.trim());
    return true;
  }, [step, draft]);

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/concierge/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ organization_id: orgId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать сессию консьержа");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function finish() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      const apiDraft = v2ToApiDraft(draft);
      const patchRes = await fetch(`${PLATFORM_BUILDER_API}/concierge/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: 11, organization_id: orgId, draft: apiDraft }),
      });
      const patchBody = await patchRes.json();
      if (!patchRes.ok) throw new Error(patchBody.error || "Не удалось сохранить консьержа");

      const create = await fetch(`${PLATFORM_BUILDER_API}/concierge/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const createBody = await create.json();
      if (!create.ok) throw new Error(createBody.error || "Не удалось создать консьержа");
      setCreated(createBody);
      setStep(CONCIERGE_V2_STEPS.length - 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setBusy(false);
    }
  }

  function runTest() {
    const reply = previewReply(draft, testIn || "Привет");
    setTestOut(reply);
  }

  return (
    <PlatformBuilderLayout
      title="Конструктор AI Консьержа"
      subtitle="Пошаговая настройка главного помощника организации — без технических вкладок."
    >
      <div className="pb-wizard" data-testid="concierge-wizard-v2">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Badge tone="success">Мастер 2.0</Badge>
          <Badge>Один на организацию</Badge>
          <Link className="eds-type-caption text-[var(--eds-accent)]" to="/platform-builder/builder-studio">
            ← {term("builder")} AI
          </Link>
        </div>

        <ProgressIndicator current={step} total={CONCIERGE_V2_STEPS.length} />
        <BuilderStepNav steps={[...CONCIERGE_V2_STEPS]} current={step} onChange={setStep} />

        <div className="pb-wizard-grid">
          <Card title={CONCIERGE_V2_STEPS[step]} className="pb-card">
            {step === 0 ? (
              <div className="space-y-3">
                <label className="block eds-type-small">
                  Имя AI
                  <Input
                    className="mt-1"
                    placeholder="Например: Алекс"
                    value={draft.name}
                    onChange={(e) => patch({ name: e.target.value })}
                    data-testid="concierge-name"
                  />
                </label>
                <div>
                  <p className="eds-type-small font-medium mb-1">Аватар</p>
                  <ChipGrid
                    items={V2_AVATARS}
                    single
                    activeId={draft.avatar}
                    onSelect={(id) => patch({ avatar: id })}
                  />
                </div>
                <div>
                  <p className="eds-type-small font-medium mb-1">Голос</p>
                  <ChipGrid
                    items={V2_VOICES}
                    single
                    activeId={draft.voice}
                    onSelect={(id) => patch({ voice: id })}
                  />
                </div>
                <div>
                  <p className="eds-type-small font-medium mb-1">Язык</p>
                  <ChipGrid
                    items={V2_LANGUAGES}
                    single
                    activeId={draft.language}
                    onSelect={(id) => patch({ language: id })}
                  />
                </div>
                <label className="block eds-type-small">
                  Приветствие
                  <Input
                    className="mt-1"
                    value={draft.greeting}
                    onChange={(e) => patch({ greeting: e.target.value })}
                  />
                </label>
              </div>
            ) : null}

            {step === 1 ? (
              <div className="space-y-3">
                <ChipGrid
                  items={V2_ROLES}
                  single
                  activeId={draft.role || undefined}
                  onSelect={(id) => patch({ role: id })}
                />
                {draft.role === "custom" ? (
                  <Input
                    placeholder="Своя роль"
                    value={draft.roleCustom}
                    onChange={(e) => patch({ roleCustom: e.target.value })}
                  />
                ) : null}
              </div>
            ) : null}

            {step === 2 ? (
              <div className="space-y-3">
                <ChipGrid
                  items={V2_STYLES}
                  single
                  activeId={draft.style}
                  onSelect={(id) => patch({ style: id })}
                />
                <p className="eds-type-helper rounded-md border border-[var(--ew-border)] p-3">
                  Пример: {style.sample}
                </p>
              </div>
            ) : null}

            {step === 3 ? (
              <ChipGrid
                items={V2_SKILLS}
                selected={draft.skills}
                onToggle={(id) => patch({ skills: toggleList(draft.skills, id) })}
              />
            ) : null}

            {step === 4 ? (
              <ChipGrid
                items={V2_MODULES}
                selected={draft.modules}
                onToggle={(id) => patch({ modules: toggleList(draft.modules, id) })}
              />
            ) : null}

            {step === 5 ? (
              <ChipGrid
                items={V2_PERMISSIONS}
                selected={draft.permissions}
                onToggle={(id) => patch({ permissions: toggleList(draft.permissions, id) })}
              />
            ) : null}

            {step === 6 ? (
              <div className="space-y-3" data-testid="concierge-test-dialog">
                <p className="eds-type-helper">Напишите сообщение — AI ответит в стиле настроек.</p>
                <Input
                  placeholder="Сообщение пользователя…"
                  value={testIn}
                  onChange={(e) => setTestIn(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") runTest();
                  }}
                />
                <Button type="button" onClick={runTest}>
                  Получить ответ
                </Button>
                {testOut ? (
                  <div className="rounded-lg border border-[var(--eds-success)] p-3 eds-type-body">{testOut}</div>
                ) : (
                  <div className="rounded-lg border border-[var(--ew-border)] p-3 eds-type-helper">
                    {draft.greeting}
                  </div>
                )}
                {created ? (
                  <p className="eds-type-body text-[var(--eds-success)]" data-testid="concierge-created">
                    Консьерж создан. Можно пользоваться.
                  </p>
                ) : null}
              </div>
            ) : null}

            {error ? (
              <p className="mt-3 eds-type-caption text-[var(--eds-danger)]" role="alert">
                {error}
              </p>
            ) : null}

            <div className="mt-4 flex flex-wrap gap-2">
              <Button
                type="button"
                variant="secondary"
                disabled={step === 0}
                onClick={() => setStep((s) => Math.max(0, s - 1))}
              >
                {term("back")}
              </Button>
              {step < CONCIERGE_V2_STEPS.length - 1 ? (
                <Button
                  type="button"
                  className="ews-primary-cta"
                  disabled={!canNext}
                  onClick={() => setStep((s) => s + 1)}
                  data-testid="concierge-next"
                >
                  {term("next")}
                </Button>
              ) : (
                <Button
                  type="button"
                  className="ews-primary-cta"
                  disabled={busy || !draft.name.trim()}
                  onClick={() => void finish()}
                  data-testid="concierge-finish"
                >
                  {busy ? "Сохранение…" : term("done")}
                </Button>
              )}
            </div>
          </Card>

          <Card title={term("preview")} className="pb-card pb-preview" data-testid="concierge-preview">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl" aria-hidden>
                {avatar.emoji}
              </span>
              <div>
                <p className="eds-type-section">{draft.name.trim() || "AI Консьерж"}</p>
                <p className="eds-type-helper">
                  {roleLabel} · {style.name}
                </p>
              </div>
            </div>
            <p className="eds-type-body rounded-md bg-[var(--eds-surface-muted,transparent)] p-3 border border-[var(--ew-border)]">
              {draft.greeting}
            </p>
            <ul className="mt-3 space-y-1 eds-type-helper">
              <li>Навыки: {draft.skills.length || 0}</li>
              <li>Модули: {draft.modules.length || 0}</li>
              <li>Права: {draft.permissions.length || 0}</li>
              <li>Язык: {V2_LANGUAGES.find((l) => l.id === draft.language)?.name}</li>
            </ul>
          </Card>
        </div>
      </div>
    </PlatformBuilderLayout>
  );
}
