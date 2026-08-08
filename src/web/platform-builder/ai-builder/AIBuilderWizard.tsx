import { useMemo, useState } from "react";
import { Badge, Button, Card, Checkbox, Input, Switch, Tooltip } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { useAcademyStore } from "../managers/academyStore";
import { PLATFORM_BUILDER_API } from "../types";
import {
  AGENT_COUNTS,
  AI_WIZARD_STEPS,
  COMMUNICATION_STYLES,
  KNOWLEDGE_SOURCES,
  NAME_SUGGESTIONS,
  PERMISSIONS,
  PROFESSIONS,
  SKILLS,
  SPECIALIZATION_TREE,
  WHY_MULTI,
  emptyAgent,
  type AgentDraft,
  type HelpBits,
  type SpecNode,
} from "./catalog";

function makeHelp(purpose: string, benefits: string, example: string, what = ""): HelpBits {
  return {
    shortDescription: what || purpose,
    purpose,
    benefits,
    example,
    businessValue: benefits,
    tooltip: purpose,
    moreInformation: `${purpose} ${benefits}`,
  };
}

function toHelpContent(h: HelpBits) {
  return {
    shortDescription: h.shortDescription,
    detailedExplanation: h.moreInformation,
    example: h.example,
    popup: { title: h.shortDescription, body: h.purpose },
    tooltip: h.tooltip,
    purpose: h.purpose,
    benefits: h.benefits,
    typicalUse: h.example,
    businessValue: h.businessValue,
  };
}

function toggleList(list: string[], id: string): string[] {
  return list.includes(id) ? list.filter((x) => x !== id) : [...list, id];
}

