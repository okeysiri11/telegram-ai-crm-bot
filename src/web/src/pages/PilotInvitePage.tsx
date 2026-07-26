/**
 * Pilot invitation flow — Sprint 32.1.
 * Reuses ecosystem organizations invitations API — no parallel invite service.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card, Input, Select, Table } from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { hubIntegrations } from "@/integrations/hub";
import { telemetry } from "@/integrations/telemetry";
import { PLATFORM_BUILDER_VERSION } from "../../platform-builder/types";
import { pilotMetrics } from "@/integrations/pilotMetrics";

type Dict = Record<string, unknown>;

const ECO_SESSION_KEY = "ecosystem_pilot_session";

function loadSession(): string {
  try {
    return localStorage.getItem(ECO_SESSION_KEY) || "";
  } catch {
    return "";
  }
}

function saveSession(token: string) {
  try {
    localStorage.setItem(ECO_SESSION_KEY, token);
  } catch {
    /* ignore */
  }
}

async function ecoFetch(path: string, init: RequestInit = {}, token?: string) {
  const headers = new Headers(init.headers || {});
  if (!headers.has("Content-Type") && init.body) headers.set("Content-Type", "application/json");
  const t = token ?? loadSession();
  if (t) headers.set("Authorization", `Bearer ${t}`);
  return fetch(`${hubIntegrations.ecosystem}${path}`, { ...init, headers });
}

