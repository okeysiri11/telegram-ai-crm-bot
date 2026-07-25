import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Checkbox, Input, Switch, Tooltip } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { ProgressIndicator } from "../framework/ProgressIndicator";
import { BuilderStepNav } from "../framework/BuilderStepNav";
import { HelpPanel } from "../framework/HelpPanel";
import { useAcademyStore } from "../managers/academyStore";
import { PLATFORM_BUILDER_API } from "../types";
import {
  AVATARS,
  COMMUNICATION_STYLES,
  CONCIERGE_WIZARD_STEPS,
  GROUP_AI_INVITE_ROLES,
  ORCHESTRATION,
  ORG_ACCESS,
  OWNER_RELATIONSHIPS,
  PROACTIVE,
  RECOMMENDATIONS,
  ROLES,
  TEAM_OWNER_ACTIONS,
  VOICE_PROFILES,
  emptyDraft,
  type ConciergeDraft,
  type HelpBits,
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

type TeamMember = {
  agent_id: string;
  name: string;
  avatar: string;
  profession: string;
  specialization: string;
  status: string;
  current_task?: string | null;
  memory_usage?: number;
  last_activity?: string;
  capabilities?: string[];
};

export function ConciergeWizard() {
  const [step, setStep] = useState(0);
  const [orgId, setOrgId] = useState("org_demo");
  const [draft, setDraft] = useState<ConciergeDraft>(emptyDraft());
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [created, setCreated] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [teamPreview, setTeamPreview] = useState<TeamMember[]>([]);

  const mode = useAcademyStore((s) => s.mode);
  const learning = useAcademyStore((s) => s.isLearningEnabled("concierge"));
  const toggleLearning = useAcademyStore((s) => s.toggleLearning);
  const guided = learning && mode === "guided_learning";

  const sample =
    COMMUNICATION_STYLES.find((s) => s.id === draft.communicationStyle)?.sample ||
    COMMUNICATION_STYLES[1].sample;
  const avatar = AVATARS.find((a) => a.id === draft.avatar) || AVATARS[0];

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch(
          `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/dashboard`,
        );
        if (!res.ok) return;
        const data = await res.json();
        setTeamPreview((data.members || []) as TeamMember[]);
      } catch {
        /* preview optional while API boots */
      }
    })();
  }, [orgId]);

  const help = useMemo(() => {
    const title = CONCIERGE_WIZARD_STEPS[step];
    if (step === 1 && draft.role) {
      const role = ROLES.find((r) => r.id === draft.role);
      if (role) return toHelpContent(role.help);
    }
    return toHelpContent(
      makeHelp(
        `This screen helps you set «${title}».`,
        "Clear Concierge choices make organization support easier to understand.",
        `Example: complete «${title}» before moving on.`,
        title,
      ),
    );
  }, [step, draft.role]);

  function patch(p: Partial<ConciergeDraft>) {
    setDraft((d) => ({ ...d, ...p }));
    setCreated(null);
  }

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    const res = await fetch(`${PLATFORM_BUILDER_API}/concierge/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ organization_id: orgId }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Could not start Concierge session");
    setSessionId(data.session_id);
    return data.session_id as string;
  }

  async function syncAndCreate() {
    setBusy(true);
    setError(null);
    try {
      const sid = await ensureSession();
      const payload = {
        step: 11,
        organization_id: orgId,
        draft: {
          name: draft.name,
          avatar: draft.avatar,
          gender: draft.gender,
          voice_profile: draft.voiceProfile,
          communication_style: draft.communicationStyle,
          role: draft.role,
          role_custom: draft.roleCustom,
          organization_access: draft.organizationAccess,
          orchestration: draft.orchestration,
          proactive: draft.proactive,
          owner_relationship: draft.ownerRelationship,
          recommendations: draft.recommendations,
          group_ai_invite_roles: draft.groupAiInviteRoles,
          enable_ai_team_center: draft.enableAiTeamCenter,
        },
      };
      const patchRes = await fetch(`${PLATFORM_BUILDER_API}/concierge/sessions/${sid}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const patchBody = await patchRes.json();
      if (!patchRes.ok) throw new Error(patchBody.error || "Could not save Concierge");

      const create = await fetch(`${PLATFORM_BUILDER_API}/concierge/sessions/${sid}/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const createBody = await create.json();
      if (!create.ok) throw new Error(createBody.error || "Could not create Concierge");
      setCreated(createBody);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="Concierge Builder"
      subtitle="Create the organization’s central AI Concierge — not an AI Agent. Only one per organization."
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge>Operational</Badge>
        <Badge>Not an AI Agent</Badge>
        <Badge>AI Team Center</Badge>
        <Badge>Academy · {mode}</Badge>
        <Switch
          checked={learning}
          onChange={(v) => toggleLearning("concierge", v)}
          label="Learning mode"
        />
        <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/ai-team">
          Open AI Team Center →
        </Link>
      </div>

      <ProgressIndicator current={step} total={CONCIERGE_WIZARD_STEPS.length} />
      <BuilderStepNav steps={[...CONCIERGE_WIZARD_STEPS]} current={step} onChange={setStep} />

      <div className="eds-grid eds-grid--dashboard">
        <Card title={CONCIERGE_WIZARD_STEPS[step]}>
          {step === 0 ? (
            <div className="space-y-3">
              <Input
                placeholder="Concierge name (required)"
                value={draft.name}
                onChange={(e) => patch({ name: e.target.value })}
              />
              <div className="flex flex-wrap gap-2">
                {AVATARS.map((a) => (
                  <Button
                    key={a.id}
                    variant={draft.avatar === a.id ? "primary" : "secondary"}
                    onClick={() => patch({ avatar: a.id })}
                  >
                    {a.emoji} {a.name}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {(["male", "female", "neutral"] as const).map((g) => (
                  <Button
                    key={g}
                    variant={draft.gender === g ? "primary" : "ghost"}
                    onClick={() => patch({ gender: g })}
                  >
                    Gender · {g}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {VOICE_PROFILES.map((v) => (
                  <Button
                    key={v.id}
                    variant={draft.voiceProfile === v.id ? "primary" : "secondary"}
                    onClick={() => patch({ voiceProfile: v.id })}
                  >
                    Voice · {v.name}
                  </Button>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {COMMUNICATION_STYLES.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className={`rounded-md border p-3 text-left eds-type-small ${
                      draft.communicationStyle === s.id
                        ? "border-[var(--eds-primary)]"
                        : "border-[var(--eds-border)]"
                    }`}
                    onClick={() => patch({ communicationStyle: s.id })}
                  >
                    <strong>{s.name}</strong>
                    <p className="eds-type-caption text-[var(--eds-text-muted)]">{s.sample}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {step === 1 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {ROLES.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => patch({ role: r.id })}
                  className={`rounded-md border p-3 text-left ${
                    draft.role === r.id
                      ? "border-[var(--eds-primary)] bg-[var(--eds-primary-soft)]"
                      : "border-[var(--eds-border)]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <strong className="eds-type-small">{r.name}</strong>
                    <Tooltip label={r.help.tooltip}>
                      <span className="eds-type-caption text-[var(--eds-primary)]">Info</span>
                    </Tooltip>
                  </div>
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{r.help.purpose}</p>
                  {guided ? (
                    <p className="mt-1 eds-type-caption">
                      Benefits: {r.help.benefits} · {r.help.example}
                    </p>
                  ) : null}
                </button>
              ))}
              {draft.role === "custom" ? (
                <Input
                  className="sm:col-span-2"
                  placeholder="Describe the custom role"
                  value={draft.roleCustom}
                  onChange={(e) => patch({ roleCustom: e.target.value })}
                />
              ) : null}
            </div>
          ) : null}

          {step === 2 ? (
            <div className="space-y-3">
              <Input
                placeholder="Organization ID"
                value={orgId}
                onChange={(e) => {
                  setOrgId(e.target.value);
                  setSessionId(null);
                }}
              />
              <div className="grid gap-2 sm:grid-cols-2">
                {ORG_ACCESS.map((item) => (
                  <label key={item.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                    <span className="inline-flex items-center gap-2">
                      <Checkbox
                        checked={draft.organizationAccess.includes(item.id)}
                        onChange={() =>
                          patch({ organizationAccess: toggleList(draft.organizationAccess, item.id) })
                        }
                      />
                      {item.name}
                    </span>
                    <p className="mt-1 text-[var(--eds-text-muted)]">{item.help.shortDescription}</p>
                    {guided ? (
                      <p className="mt-1 eds-type-caption">
                        Purpose: {item.help.purpose} · Value: {item.help.benefits} · {item.help.example}
                      </p>
                    ) : null}
                  </label>
                ))}
              </div>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="space-y-3">
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                AI Team Center shows all AI Specialists. Unlimited specialists. Concierge manages; specialists execute.
              </p>
              <label className="flex items-center gap-2 eds-type-small">
                <Checkbox
                  checked={draft.enableAiTeamCenter}
                  onChange={() => patch({ enableAiTeamCenter: !draft.enableAiTeamCenter })}
                />
                Enable AI Team Center on create
              </label>
              <div className="flex flex-wrap gap-2">
                {TEAM_OWNER_ACTIONS.map((a) => (
                  <Badge key={a}>{a}</Badge>
                ))}
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {teamPreview.slice(0, 4).map((m) => (
                  <div key={m.agent_id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                    <strong>
                      {m.avatar} {m.name}
                    </strong>
                    <p className="text-[var(--eds-text-muted)]">
                      {m.profession} · {m.specialization}
                    </p>
                    <p>Status: {m.status}</p>
                    <p>Task: {m.current_task || "—"}</p>
                  </div>
                ))}
              </div>
              <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/ai-team">
                Open full AI Team dashboard →
              </Link>
            </div>
          ) : null}

          {step === 4 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {ORCHESTRATION.map((item) => (
                <label key={item.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={draft.orchestration.includes(item.id)}
                      onChange={() =>
                        patch({ orchestration: toggleList(draft.orchestration, item.id) })
                      }
                    />
                    {item.name}
                  </span>
                  <p className="mt-1 text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                </label>
              ))}
              <p className="sm:col-span-2 eds-type-caption text-[var(--eds-text-muted)]">
                Architecture supports future Collaborative AI — Concierge coordinates, Specialists execute.
              </p>
            </div>
          ) : null}

          {step === 5 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {PROACTIVE.map((item) => (
                <label key={item.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                  <span className="inline-flex items-center gap-2">
                    <Checkbox
                      checked={draft.proactive.includes(item.id)}
                      onChange={() => patch({ proactive: toggleList(draft.proactive, item.id) })}
                    />
                    {item.name}
                  </span>
                  {"help" in item && item.help ? (
                    <p className="mt-1 text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                  ) : null}
                </label>
              ))}
            </div>
          ) : null}

          {step === 6 ? (
            <div className="grid gap-2 sm:grid-cols-2">
              {OWNER_RELATIONSHIPS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => patch({ ownerRelationship: item.id })}
                  className={`rounded-md border p-3 text-left eds-type-small ${
                    draft.ownerRelationship === item.id
                      ? "border-[var(--eds-primary)]"
                      : "border-[var(--eds-border)]"
                  }`}
                >
                  <strong>{item.name}</strong>
                  <p className="eds-type-caption text-[var(--eds-text-muted)]">{item.help.purpose}</p>
                </button>
              ))}
            </div>
          ) : null}

          {step === 7 ? (
            <div className="space-y-3">
              <Badge>Architecture only</Badge>
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Smart Recommendation Engine prepares specialist, workflow, dashboard, knowledge, automation,
                marketplace, and vertical recommendations.
              </p>
              <div className="grid gap-2 sm:grid-cols-2">
                {RECOMMENDATIONS.map((item) => (
                  <label key={item.id} className="rounded-md border border-[var(--eds-border)] p-3 eds-type-small">
                    <span className="inline-flex items-center gap-2">
                      <Checkbox
                        checked={draft.recommendations.includes(item.id)}
                        onChange={() =>
                          patch({ recommendations: toggleList(draft.recommendations, item.id) })
                        }
                      />
                      {item.name}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ) : null}

          {step === 8 ? (
            <div className="space-y-3">
              <Badge>Architecture only</Badge>
              <p className="eds-type-small text-[var(--eds-text-muted)]">
                Owner starts a conversation and invites specialists. All invited AI discuss together.
                Foundation includes conversation history, participant list, speaking order, AI summary, and
                decision summary.
              </p>
              <div className="flex flex-wrap gap-2">
                {GROUP_AI_INVITE_ROLES.map((role) => (
                  <label key={role} className="rounded-md border border-[var(--eds-border)] px-3 py-2 eds-type-small">
                    <span className="inline-flex items-center gap-2">
                      <Checkbox
                        checked={draft.groupAiInviteRoles.includes(role)}
                        onChange={() =>
                          patch({ groupAiInviteRoles: toggleList(draft.groupAiInviteRoles, role) })
                        }
                      />
                      {role}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          ) : null}

          {step === 9 ? (
            <div className="space-y-3">
              <Card title={`Concierge Card · ${draft.name || "Unnamed"}`}>
                <ul className="space-y-1 eds-type-small">
                  <li>
                    Identity: {avatar.emoji} {draft.name || "—"} · {draft.gender} · voice {draft.voiceProfile}
                  </li>
                  <li>
                    Role:{" "}
                    {draft.role === "custom"
                      ? draft.roleCustom || "Custom"
                      : ROLES.find((r) => r.id === draft.role)?.name || "—"}
                  </li>
                  <li>Organization access: {draft.organizationAccess.join(", ") || "—"}</li>
                  <li>Proactive: {draft.proactive.join(", ") || "—"}</li>
                  <li>Orchestration: {draft.orchestration.join(", ") || "—"}</li>
                  <li>Owner relationship: {draft.ownerRelationship}</li>
                  <li>AI Team Center: {draft.enableAiTeamCenter ? "Yes" : "No"}</li>
                </ul>
              </Card>
              <Card title="Organization Overview">
                <p className="eds-type-small">Organization: {orgId}</p>
                <p className="eds-type-small">Access areas: {draft.organizationAccess.length}</p>
              </Card>
              <Card title="AI Team Overview">
                <p className="eds-type-small">Specialists preview: {teamPreview.length}</p>
                <p className="eds-type-caption text-[var(--eds-text-muted)]">
                  Unlimited AI Specialists. Concierge manages; specialists execute.
                </p>
              </Card>
            </div>
          ) : null}

          {step === 10 ? (
            <div className="space-y-3">
              <p className="eds-type-small">
                Create registers the Concierge, AI Team Center, and Organization Connection in the Concierge
                Registry. Exactly one Concierge is allowed per organization.
              </p>
              {error ? <p className="eds-type-small text-[var(--eds-danger)]">{error}</p> : null}
              {created ? (
                <Card title="Created">
                  <p className="eds-type-small">Concierge, AI Team Center, and organization linked.</p>
                  <pre className="mt-2 max-h-48 overflow-auto eds-type-caption">
                    {JSON.stringify(
                      {
                        concierge: created.concierge,
                        ai_team_center: created.ai_team_center,
                      },
                      null,
                      2,
                    )}
                  </pre>
                </Card>
              ) : (
                <Button variant="primary" disabled={busy} onClick={() => void syncAndCreate()}>
                  {busy ? "Creating…" : "Create Concierge"}
                </Button>
              )}
            </div>
          ) : null}

          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))}>
              Back
            </Button>
            <Button
              disabled={step >= CONCIERGE_WIZARD_STEPS.length - 1}
              onClick={() => setStep((s) => Math.min(CONCIERGE_WIZARD_STEPS.length - 1, s + 1))}
            >
              Next
            </Button>
          </div>
        </Card>

        <HelpPanel help={help} guided={guided} />

        <Card title="Live conversation preview">
          <p className="eds-type-small text-[var(--eds-text-muted)]">Owner: What should I focus on today?</p>
          <p className="mt-2 eds-type-small">
            <strong>
              {avatar.emoji} {draft.name || "Concierge"}:
            </strong>{" "}
            {sample}
          </p>
        </Card>

        <Card title="Organization overview">
          <p className="eds-type-small">Organization: {orgId}</p>
          <p className="eds-type-small">Access areas: {draft.organizationAccess.length}</p>
          <p className="eds-type-small">Orchestration: {draft.orchestration.length}</p>
          <p className="eds-type-small">Proactive: {draft.proactive.length}</p>
          <p className="eds-type-small">AI Team specialists: {teamPreview.length}</p>
          <p className="eds-type-caption text-[var(--eds-text-muted)]">
            Concierge coordinates Specialists. Specialists execute work.
          </p>
        </Card>
      </div>
    </PlatformBuilderLayout>
  );
}
