/**
 * AI Builder Studio — Sprint 32.8.
 * Constructor UX over existing AI Team / Workflow / catalogs.
 * No new Builder / Workflow Engine / AI Core.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";
import { PLATFORM_BUILDER_API } from "../../platform-builder/types";
import { AIBuilderWizard } from "../../platform-builder/ai-builder/AIBuilderWizard";
import { useLiveEnterprise } from "@/live-ops";
import { deriveWorkflowAutomation } from "@/enterprise-workflow";
import { telemetry } from "@/integrations/telemetry";
import {
  STUDIO_HOME_CARDS,
  DOMAIN_SKILL_PACKS,
  PROMPT_LIBRARY,
  ECOSYSTEM_TEMPLATES,
  INTEGRATION_CARDS,
  PROFESSIONS,
  SKILLS,
  PERMISSIONS,
  PRIORITIES,
  BUSINESS_WORKFLOW_TEMPLATES,
  studioCatalogStats,
  type StudioSectionId,
  type PromptKind,
} from "./studioCatalog";

type TeamMember = {
  agent_id: string;
  name: string;
  avatar: string;
  profession: string;
  specialization: string;
  status: string;
  current_task?: string | null;
  capabilities?: string[];
  paused?: boolean;
};

type Dashboard = {
  count: number;
  active: number;
  paused: number;
  members: TeamMember[];
};

const SECTIONS: Array<{ id: StudioSectionId; label: string }> = [
  { id: "home", label: "Home" },
  { id: "team", label: "AI Team" },
  { id: "workflow", label: "Workflow" },
  { id: "skills", label: "Skills" },
  { id: "prompts", label: "Prompts" },
  { id: "templates", label: "Templates" },
  { id: "integrations", label: "Integrations" },
  { id: "knowledge", label: "Knowledge" },
  { id: "wizard", label: "Wizard" },
];

export function AIBuilderStudioPage() {
  const [params, setParams] = useSearchParams();
  const mode = params.get("mode");
  const sectionParam = (params.get("section") || (mode === "wizard" ? "wizard" : "home")) as StudioSectionId;
  const [section, setSection] = useState<StudioSectionId>(
    SECTIONS.some((s) => s.id === sectionParam) ? sectionParam : "home",
  );

  useEffect(() => {
    if (SECTIONS.some((s) => s.id === sectionParam)) setSection(sectionParam);
  }, [sectionParam]);

  function go(id: StudioSectionId) {
    setSection(id);
    const next = new URLSearchParams(params);
    if (id === "home") next.delete("section");
    else next.set("section", id);
    if (id === "wizard") next.set("mode", "wizard");
    else next.delete("mode");
    setParams(next, { replace: true });
    void telemetry.userActivity(`abs_section:${id}`);
  }

  return (
    <PlatformBuilderLayout
      title="AI Builder Studio"
      subtitle="Собирайте платформу как конструктор: AI Team, Workflow, Skills, Prompts и Templates — без нового Builder Engine."
    >
      <div className="abs-studio eds-anim-fade">
        <nav className="abs-tabs" aria-label="Builder Studio sections">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              className={`abs-tab${section === s.id ? " is-active" : ""}`}
              onClick={() => go(s.id)}
            >
              {s.label}
            </button>
          ))}
        </nav>

        {section === "home" ? <BuilderHome onOpen={go} /> : null}
        {section === "team" ? <TeamBuilderPanel /> : null}
        {section === "workflow" ? <WorkflowBuilderPanel /> : null}
        {section === "skills" ? <SkillLibraryPanel /> : null}
        {section === "prompts" ? <PromptLibraryPanel /> : null}
        {section === "templates" ? <TemplateLibraryPanel /> : null}
        {section === "integrations" ? <IntegrationsPanel /> : null}
        {section === "knowledge" ? <KnowledgePanel /> : null}
        {section === "wizard" ? (
          <Card title="Classic AI Builder Wizard" className="abs-card">
            <p className="eds-type-small text-[var(--eds-text-muted)] mb-3">
              Существующий wizard создания агентов — без изменений архитектуры.
            </p>
            <AIBuilderWizard embedded />
          </Card>
        ) : null}
      </div>
    </PlatformBuilderLayout>
  );
}

function BuilderHome({ onOpen }: { onOpen: (id: StudioSectionId) => void }) {
  const { snapshot } = useLiveEnterprise(true);
  const wf = useMemo(() => deriveWorkflowAutomation(snapshot), [snapshot]);
  const [teamCount, setTeamCount] = useState(0);
  const catalog = studioCatalogStats();

  useEffect(() => {
    void fetch(`${PLATFORM_BUILDER_API}/ai-team/organizations/org_demo/dashboard`)
      .then((r) => r.json())
      .then((d) => setTeamCount(Number(d.count) || 0))
      .catch(() => setTeamCount(0));
  }, []);

  return (
    <div className="space-y-4">
      <Card title="Builder Dashboard" className="abs-dash">
        <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5 eds-type-small">
          <li>
            <Badge tone="success">AI {teamCount || catalog.professions}</Badge>
          </li>
          <li>
            <Badge>Workflow {wf.templates.length}</Badge>
          </li>
          <li>
            <Badge>Skills {catalog.skills}</Badge>
          </li>
          <li>
            <Badge>Prompts {catalog.prompts}</Badge>
          </li>
          <li>
            <Badge>Templates {catalog.templates}</Badge>
          </li>
        </ul>
      </Card>

      <div className="abs-home-grid">
        {STUDIO_HOME_CARDS.map((c) => (
          <button
            key={c.id}
            type="button"
            className="abs-home-card"
            onClick={() => {
              if (c.route && c.id === "knowledge") {
                window.location.assign(c.route);
                return;
              }
              onOpen(c.id);
            }}
          >
            <span className="font-semibold">{c.title}</span>
            <span className="block eds-type-small text-[var(--eds-text-muted)]">{c.detail}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function TeamBuilderPanel() {
  const [orgId, setOrgId] = useState("org_demo");
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");
  const [name, setName] = useState("");
  const [profession, setProfession] = useState("sales");
  const [skills, setSkills] = useState<string[]>([]);
  const [priority, setPriority] = useState<string>("medium");
  const [access, setAccess] = useState<string[]>(["read_crm", "read_knowledge"]);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/dashboard`,
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Load failed");
      setDash(data as Dashboard);
      const first = (data as Dashboard).members?.[0];
      if (first) applyMember(first);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }, [orgId]);

  useEffect(() => {
    void load();
  }, [load]);

  function applyMember(m: TeamMember) {
    setSelectedId(m.agent_id);
    setName(m.name);
    const prof =
      PROFESSIONS.find((p) => p.name.toLowerCase() === m.profession.toLowerCase() || p.id === m.profession)?.id ||
      "sales";
    setProfession(prof);
    setSkills(m.capabilities?.length ? m.capabilities : ["answer_questions", "crm_operations"]);
  }

  async function saveEdit() {
    if (!selectedId) return;
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch(
        `${PLATFORM_BUILDER_API}/ai-team/organizations/${encodeURIComponent(orgId)}/actions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            agent_id: selectedId,
            action: "edit_agent",
            payload: {
              name,
              profession: PROFESSIONS.find((p) => p.id === profession)?.name || profession,
              specialization: priority,
              capabilities: skills,
              permissions: access,
            },
          }),
        },
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Edit failed");
      setDash(data.dashboard as Dashboard);
      setMessage("AI обновлён (роль / навыки / приоритет / доступ)");
      void telemetry.userActivity("abs_team_edit");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Edit failed");
    } finally {
      setBusy(false);
    }
  }

  function toggleSkill(id: string) {
    setSkills((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].slice(0, 8)));
  }

  function toggleAccess(id: string) {
    setAccess((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].slice(0, 8)));
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        <Input className="max-w-xs" value={orgId} onChange={(e) => setOrgId(e.target.value)} placeholder="org id" />
        <Button size="sm" disabled={busy} onClick={() => void load()}>
          Refresh
        </Button>
        <Link to="/platform-builder/ai-team">
          <Button size="sm" variant="ghost">
            AI Team Center →
          </Button>
        </Link>
      </div>
      {message ? <p className="eds-type-small text-[var(--eds-text-muted)]">{message}</p> : null}

      <div className="abs-split">
        <Card title="Команда" className="abs-card">
          <ul className="space-y-2 eds-type-small">
            {(dash?.members || []).map((m) => (
              <li key={m.agent_id}>
                <button
                  type="button"
                  className={`abs-member${selectedId === m.agent_id ? " is-active" : ""}`}
                  onClick={() => applyMember(m)}
                >
                  <span className="font-medium">
                    {m.avatar} {m.name}
                  </span>
                  <span className="block text-[var(--eds-text-muted)]">
                    {m.profession} · {m.status}
                  </span>
                </button>
              </li>
            ))}
            {!dash?.members?.length ? <li className="text-[var(--eds-text-muted)]">· Нет агентов — создайте через Wizard</li> : null}
          </ul>
          <div className="mt-3">
            <Link to="/platform-builder/builder-studio?section=wizard&mode=wizard">
              <Button size="sm" variant="secondary">
                Добавить AI
              </Button>
            </Link>
          </div>
        </Card>

        <Card title="Визуальный редактор" className="abs-card">
          <div className="space-y-3 eds-type-small">
            <label className="block">
              Имя
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label className="block">
              Роль / Profession
              <select
                className="mt-1 w-full rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] px-2 py-1.5"
                value={profession}
                onChange={(e) => setProfession(e.target.value)}
              >
                {PROFESSIONS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              Приоритет
              <select
                className="mt-1 w-full rounded-md border border-[var(--eds-border)] bg-[var(--eds-surface)] px-2 py-1.5"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>
            <div>
              <p className="font-medium mb-1">Навыки</p>
              <div className="flex flex-wrap gap-1">
                {SKILLS.slice(0, 10).map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    className={`abs-chip${skills.includes(s.id) ? " is-active" : ""}`}
                    onClick={() => toggleSkill(s.id)}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="font-medium mb-1">Доступ</p>
              <div className="flex flex-wrap gap-1">
                {PERMISSIONS.slice(0, 8).map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`abs-chip${access.includes(p.id) ? " is-active" : ""}`}
                    onClick={() => toggleAccess(p.id)}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>
            <Button disabled={busy || !selectedId} onClick={() => void saveEdit()}>
              Сохранить изменения
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

function WorkflowBuilderPanel() {
  const { snapshot } = useLiveEnterprise(true);
  const bundle = useMemo(() => deriveWorkflowAutomation(snapshot), [snapshot]);
  const [tplId, setTplId] = useState(BUSINESS_WORKFLOW_TEMPLATES[0]?.id || "new_client");
  const tpl = BUSINESS_WORKFLOW_TEMPLATES.find((t) => t.id === tplId) || BUSINESS_WORKFLOW_TEMPLATES[0];

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Link to="/platform-builder/workflow-center">
          <Button size="sm" variant="secondary">
            Workflow Center →
          </Button>
        </Link>
        <Badge>{bundle.metrics.activeCount} active</Badge>
        <Badge tone="success">{bundle.metrics.completedToday} done</Badge>
      </div>
      <div className="abs-split">
        <Card title="Шаблоны Workflow" className="abs-card">
          <ul className="space-y-1">
            {BUSINESS_WORKFLOW_TEMPLATES.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  className={`abs-member${tplId === t.id ? " is-active" : ""}`}
                  onClick={() => setTplId(t.id)}
                >
                  <span className="font-medium">{t.libraryLabel}</span>
                  <span className="block eds-type-small text-[var(--eds-text-muted)]">{t.hubKind}</span>
                </button>
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Визуальный процесс" className="abs-card">
          <p className="eds-type-small text-[var(--eds-text-muted)] mb-2">{tpl?.description}</p>
          <ol className="abs-chain">
            {(tpl?.steps || []).map((s, i) => (
              <li key={s.id}>
                <Badge>{s.label}</Badge>
                {i < (tpl?.steps.length || 0) - 1 ? <span className="abs-arrow">↓</span> : null}
              </li>
            ))}
          </ol>
          <p className="mt-3 eds-type-caption text-[var(--eds-text-muted)]">
            Только визуализация существующих шаблонов — без нового Workflow Engine.
          </p>
          <div className="mt-2">
            <Link to={`/enterprise-city?wf=${tpl?.id}`}>
              <Button size="sm" variant="ghost">
                Показать на City →
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

function SkillLibraryPanel() {
  return (
    <div className="space-y-3">
      <Card title="Skill Library · Domain Packs" className="abs-card">
        <div className="abs-home-grid">
          {DOMAIN_SKILL_PACKS.map((pack) => (
            <div key={pack.id} className="abs-home-card is-static">
              <span className="font-semibold">{pack.title}</span>
              <ul className="mt-2 eds-type-small text-[var(--eds-text-muted)]">
                {pack.skills.map((sid) => {
                  const s = SKILLS.find((x) => x.id === sid);
                  return <li key={sid}>· {s?.name || sid}</li>;
                })}
              </ul>
            </div>
          ))}
        </div>
      </Card>
      <Card title="All Skills" className="abs-card">
        <div className="flex flex-wrap gap-1">
          {SKILLS.map((s) => (
            <Badge key={s.id}>{s.name}</Badge>
          ))}
        </div>
      </Card>
    </div>
  );
}

function PromptLibraryPanel() {
  const [filter, setFilter] = useState<PromptKind | "all">("all");
  const items = PROMPT_LIBRARY.filter((p) => filter === "all" || p.kind === filter);
  return (
    <div className="space-y-3">
      <Card title="Prompt Library" className="abs-card">
        <div className="flex flex-wrap gap-2 mb-3">
        {(["all", "system", "user", "corporate", "favorite"] as const).map((k) => (
          <Button key={k} size="sm" variant={filter === k ? "secondary" : "ghost"} onClick={() => setFilter(k)}>
            {k}
          </Button>
        ))}
        </div>
        <div className="abs-home-grid">
          {items.map((p) => (
            <Card key={p.id} title={p.title} className="abs-card">
              <Badge>{p.kind}</Badge>
              <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">{p.body}</p>
            </Card>
          ))}
        </div>
      </Card>
    </div>
  );
}

function TemplateLibraryPanel() {
  return (
    <Card title="Ecosystem Templates" className="abs-card">
      <p className="eds-type-small text-[var(--eds-text-muted)] mb-3">
        Семь Business Ecosystems — готовые шаблоны запуска.
      </p>
      <div className="abs-home-grid">
        {ECOSYSTEM_TEMPLATES.map((t) => (
          <Link key={t.id} to={t.route} className="abs-home-card">
            <span className="font-semibold">{t.title}</span>
            <span className="block eds-type-small text-[var(--eds-text-muted)]">{t.detail}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function IntegrationsPanel() {
  return (
    <Card title="Integrations" className="abs-card">
      <div className="abs-home-grid">
        {INTEGRATION_CARDS.map((c) => (
          <Link key={c.id} to={c.route} className="abs-home-card">
            <span className="font-semibold">{c.title}</span>
            <span className="block eds-type-small text-[var(--eds-text-muted)]">{c.detail}</span>
          </Link>
        ))}
      </div>
    </Card>
  );
}

function KnowledgePanel() {
  return (
    <Card title="Knowledge" className="abs-card">
      <p className="eds-type-small text-[var(--eds-text-muted)] mb-3">
        Используйте существующую Knowledge Base и источники AI Builder.
      </p>
      <div className="flex flex-wrap gap-2">
        <Link to="/platform-builder/knowledge">
          <Button size="sm">Open Knowledge Base</Button>
        </Link>
        <Link to="/workspace/docs">
          <Button size="sm" variant="secondary">
            Documents
          </Button>
        </Link>
      </div>
    </Card>
  );
}