export function PilotInvitePage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [roleId, setRoleId] = useState("member");
  const [roles, setRoles] = useState<Dict[]>([]);
  const [orgs, setOrgs] = useState<Dict[]>([]);
  const [orgId, setOrgId] = useState("");
  const [invitation, setInvitation] = useState<Dict | null>(null);
  const [sessionToken, setSessionToken] = useState(loadSession);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);

  function push(msg: string) {
    setLog((prev) => [...prev, msg]);
  }

  useEffect(() => {
    if (!sessionToken) return;
    void (async () => {
      const [rolesRes, orgsRes] = await Promise.all([
        ecoFetch("/roles", {}, sessionToken),
        ecoFetch("/organizations", {}, sessionToken),
      ]);
      if (rolesRes.ok) {
        const body = (await rolesRes.json()) as { roles?: Dict[] };
        setRoles(body.roles || []);
        if (body.roles?.[0]?.role_id) setRoleId(String(body.roles[0].role_id));
      }
      if (orgsRes.ok) {
        const body = (await orgsRes.json()) as { organizations?: Dict[] };
        setOrgs(body.organizations || []);
        if (body.organizations?.[0]) {
          const id = String(body.organizations[0].organization_id || "");
          setOrgId(id);
        }
      }
    })();
  }, [sessionToken]);

  async function ensureSession(mode: "register" | "login") {
    setBusy(true);
    setError(null);
    try {
      const path = mode === "register" ? "/identity/auth/register" : "/identity/auth/login";
      const res = await ecoFetch(path, {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password,
          display_name: displayName || email.trim(),
          device_name: "pilot-web",
          platform: "web",
        }),
      });
      const body = (await res.json()) as Dict;
      if (!res.ok) throw new Error(String(body.error || `Auth HTTP ${res.status}`));
      const session = body.session as Dict | undefined;
      const token = String(session?.access_token || session?.token || "");
      if (!token) throw new Error("No ecosystem session token returned");
      saveSession(token);
      setSessionToken(token);
      push(`${mode} ok — ecosystem session ready`);
      if (mode === "register") pilotMetrics.recordRegistration();
      await telemetry.userActivity(`pilot_invite_${mode}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Auth failed");
    } finally {
      setBusy(false);
    }
  }

  async function createOrg() {
    if (!orgName.trim()) {
      setError("Organization name required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await ecoFetch("/organizations", {
        method: "POST",
        body: JSON.stringify({ name: orgName.trim() }),
      });
      const body = (await res.json()) as Dict;
      if (!res.ok) throw new Error(String(body.error || `Org HTTP ${res.status}`));
      setOrgs((prev) => [...prev, body]);
      setOrgId(String(body.organization_id || ""));
      push(`Organization created: ${String(body.organization_id)}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Create org failed");
    } finally {
      setBusy(false);
    }
  }

  async function sendInvite() {
    if (!orgId || !inviteEmail.trim()) {
      setError("Organization and invitee email are required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await ecoFetch("/organizations/invitations", {
        method: "POST",
        body: JSON.stringify({
          organization_id: orgId,
          email: inviteEmail.trim(),
          role_id: roleId,
        }),
      });
      const body = (await res.json()) as Dict;
      if (!res.ok) throw new Error(String(body.error || `Invite HTTP ${res.status}`));
      setInvitation(body);
      push(`Invitation created for ${inviteEmail.trim()}`);
      pilotMetrics.recordInvitation("sent");
      await telemetry.audit("pilot_invite_sent", orgId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Invite failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Pilot Invitations</Badge>
        <Badge>Sprint 32.1</Badge>
        <Badge>PB {PLATFORM_BUILDER_VERSION}</Badge>
        {sessionToken ? <Badge tone="success">Ecosystem session</Badge> : <Badge tone="warning">Auth needed</Badge>}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">Owner & User Invitations</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Creates invitation tokens via existing ecosystem organization APIs. Share the invite URL with external
        pilot users.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link to="/pilot/onboard">
          <Button size="sm" variant="secondary">
            Onboarding
          </Button>
        </Link>
        <Link to="/invite/accept">
          <Button size="sm" variant="secondary">
            Accept invite
          </Button>
        </Link>
        <Link to="/pilot">
          <Button size="sm" variant="secondary">
            Pilot Dashboard
          </Button>
        </Link>
      </div>

      {error ? (
        <div className="mt-4">
          <EmptyState title="Invitation warning" description={error} actionLabel="Onboard" actionTo="/pilot/onboard" />
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="1. Ecosystem session (owner)">
          <div className="grid gap-2">
            <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Owner email" aria-label="Owner email" />
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              aria-label="Password"
            />
            <Input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Display name"
              aria-label="Display name"
            />
            <div className="flex flex-wrap gap-2">
              <Button size="sm" disabled={busy || !email || !password} onClick={() => void ensureSession("register")}>
                Register
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={busy || !email || !password}
                onClick={() => void ensureSession("login")}
              >
                Login
              </Button>
            </div>
          </div>
        </Card>

        <Card title="2. Organization">
          <div className="grid gap-2">
            <Input
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="New organization name"
              aria-label="Organization name"
            />
            <Button size="sm" disabled={busy || !sessionToken} onClick={() => void createOrg()}>
              Create organization
            </Button>
            {orgs.length ? (
              <Select value={orgId} onChange={(e) => setOrgId(e.target.value)} aria-label="Select organization">
                {orgs.map((o) => (
                  <option key={String(o.organization_id)} value={String(o.organization_id)}>
                    {String(o.name)} ({String(o.organization_id)})
                  </option>
                ))}
              </Select>
            ) : (
              <p className="eds-type-small text-[var(--eds-text-muted)]">No organizations yet.</p>
            )}
          </div>
        </Card>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="3. Send invitation">
          <div className="grid gap-2">
            <Input
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="Invitee email"
              aria-label="Invitee email"
            />
            <Select value={roleId} onChange={(e) => setRoleId(e.target.value)} aria-label="Role">
              {roles.length ? (
                roles.map((r) => (
                  <option key={String(r.role_id)} value={String(r.role_id)}>
                    {String(r.name || r.role_id)}
                  </option>
                ))
              ) : (
                <>
                  <option value="owner">owner</option>
                  <option value="admin">admin</option>
                  <option value="member">member</option>
                </>
              )}
            </Select>
            <Button size="sm" disabled={busy || !sessionToken || !orgId} onClick={() => void sendInvite()}>
              Create invitation token
            </Button>
          </div>
        </Card>

        <Card title="Invitation result">
          {invitation ? (
            <>
              <p className="eds-type-small">
                Token: <code>{String(invitation.token)}</code>
              </p>
              <p className="mt-2 eds-type-small">
                URL:{" "}
                <Link className="underline" to={String(invitation.invite_url || "/invite/accept")}>
                  {String(invitation.invite_url)}
                </Link>
              </p>
              <pre className="mt-2 max-h-40 overflow-auto eds-type-small">
                {JSON.stringify(invitation, null, 2)}
              </pre>
            </>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">No invitation created yet.</p>
          )}
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Activity">
          {log.length ? (
            <Table headers={["#", "Event"]}>
              {log.map((line, i) => (
                <tr key={`${i}-${line}`} className="border-t border-[var(--ew-border)]">
                  <td className="px-3 py-2">{i + 1}</td>
                  <td className="px-3 py-2">{line}</td>
                </tr>
              ))}
            </Table>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">Awaiting actions.</p>
          )}
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
