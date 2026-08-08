import { useMemo, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { PLATFORM_BUILDER_API } from "../types";
import { COLLAB_STEPS, DEFAULT_SPECIALISTS, PRIORITIES } from "./catalog";

type Dict = Record<string, unknown>;

export function CollaborativeAIStudio() {
  const [step, setStep] = useState(0);
  const [wizardId, setWizardId] = useState<string | null>(null);
  const [teamName, setTeamName] = useState("Enterprise Collective Team");
  const [goal, setGoal] = useState("Deliver a unified cross-domain recommendation");
  const [priority, setPriority] = useState("high");
  const [selected, setSelected] = useState<string[]>(["ai_legal", "ai_finance", "ai_ops"]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [team, setTeam] = useState<Dict | null>(null);
  const [roles, setRoles] = useState<Dict | null>(null);
  const [workspace, setWorkspace] = useState<Dict | null>(null);
  const [tasks, setTasks] = useState<Dict | null>(null);
  const [knowledge, setKnowledge] = useState<Dict | null>(null);
  const [decision, setDecision] = useState<Dict | null>(null);
  const [report, setReport] = useState<Dict | null>(null);
  const [performance, setPerformance] = useState<Dict | null>(null);
  const [explain, setExplain] = useState<Dict | null>(null);
  const [ops, setOps] = useState<Dict | null>(null);
  const [created, setCreated] = useState<Dict | null>(null);
  const [collabSessionId, setCollabSessionId] = useState<string | null>(null);

  const panelHelp = useMemo(
    () => ({
      shortDescription: COLLAB_STEPS[step],
      detailedExplanation:
        "Совместная работа AI lets specialists work as one organization. The Concierge orchestrates discussion, delegates work, and delivers a unified answer.",
      example: `Example: complete «${COLLAB_STEPS[step]}».`,
      popup: { title: COLLAB_STEPS[step], body: "Enterprise Collective Intelligence." },
      tooltip: COLLAB_STEPS[step],
      purpose: "Coordinate AI Specialists",
      benefits: "Faster, safer cross-domain decisions",
      typicalUse: "Complex organizational recommendations",
      businessValue: "Foundation for Центр операций AI and AI City",
    }),
    [step],
  );

  async function ensureWizard(): Promise<string> {
    if (wizardId) return wizardId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/collaborative-ai/wizard/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ owner_id: "owner" }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Не удалось начать wizard");
    setWizardId(data.session_id);
    return data.session_id as string;
  }

  async function patchWizard(nextStep: number) {
    const wid = await ensureWizard();
    await fetch(`${PLATFORM_BUILDER_API}/collaborative-ai/wizard/sessions/${wid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        step: nextStep + 1,
        draft: {
          team_name: teamName,
          business_goal: goal,
          priority,
          specialist_ids: selected,
          topic: goal,
          team_id: team?.team_id,
          collab_session_id: collabSessionId,
        },
      }),
    });
  }

  async function go(next: number) {
    setError(null);
    setBusy(true);
    try {
      await patchWizard(next);
      setStep(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка навигации");
    } finally {
      setBusy(false);
    }
  }

  function toggleSpec(id: string) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function createTeam() {
    setBusy(true);
    setError(null);
    try {
      await ensureWizard();
      const res = await fetch(`${PLATFORM_BUILDER_API}/collaborative-ai/teams`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          team_name: teamName,
          business_goal: goal,
          priority,
          specialists: DEFAULT_SPECIALISTS.filter((s) => selected.includes(s.id)),
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Team create failed");
      setTeam(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Team create failed");
    } finally {
      setBusy(false);
    }
  }

  async function assignRoles() {
    if (!team?.team_id) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/teams/${team.team_id}/roles`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
      );
      setRoles(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function openSession() {
    if (!team?.team_id) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/teams/${team.team_id}/sessions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic: goal }),
        },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Session failed");
      setCollabSessionId(body.session_id);
      const ws = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${body.session_id}/workspace`,
      );
      setWorkspace(await ws.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Session failed");
    } finally {
      setBusy(false);
    }
  }

  async function runTasks() {
    if (!collabSessionId) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${collabSessionId}/tasks`,
        { method: "POST", body: "{}" },
      );
      setTasks(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runKnowledge() {
    if (!collabSessionId) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${collabSessionId}/knowledge`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
      );
      setKnowledge(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runDecide() {
    if (!collabSessionId) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${collabSessionId}/decide`,
        { method: "POST", body: "{}" },
      );
      setDecision(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadReport() {
    if (!collabSessionId) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${collabSessionId}/report`,
      );
      setReport(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadPerformance() {
    if (!collabSessionId) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${collabSessionId}/performance`,
      );
      setPerformance(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadExplain() {
    if (!collabSessionId) return;
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/sessions/${collabSessionId}/explain`,
      );
      setExplain(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function loadOps() {
    setBusy(true);
    try {
      const q = new URLSearchParams();
      if (team?.team_id) q.set("team_id", String(team.team_id));
      if (collabSessionId) q.set("session_id", collabSessionId);
      const res = await fetch(`${PLATFORM_BUILDER_API}/collaborative-ai/ops-foundation?${q}`);
      setOps(await res.json());
    } finally {
      setBusy(false);
    }
  }

  async function runCreate() {
    setBusy(true);
    setError(null);
    try {
      const wid = await ensureWizard();
      await patchWizard(10);
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/collaborative-ai/wizard/sessions/${wid}/create`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || "Ошибка создания");
      setCreated(body);
      if (body.ai_team?.team_id) setTeam(body.ai_team);
      if (body.collaborative_session?.session_id) {
        setCollabSessionId(body.collaborative_session.session_id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка создания");
    } finally {
      setBusy(false);
    }
  }

  const consensus = String(workspace?.consensus_status || "forming");

  return (
    <PlatformBuilderLayout
      title="Совместная работа AI"
      subtitle="Enterprise Collective Intelligence — Concierge-orchestrated specialist teams."
    >
      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="success">Collective Intelligence</Badge>
        <Badge>Decision Engine</Badge>
        <Badge>Sprint 28.8</Badge>
        {wizardId ? <Badge>wizard {wizardId}</Badge> : null}
      </div>

      <ProgressIndicator current={step} total={COLLAB_STEPS.length} />
      <BuilderStepNav steps={[...COLLAB_STEPS]} current={step} onChange={(i) => void go(i)} />

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          {error ? (
            <Card title="Error">
              <p className="eds-type-small text-[var(--eds-danger)]">{error}</p>
            </Card>
          ) : null}

          {step === 0 ? (
            <Card title="AI Team Creation">
              <div className="space-y-3">
                <Input value={teamName} onChange={(e) => setTeamName(e.target.value)} placeholder="Team name" />
                <Input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Business goal" />
                <select
                  className="rounded-md border border-[var(--eds-border)] bg-transparent px-2 py-2"
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
                <div className="flex flex-wrap gap-2">
                  {DEFAULT_SPECIALISTS.map((s) => (
                    <Button
                      key={s.id}
                      variant={selected.includes(s.id) ? "primary" : "ghost"}
                      onClick={() => toggleSpec(s.id)}
                    >
                      {s.name}
                    </Button>
                  ))}
                </div>
                <p className="eds-type-small opacity-70">Concierge: Организация Concierge (orchestrator)</p>
                <Button disabled={busy} onClick={() => void createTeam()}>
                  Создать AI Team
                </Button>
                {team ? (
                  <pre className="overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                    {JSON.stringify(
                      { team_id: team.team_id, visual_id: team.visual_id, priority: team.priority },
                      null,
                      2,
                    )}
                  </pre>
                ) : null}
              </div>
            </Card>
          ) : null}

          {step === 1 ? (
            <Card title="Роль Assignment">
              <Button disabled={busy || !team} onClick={() => void assignRoles()}>
                Assign roles
              </Button>
              {roles ? (
                <ul className="mt-3 space-y-2">
                  {((roles.roles as Dict[]) || []).map((r) => (
                    <li
                      key={String(r.specialist_id)}
                      className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small animate-[fadeIn_0.35s_ease]"
                    >
                      <strong>{String(r.specialist_name)}</strong> · {String(r.role)} · priority{" "}
                      {String(r.priority)}
                      <div className="opacity-70">{String(r.expected_output)}</div>
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 2 ? (
            <Card title="Collaborative Session">
              <Button disabled={busy || !team} onClick={() => void openSession()}>
                Open workspace
              </Button>
              {workspace ? (
                <div className="mt-4 space-y-3">
                  <div className="flex flex-wrap gap-2">
                    <Badge tone="success">Speaker: {String(workspace.current_speaker)}</Badge>
                    <Badge>Consensus: {consensus}</Badge>
                    <span
                      className="inline-flex items-center gap-2 rounded-md border border-[var(--eds-border)] px-2 eds-type-caption"
                      style={{ animation: "pulseSoft 2s ease infinite" }}
                    >
                      Progress {Math.round(Number(workspace.discussion_progress || 0) * 100)}%
                    </span>
                  </div>
                  <p className="eds-type-small">Task: {String(workspace.current_task)}</p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {((workspace.participants as Dict[]) || []).map((p) => (
                      <div
                        key={String(p.id)}
                        className="rounded-md border border-[var(--eds-border)] p-2 eds-type-small"
                      >
                        {String(p.name)} · {String(p.role)}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 3 ? (
            <Card title="Task Distribution">
              <Button disabled={busy || !collabSessionId} onClick={() => void runTasks()}>
                Concierge distribute tasks
              </Button>
              {tasks ? (
                <ul className="mt-3 space-y-2 eds-type-small">
                  {((tasks.tasks as Dict[]) || []).map((t) => (
                    <li key={String(t.task_id)} className="rounded-md border border-[var(--eds-border)] p-2">
                      {String(t.assignee_name)} → {String(t.title)} [{String(t.status)}]
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 4 ? (
            <Card title="Shared База знаний">
              <Button disabled={busy || !collabSessionId} onClick={() => void runKnowledge()}>
                Exchange findings
              </Button>
              {knowledge ? (
                <ul className="mt-3 space-y-1 eds-type-small">
                  {((knowledge.entries as Dict[]) || []).map((e) => (
                    <li key={String(e.exchange_id)}>
                      {String(e.from)}: {String(e.finding)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </Card>
          ) : null}

          {step === 5 ? (
            <Card title="Decision Engine">
              <Button disabled={busy || !collabSessionId} onClick={() => void runDecide()}>
                Generate decision
              </Button>
              {decision ? (
                <div className="mt-3 space-y-2 eds-type-small">
                  <p>
                    <strong>Recommended:</strong> {String(decision.recommended_decision)}
                  </p>
                  <p>Impact: {String(decision.business_impact)}</p>
                  <ul className="space-y-2">
                    {((decision.alternatives as Dict[]) || []).map((a) => (
                      <li key={String(a.id)} className="rounded-md border border-[var(--eds-border)] p-2">
                        {String(a.title)}
                        <div className="opacity-70">Pros: {((a.pros as string[]) || []).join(", ")}</div>
                        <div className="opacity-70">Cons: {((a.cons as string[]) || []).join(", ")}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 6 ? (
            <Card title="Executive Итоги">
              <Button disabled={busy || !collabSessionId} onClick={() => void loadReport()}>
                Prepare report
              </Button>
              {report ? (
                <dl className="mt-3 space-y-2 eds-type-small">
                  <div>
                    <dt className="opacity-60">Executive Итоги</dt>
                    <dd>{String(report.executive_summary)}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Decision Explanation</dt>
                    <dd>{String(report.decision_explanation)}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Action Plan</dt>
                    <dd>{((report.action_plan as string[]) || []).join(" · ")}</dd>
                  </div>
                </dl>
              ) : null}
            </Card>
          ) : null}

          {step === 7 ? (
            <Card title="Team Performance">
              <Button disabled={busy || !collabSessionId} onClick={() => void loadPerformance()}>
                Load metrics
              </Button>
              {performance ? (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {Object.entries((performance.metrics as Dict) || {}).map(([k, v]) => (
                    <div key={k} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                      <div className="font-medium">{k}</div>
                      <div className="opacity-80">
                        {typeof v === "object" ? `${(v as unknown[]).length} contributors` : String(v)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 8 ? (
            <Card title="Explain Decision">
              <Button disabled={busy || !collabSessionId} onClick={() => void loadExplain()}>
                Explain recommendation
              </Button>
              {explain ? (
                <dl className="mt-3 space-y-2 eds-type-small">
                  <div>
                    <dt className="opacity-60">Why</dt>
                    <dd>{String(explain.why_this_recommendation)}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Business Benefits</dt>
                    <dd>{((explain.business_benefits as string[]) || []).join(" · ")}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Alternatives</dt>
                    <dd>{((explain.alternative_approaches as string[]) || []).join(" · ")}</dd>
                  </div>
                  <div>
                    <dt className="opacity-60">Expected Result</dt>
                    <dd>{String(explain.expected_result)}</dd>
                  </div>
                </dl>
              ) : null}
            </Card>
          ) : null}

          {step === 9 ? (
            <Card title="Центр операций AI Foundation">
              <Button disabled={busy} onClick={() => void loadOps()}>
                Load visual foundation
              </Button>
              {ops ? (
                <div className="mt-3 space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {((ops.surfaces as string[]) || []).map((s) => (
                      <Badge key={s}>{s}</Badge>
                    ))}
                  </div>
                  <ul className="eds-type-small space-y-1">
                    {((ops.objects as Dict[]) || []).map((o) => (
                      <li key={String(o.internal_id)}>
                        {String(o.object_type)} · {String(o.label)} · {String(o.visual_id)}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Card>
          ) : null}

          {step === 10 ? (
            <Card title="Создать — зарегистрировать Collective Intelligence">
              <p className="eds-type-small mb-3">
                Registers AI Team, Collaborative Session, Decision Engine, and База знаний Exchange.
              </p>
              <Button disabled={busy} onClick={() => void runCreate()}>
                Register
              </Button>
              {created ? (
                <pre className="mt-3 overflow-auto rounded-md border border-[var(--eds-border)] p-3 eds-type-caption">
                  {JSON.stringify(
                    {
                      team_id: (created.ai_team as Dict)?.team_id,
                      session_id: (created.collaborative_session as Dict)?.session_id,
                      decision_id: (created.decision_engine as Dict)?.decision_id,
                      exchange_pack_id: (created.knowledge_exchange as Dict)?.exchange_pack_id,
                    },
                    null,
                    2,
                  )}
                </pre>
              ) : null}
            </Card>
          ) : null}

          <div className="flex justify-between">
            <Button disabled={busy || step === 0} onClick={() => void go(step - 1)}>
              Назад
            </Button>
            <Button
              disabled={busy || step >= COLLAB_STEPS.length - 1}
              onClick={() => void go(step + 1)}
            >
              Далее
            </Button>
          </div>
        </div>
        <HelpPanel help={panelHelp} guided />
      </div>

      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
        @keyframes pulseSoft { 0%,100% { border-color: var(--eds-border); } 50% { border-color: var(--eds-accent, #38bdf8); } }
      `}</style>
    </PlatformBuilderLayout>
  );
}