function SpecTree({
  nodes,
  selected,
  onToggle,
  depth = 0,
}: {
  nodes: SpecNode[];
  selected: string[];
  onToggle: (id: string) => void;
  depth?: number;
}) {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  return (
    <ul className="space-y-1" style={{ marginLeft: depth * 12 }}>
      {nodes.map((node) => {
        const expanded = open[node.id] ?? depth < 1;
        return (
          <li key={node.id}>
            <div className="flex items-center gap-2">
              {node.children?.length ? (
                <button
                  type="button"
                  className="eds-type-caption text-[var(--eds-primary)]"
                  onClick={() => setOpen((s) => ({ ...s, [node.id]: !expanded }))}
                >
                  {expanded ? "▾" : "▸"}
                </button>
              ) : (
                <span className="w-3" />
              )}
              <label className="inline-flex items-center gap-2 eds-type-small">
                <Checkbox
                  checked={selected.includes(node.id)}
                  onChange={() => onToggle(node.id)}
                />
                {node.name}
              </label>
            </div>
            {expanded && node.children?.length ? (
              <SpecTree nodes={node.children} selected={selected} onToggle={onToggle} depth={depth + 1} />
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

export function AIBuilderWizard({ embedded = false }: { embedded?: boolean } = {}) {
  const [step, setStep] = useState(0);
  const [countChoice, setCountChoice] = useState<number | "custom">(1);
  const [customCount, setCustomCount] = useState(4);
  const [activeSlot, setActiveSlot] = useState(0);
  const [agents, setAgents] = useState<AgentDraft[]>([emptyAgent(1)]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [created, setCreated] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mode = useAcademyStore((s) => s.mode);
  const learning = useAcademyStore((s) => s.isLearningEnabled("ai"));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const guided = learning && mode === "guided_learning";

  const agent = agents[activeSlot] || agents[0];
  const tree = SPECIALIZATION_TREE[agent?.profession || ""] || SPECIALIZATION_TREE.default;

  const help = useMemo(() => {
    const title = AI_WIZARD_STEPS[step];
    if (step === 2 && agent?.profession) {
      const p = PROFESSIONS.find((x) => x.id === agent.profession);
      if (p) return toHelpContent(p.help);
    }
    return toHelpContent(
      makeHelp(
        `Этот экран помогает настроить «${title}».`,
        "Чёткие настройки делают AI-специалиста понятнее и удобнее.",
        `Пример: завершите «${title}» перед следующим шагом.`,
        title,
      ),
    );
  }, [step, agent?.profession]);

  function resizeTeam(n: number) {
    setAgents(Array.from({ length: n }, (_, i) => emptyAgent(i + 1)));
    setActiveSlot(0);
    setCreated(null);
    setSessionId(null);
  }

  function applyCount(value: number | "custom", custom = customCount) {
    setCountChoice(value);
    const n = value === "custom" ? Math.min(50, Math.max(1, custom)) : value;
    resizeTeam(n);
  }

  function patchAgent(patch: Partial<AgentDraft>) {
    setAgents((prev) => prev.map((a, i) => (i === activeSlot ? { ...a, ...patch } : a)));
  }

  function patchPersonality(patch: Partial<AgentDraft["personality"]>) {
    setAgents((prev) =>
      prev.map((a, i) =>
        i === activeSlot ? { ...a, personality: { ...a.personality, ...patch } } : a,
      ),
    );
  }

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/ai-builder/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        agent_count: countChoice === "custom" ? "custom" : countChoice,
        custom_count: countChoice === "custom" ? customCount : undefined,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать сессию");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function syncAndCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      const payload = {
        step: 10,
        agents: agents.map((a) => ({
          slot: a.slot,
          name: a.name,
          name_gender: a.nameGender,
          profession: a.profession === "custom" ? a.professionCustom || "custom" : a.profession,
          profession_custom: a.professionCustom,
          specialization: a.specialization,
          knowledge: a.knowledge,
          skills: a.skills,
          permissions: a.permissions,
          personality: {
            gender: a.personality.gender,
            communication_style: a.personality.communicationStyle,
            professional_tone: a.personality.professionalTone,
            conversation_style: a.personality.conversationStyle,
          },
        })),
      };
      const patch = await fetch(`${PLATFORM_BUILDER_API}/ai-builder/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const patchBody = await patch.json();
      if (!patch.ok) throw new Error(patchBody.error || "Не удалось сохранить configuration");

      const create = await fetch(`${PLATFORM_BUILDER_API}/ai-builder/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const createBody = await create.json();
      if (!create.ok) throw new Error(createBody.error || "Не удалось создать agents");
      setCreated(createBody);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Что-то пошло не так");
    } finally {
      setBusy(false);
    }
  }

  const styleSample =
    COMMUNICATION_STYLES.find((s) => s.id === agent.personality.communicationStyle)?.sample ||
    COMMUNICATION_STYLES[0].sample;

  const body = (
      <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Badge>Работает</Badge>
        <Badge>Академия · {mode}</Badge>
        <Switch checked={learning} onChange={(v) => toggleLearning("ai", v)} label="Режим обучения" />
      </div>

      <ProgressIndicator current={step} total={AI_WIZARD_STEPS.length} />
      <BuilderStepNav steps={[...AI_WIZARD_STEPS]} current={step} onChange={setStep} />

      {agents.length > 1 ? (
        <div className="flex flex-wrap gap-2">
          {agents.map((a, i) => (
            <Button key={a.slot} variant={i === activeSlot ? "primary" : "ghost"} onClick={() => setActiveSlot(i)}>
              Специалист {a.slot}
              {a.name ? `: ${a.name}` : ""}
            </Button>
          ))}
        </div>
      ) : null}

      <div className="eds-grid eds-grid--dashboard">
        <Card title={AI_WIZARD_STEPS[step]}>
          {step === 0 ? (
            <div className="space-y-4">
              <p className="eds-type-small text-[var(--eds-text-muted)]">{WHY_MULTI.summary}</p>
              <div className="flex flex-wrap gap-2">
                {AGENT_COUNTS.map((c) => (
                  <Button
                    key={String(c.value)}
                    variant={countChoice === c.value ? "primary" : "secondary"}
                    onClick={() => applyCount(c.value)}
                  >
                    {c.label}
                  </Button>
                ))}
              </div>
              {countChoice === "custom" ? (
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={customCount}
                  onChange={(e) => {
                    const n = Number(e.target.value) || 1;
                    setCustomCount(n);
                    applyCount("custom", n);
                  }}
                />
              ) : null}
              <div className="rounded-lg border border-[var(--eds-border)] p-4 eds-anim-fade">
                <p className="eds-type-caption mb-2">{WHY_MULTI.title}</p>
                <div className="flex flex-wrap gap-2">
                  {WHY_MULTI.members.map((m) => (
                    <Badge key={m}>{m}</Badge>
                  ))}
                </div>
                <p className="mt-2 eds-type-caption text-[var(--eds-text-muted)]">
                  Наглядная схема команды AI — независимые специалисты работают вместе.
                </p>
                <ul className="mt-2 space-y-1 eds-type-small">
                  {WHY_MULTI.points.map((p) => (
                    <li key={p}>• {p}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}

          {step === 1 ? (
            <div className="space-y-3">
              <p className="eds-type-small">У каждого AI-агента должно быть имя. Выберите подсказку или введите своё.</p>
              <div className="flex flex-wrap gap-2">
                {([
                  ["male", "Мужской"],
                  ["female", "Женский"],
                  ["neutral", "Нейтральный"],
                ] as const).map(([g, label]) => (
                  <Button
                    key={g}
                    variant={agent.nameGender === g ? "primary" : "ghost"}
                    onClick={() => patchAgent({ nameGender: g })}
                  >
                    {label}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {NAME_SUGGESTIONS[agent.nameGender].map((n) => (
                  <Button key={n} variant="secondary" onClick={() => patchAgent({ name: n })}>
                    {n}
                  </Button>
                ))}
              </div>
              <Input
                placeholder="Своё имя (обязательно)"
                value={agent.name}
                onChange={(e) => patchAgent({ name: e.target.value })}
              />
              <Card title="Живой предпросмотр">
                <p className="eds-type-small">
                  Здравствуйте, я <strong>{agent.name || "…"}</strong> — готов помочь вашей команде.
                </p>
              </Card>
            </div>
          ) : null}

          {step === 2 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {PROFESSIONS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => patchAgent({ profession: p.id, specialization: [] })}
                  className={`rounded-md border p-3 text-left eds-anim-fade ${
                    agent.profession === p.id
                      ? "border-[var(--eds-primary)] bg-[var(--eds-primary-soft)]"
                      : "border-[var(--eds-border)]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <strong className="eds-type-small">{p.name}</strong>
                    <Tooltip label={p.help.tooltip}>
                      <span className="eds-type-caption text-[var(--eds-primary)]">Справка</span>
                    </Tooltip>
                  </div>
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{p.help.shortDescription}</p>
                </button>
              ))}
              {agent.profession === "custom" ? (
                <Input
                  className="sm:col-span-2"
                  placeholder="Опишите свою профессию"
                  value={agent.professionCustom}
                  onChange={(e) => patchAgent({ professionCustom: e.target.value })}
                />
              ) : null}
            </div>
          ) : null}

          {step === 3 ? (
            <div className="space-y-2">
              <p className="eds-type-small">Раскройте дерево и выберите одну или несколько специализаций.</p>
              <SpecTree
                nodes={tree}
                selected={agent.specialization}
                onToggle={(id) => patchAgent({ specialization: toggleList(agent.specialization, id) })}
              />
            </div>
          ) : null}

          {step === 4 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {KNOWLEDGE_SOURCES.map((k) => (
                <label key={k.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={agent.knowledge.includes(k.id)}
                      onChange={() => patchAgent({ knowledge: toggleList(agent.knowledge, k.id) })}
                    />
                    {k.name}
                  </span>
                  <p className="mt-1 text-[var(--eds-text-muted)]">{k.help.shortDescription}</p>
                  {guided ? (
                    <p className="mt-1 eds-type-caption">
                      Purpose: {k.help.purpose} · Benefits: {k.help.benefits} · {k.help.example}
                    </p>
                  ) : null}
                </label>
              ))}
            </div>
          ) : null}

          {step === 5 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {SKILLS.map((s) => (
                <label key={s.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={agent.skills.includes(s.id)}
                      onChange={() => patchAgent({ skills: toggleList(agent.skills, s.id) })}
                    />
                    {s.name}
                  </span>
                  <p className="mt-1 text-[var(--eds-text-muted)]">{s.help.purpose}</p>
                </label>
              ))}
            </div>
          ) : null}

          {step === 6 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {PERMISSIONS.map((p) => (
                <label key={p.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={agent.permissions.includes(p.id)}
                      onChange={() => patchAgent({ permissions: toggleList(agent.permissions, p.id) })}
                    />
                    {p.name}
                  </span>
                  <p className="mt-1 text-[var(--eds-text-muted)]">{p.help.purpose}</p>
                </label>
              ))}
            </div>
          ) : null}

          {step === 7 ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {(["male", "female", "neutral"] as const).map((g) => (
                  <Button
                    key={g}
                    variant={agent.personality.gender === g ? "primary" : "ghost"}
                    onClick={() => patchPersonality({ gender: g })}
                  >
                    Gender · {g}
                  </Button>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {COMMUNICATION_STYLES.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className={`rounded-md border p-3 text-left eds-type-small ${
                      agent.personality.communicationStyle === s.id
                        ? "border-[var(--eds-primary)]"
                        : "border-[var(--eds-border)]"
                    }`}
                    onClick={() => patchPersonality({ communicationStyle: s.id })}
                  >
                    <strong>{s.name}</strong>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">{s.sample}</p>
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {["formal", "balanced", "casual"].map((t) => (
                  <Button
                    key={t}
                    variant={agent.personality.professionalTone === t ? "primary" : "secondary"}
                    onClick={() => patchPersonality({ professionalTone: t })}
                  >
                    Тон · {({ formal: "формальный", balanced: "сбалансированный", casual: "неформальный" } as Record<string, string>)[t] || t}
                  </Button>
                ))}
              </div>
              <Card title="Пример диалога">
                <p className="eds-type-small text-[var(--eds-text-muted)]">
                  Вы: Поможете с приоритетами на сегодня?
                </p>
                <p className="mt-2 eds-type-small">
                  <strong>{agent.name || "AI"}:</strong> {styleSample}
                </p>
              </Card>
            </div>
          ) : null}

          {step === 8 ? (
            <div className="space-y-3">
              {agents.map((a) => (
                <Card key={a.slot} title={`Карточка AI · ${a.name || `Специалист ${a.slot}`}`}>
                  <ul className="space-y-1 eds-type-small">
                    <li>Имя: {a.name || "—"}</li>
                    <li>
                      Назначение:{" "}
                      {a.profession === "custom"
                        ? a.professionCustom || "Свой вариант"
                        : PROFESSIONS.find((p) => p.id === a.profession)?.name || "—"}
                    </li>
                    <li>Специализация: {a.specialization.join(", ") || "—"}</li>
                    <li>База знаний: {a.knowledge.join(", ") || "—"}</li>
                    <li>Навыки: {a.skills.join(", ") || "—"}</li>
                    <li>Права: {a.permissions.join(", ") || "—"}</li>
                    <li>
                      Личность: {a.personality.communicationStyle} · {a.personality.professionalTone}
                    </li>
                  </ul>
                </Card>
              ))}
            </div>
          ) : null}

          {step === 9 ? (
            <div className="space-y-3">
              <p className="eds-type-small">
                Создание зарегистрирует каждого AI-агента, сохранит конфигурацию и добавит их в реестр AI.
              </p>
              {error ? <p className="eds-type-small text-[var(--eds-danger)]">{error}</p> : null}
              {created ? (
                <Card title="Создано">
                  <p className="eds-type-small">
                    Зарегистрировано агентов: {(created.created_count as number) || 0}
                  </p>
                  <pre className="mt-2 max-h-48 overflow-auto eds-type-caption">
                    {JSON.stringify(created.agents, null, 2)}
                  </pre>
                </Card>
              ) : (
                <Button variant="primary" disabled={busy} onClick={() => void syncAndCreate()}>
                  {busy ? "Создание…" : "Создать AI-агента"}
                </Button>
              )}
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
              Назад
            </Button>
            <Button
              disabled={step >= AI_WIZARD_STEPS.length - 1}
              onClick={() => setStep((s) => Math.min(AI_WIZARD_STEPS.length - 1, s + 1))}
            >
              Далее
            </Button>
          </div>
        </Card>

        <HelpPanel help={help} guided={guided} />

        <Card title="Предпросмотр">
          <p className="eds-type-small">
            <strong>{agent.name || "Специалист без имени"}</strong>
          </p>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            {agent.profession || "Назначение не выбрано"} · {agent.specialization.length} спец. ·{" "}
            {agent.skills.length} навыков
          </p>
          <p className="mt-2 eds-type-small">{styleSample}</p>
        </Card>
      </div>
      </div>
  );

  if (embedded) return body;

  return (
    <PlatformBuilderLayout
      title="Конструктор AI-агентов"
      subtitle="Создайте AI-специалистов простым мастером — без технических знаний."
    >
      {body}
    </PlatformBuilderLayout>
  );
}
