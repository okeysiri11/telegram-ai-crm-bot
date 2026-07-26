import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { PLATFORM_BUILDER_API } from "../types";
import { AITeamCollaborationWorkspace } from "@/ai-team-collaboration";

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
  paused?: boolean;
};

type Dashboard = {
  title: string;
  organization_id: string;
  count: number;
  active: number;
  paused: number;
  members: TeamMember[];
  owner_actions: string[];
  group_ai_chat: Record<string, unknown>;
  ready: boolean;
};

const ACTION_LABELS: Record<string, string> = {
  open_chat: "Open Chat",
  assign_task: "Assign Task",
  view_knowledge: "View Knowledge",
  view_memory: "View Memory",
  pause_agent: "Pause Agent",
  resume_agent: "Resume Agent",
  edit_agent: "Edit Agent",
  replace_agent: "Replace Agent",
  remove_agent: "Remove Agent",
};

export function AITeamCenterPage() {
  const [orgId, setOrgId] = useState("org_demo");
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/dashboard`,
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Could not load AI Team");
      setDash(data as Dashboard);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }, [orgId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(agentId: string, action: string) {
    setBusy(true);
    setMessage(null);
    try {
      const payload: Record<string, unknown> = {};
      if (action === "assign_task") payload.task = "Owner-assigned follow-up";
      if (action === "edit_agent") payload.name = undefined;
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agent_id: agentId, action, payload }),
        },
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Action failed");
      setDash(data.dashboard as Dashboard);
      setMessage(`${ACTION_LABELS[action] || action} completed`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PlatformBuilderLayout
      title="AI Team Center"
      subtitle="All AI Specialists for the organization. Concierge manages. Specialists execute."
    >
      <div className="flex flex-wrap items-center gap-3">
        <Badge>Operational</Badge>
        <Badge>Unlimited Specialists</Badge>
        <Badge>Group AI Foundation</Badge>
        <Badge tone="success">Multi-Agent Workspace</Badge>
        <Input
          className="max-w-xs"
          value={orgId}
          onChange={(e) => setOrgId(e.target.value)}
          placeholder="Organization ID"
        />
        <Button disabled={busy} onClick={() => void load()}>
          Refresh
        </Button>
      </div>

      <AITeamCollaborationWorkspace apiMembers={dash?.members} />

      {message ? <p className="eds-type-small text-[var(--eds-text-muted)]">{message}</p> : null}

      {dash ? (
        <>
          <div className="flex flex-wrap gap-4 eds-type-small">
            <span>Specialists: {dash.count}</span>
            <span>Active: {dash.active}</span>
            <span>Paused: {dash.paused}</span>
          </div>

          <div className="eds-grid eds-grid--dashboard">
            {dash.members.map((m) => (
              <Card key={m.agent_id} title={`${m.avatar} ${m.name}`}>
                <ul className="space-y-1 eds-type-small">
                  <li>Profession: {m.profession}</li>
                  <li>Specialization: {m.specialization}</li>
                  <li>Status: {m.status}</li>
                  <li>Current task: {m.current_task || "—"}</li>
                  <li>Memory: {Math.round((m.memory_usage || 0) * 100)}%</li>
                  <li>Last activity: {m.last_activity || "—"}</li>
                  <li>Capabilities: {(m.capabilities || []).join(", ") || "—"}</li>
                </ul>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(dash.owner_actions || []).map((action) => (
                    <Button
                      key={action}
                      variant="ghost"
                      disabled={busy}
                      onClick={() => void runAction(m.agent_id, action)}
                    >
                      {ACTION_LABELS[action] || action}
                    </Button>
                  ))}
                </div>
              </Card>
            ))}
          </div>

          <Card title="Group AI Chat Foundation">
            <Badge>Architecture only</Badge>
            <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
              {(dash.group_ai_chat as { description?: string })?.description ||
                "Owner invites specialists to discuss together."}
            </p>
            <p className="mt-1 eds-type-caption">
              Invite roles:{" "}
              {((dash.group_ai_chat as { invite_roles?: string[] })?.invite_roles || []).join(", ")}
            </p>
          </Card>
        </>
      ) : (
        <p className="eds-type-small">{busy ? "Loading…" : "No dashboard yet"}</p>
      )}
    </PlatformBuilderLayout>
  );
}
