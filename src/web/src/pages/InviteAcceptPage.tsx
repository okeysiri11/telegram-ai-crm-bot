/**
 * Accept invitation — Sprint 32.1.
 * Public entry: register/login to ecosystem session, then accept token.
 */

import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { hubIntegrations } from "@/integrations/hub";
import { telemetry } from "@/integrations/telemetry";

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

export function InviteAcceptPage() {
  const [params] = useSearchParams();
  const tokenFromQuery = useMemo(() => params.get("token") || "", [params]);
  const [token, setToken] = useState(tokenFromQuery);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [membership, setMembership] = useState<Dict | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function authAndAccept(mode: "register" | "login") {
    if (!token.trim()) {
      setError("Invitation token is required");
      return;
    }
    setBusy(true);
    setError(null);
    setStatus(null);
    try {
      const authPath =
        mode === "register"
          ? `${hubIntegrations.ecosystem}/identity/auth/register`
          : `${hubIntegrations.ecosystem}/identity/auth/login`;
      const authRes = await fetch(authPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          display_name: displayName || email.trim(),
          device_name: "invite-accept",
          platform: "web",
        }),
      });
      const authBody = (await authRes.json()) as Dict;
      if (!authRes.ok) throw new Error(String(authBody.error || `Auth HTTP ${authRes.status}`));
      const session = authBody.session as Dict | undefined;
      const sessionToken = String(session?.access_token || session?.token || "");
      if (!sessionToken) throw new Error("No session token");
      saveSession(sessionToken);
      setStatus("Authenticated — accepting invitation…");

      const acceptRes = await fetch(`${hubIntegrations.ecosystem}/organizations/invitations/accept`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${sessionToken}`,
        },
        body: JSON.stringify({ token: token.trim() }),
      });
      const acceptBody = (await acceptRes.json()) as Dict;
      if (!acceptRes.ok) throw new Error(String(acceptBody.error || `Accept HTTP ${acceptRes.status}`));
      setMembership(acceptBody);
      setStatus("Invitation accepted");
      await telemetry.audit("pilot_invite_accepted", String(acceptBody.organization_id || "org"));
      await telemetry.userActivity("invite_accept_success");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Accept failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="success">Accept Invitation</Badge>
        <Badge>Sprint 32.1</Badge>
        {loadSession() ? <Badge>Session present</Badge> : null}
      </div>

      <h1 className="eds-type-title text-[var(--eds-text)]">Join organization</h1>
      <p className="mt-1 max-w-3xl eds-type-body text-[var(--eds-text-muted)]">
        Register or sign in with ecosystem identity, then redeem your invitation token.
      </p>

      {error ? (
        <div className="mt-4">
          <EmptyState title="Accept failed" description={error} actionLabel="Request invite" actionTo="/pilot/invite" />
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <Card title="Invitation">
          <div className="grid gap-2">
            <Input
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Invitation token"
              aria-label="Invitation token"
            />
            <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" aria-label="Email" />
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
              <Button
                size="sm"
                disabled={busy || !token || !email || !password}
                onClick={() => void authAndAccept("register")}
              >
                Register & accept
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={busy || !token || !email || !password}
                onClick={() => void authAndAccept("login")}
              >
                Login & accept
              </Button>
            </div>
            {status ? <p className="eds-type-small text-[var(--eds-text-muted)]">{status}</p> : null}
          </div>
        </Card>

        <Card title="Membership">
          {membership ? (
            <pre className="max-h-64 overflow-auto eds-type-small">{JSON.stringify(membership, null, 2)}</pre>
          ) : (
            <p className="eds-type-small text-[var(--eds-text-muted)]">
              After accept, continue to{" "}
              <Link className="underline" to="/pilot">
                Pilot Dashboard
              </Link>{" "}
              or{" "}
              <Link className="underline" to="/workspace">
                Workspaces
              </Link>
              .
            </p>
          )}
        </Card>
      </div>
    </WorkspaceLayout>
  );
}
