/**
 * AI Skills & SDK — Sprint 36.8.
 * Skills Dashboard · Marketplace · Installed Skills · SDK Explorer · Templates · Version Manager
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const SKILLS_API = "/api/skills";
export const SDK_API = "/api/sdk";

type SectionId =
  | "skills-dashboard"
  | "marketplace"
  | "installed-skills"
  | "sdk-explorer"
  | "templates"
  | "version-manager";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "skills-dashboard", label: "Skills Dashboard" },
  { id: "marketplace", label: "Marketplace" },
  { id: "installed-skills", label: "Installed Skills" },
  { id: "sdk-explorer", label: "SDK Explorer" },
  { id: "templates", label: "Templates" },
  { id: "version-manager", label: "Version Manager" },
];

async function api<T>(base: string, path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function SkillsSdkPage() {
  const [section, setSection] = useState<SectionId>("skills-dashboard");
  const [skills, setSkills] = useState<Array<Record<string, unknown>>>([]);
  const [listings, setListings] = useState<Array<Record<string, unknown>>>([]);
  const [installed, setInstalled] = useState<Array<Record<string, unknown>>>([]);
  const [templates, setTemplates] = useState<Array<Record<string, unknown>>>([]);
  const [sdk, setSdk] = useState<Record<string, unknown> | null>(null);
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [versions, setVersions] = useState<Array<Record<string, unknown>>>([]);
  const [selectedSkill, setSelectedSkill] = useState("skill.summarize_report");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lastExec, setLastExec] = useState<Record<string, unknown> | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    const [sk, mk, inst, tpl, manifest, st] = await Promise.all([
      api<{ skills: Array<Record<string, unknown>> }>(SKILLS_API, "/skills"),
      api<{ listings: Array<Record<string, unknown>> }>(SKILLS_API, "/marketplace"),
      api<{ installed: Array<Record<string, unknown>> }>(SKILLS_API, "/installed"),
      api<{ templates: Array<Record<string, unknown>> }>(SDK_API, "/templates"),
      api<Record<string, unknown>>(SDK_API, "/manifest"),
      api<Record<string, unknown>>(SKILLS_API, "/statistics"),
    ]);
    setSkills(sk.skills || []);
    setListings(mk.listings || []);
    setInstalled(inst.installed || []);
    setTemplates(tpl.templates || []);
    setSdk(manifest);
    setStats(st);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const installSelected = async () => {
    setBusy(true);
    try {
      await api(SKILLS_API, `/skills/${encodeURIComponent(selectedSkill)}/install`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      await refresh();
      setSection("installed-skills");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const executeSelected = async () => {
    setBusy(true);
    try {
      const data = await api<Record<string, unknown>>(SKILLS_API, "/execute", {
        method: "POST",
        body: JSON.stringify({ skill_id: selectedSkill, input: { text: "demo" }, auto_install: true }),
      });
      setLastExec(data);
      await refresh();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const loadVersions = async () => {
    setBusy(true);
    try {
      const data = await api<{ versions: Array<Record<string, unknown>> }>(
        SKILLS_API,
        `/skills/${encodeURIComponent(selectedSkill)}/versions`,
      );
      setVersions(data.versions || []);
      setSection("version-manager");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="AI Skills & SDK" subtitle="Sprint 36.8 · register · install · execute">
      <div className="space-y-4" data-testid="skills-sdk-console">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <p className="eds-type-small text-[var(--eds-muted)]">
            Create, publish, install and execute reusable enterprise AI skills.
          </p>
          <div className="flex gap-2 items-center">
            {busy ? <Badge>busy…</Badge> : <Badge tone="success">ready</Badge>}
            <Button type="button" onClick={() => refresh().catch((e) => setError(String(e.message || e)))}>
              Refresh
            </Button>
          </div>
        </header>

        {error ? (
          <Card className="p-3 text-[var(--eds-danger)]" role="alert">
            {error}
          </Card>
        ) : null}

        <nav className="flex flex-wrap gap-2" aria-label="Skills SDK sections">
          {SECTIONS.map((s) => (
            <Button
              key={s.id}
              type="button"
              variant={section === s.id ? "primary" : "ghost"}
              onClick={() => setSection(s.id)}
            >
              {s.label}
            </Button>
          ))}
        </nav>

        {section === "skills-dashboard" && (
          <Card className="p-4 space-y-3" aria-label="Skills Dashboard">
            <h2 className="text-lg font-medium">Skills Dashboard</h2>
            <div className="flex gap-2 flex-wrap">
              <Input
                value={selectedSkill}
                onChange={(e) => setSelectedSkill(e.target.value)}
                aria-label="Skill ID"
              />
              <Button type="button" onClick={installSelected} disabled={busy}>
                Install
              </Button>
              <Button type="button" onClick={executeSelected} disabled={busy}>
                Execute
              </Button>
            </div>
            <pre className="text-xs overflow-auto max-h-48 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(stats || {}, null, 2)}
            </pre>
            <ul className="space-y-1 text-sm">
              {skills.map((s) => (
                <li key={String(s.skill_id)} className="flex justify-between gap-2">
                  <span>
                    {String(s.name)} · {String(s.category)} · {String(s.visibility)}
                  </span>
                  <Badge>{String(s.latest_version)}</Badge>
                </li>
              ))}
            </ul>
            {lastExec ? (
              <pre className="text-xs overflow-auto max-h-40 bg-[var(--eds-surface)] p-2 rounded">
                {JSON.stringify(lastExec, null, 2)}
              </pre>
            ) : null}
          </Card>
        )}

        {section === "marketplace" && (
          <Card className="p-4 space-y-2" aria-label="Marketplace">
            <h2 className="text-lg font-medium">Marketplace</h2>
            <ul className="space-y-1 text-sm">
              {listings.map((l) => (
                <li key={String(l.listing_id)} className="flex justify-between gap-2">
                  <span>
                    {String(l.skill_id)} · {String(l.repository)}
                  </span>
                  <Badge>
                    ★{String(l.rating)} · {String(l.downloads)} dl
                  </Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "installed-skills" && (
          <Card className="p-4 space-y-2" aria-label="Installed Skills">
            <h2 className="text-lg font-medium">Installed Skills</h2>
            <ul className="space-y-1 text-sm">
              {installed.map((i) => (
                <li key={String(i.install_id)} className="flex justify-between gap-2">
                  <span>
                    {String(i.skill_id)}@{String(i.version)}
                  </span>
                  <Badge>{String(i.state)}</Badge>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "sdk-explorer" && (
          <Card className="p-4 space-y-2" aria-label="SDK Explorer">
            <h2 className="text-lg font-medium">SDK Explorer</h2>
            <pre className="text-xs overflow-auto max-h-96 bg-[var(--eds-surface)] p-2 rounded">
              {JSON.stringify(sdk || {}, null, 2)}
            </pre>
          </Card>
        )}

        {section === "templates" && (
          <Card className="p-4 space-y-2" aria-label="Templates">
            <h2 className="text-lg font-medium">Templates</h2>
            <ul className="space-y-2 text-sm">
              {templates.map((t) => (
                <li key={String(t.template_id)}>
                  <strong>{String(t.name)}</strong> · {String(t.kind)}
                  <p className="text-[var(--eds-muted)]">{String(t.description)}</p>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {section === "version-manager" && (
          <Card className="p-4 space-y-3" aria-label="Version Manager">
            <h2 className="text-lg font-medium">Version Manager</h2>
            <Button type="button" onClick={loadVersions} disabled={busy}>
              Load Versions
            </Button>
            <ul className="space-y-1 text-sm font-mono">
              {versions.map((v) => (
                <li key={String(v.version_id)}>
                  {String(v.version)} · {String(v.signature).slice(0, 12)}…
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
