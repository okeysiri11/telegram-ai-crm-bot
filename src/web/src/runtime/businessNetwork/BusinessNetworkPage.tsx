/**
 * Business Network Center — Sprint 29.0 foundation UI.
 */

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { FullLayout } from "@/layouts/FullLayout";
import { Badge, Button, Card } from "@/ui";
import {
  businessNetworkEngine,
  EBN_HOME_PROFILE_ID,
  EBN_PARTNER_PROFILE_ID,
} from "@/runtime/businessNetwork";
import { rememberModuleRoute } from "@/modules/lastModuleStore";

type Tab = "profiles" | "relationships" | "graph" | "comms" | "documents" | "city";

export function BusinessNetworkPage() {
  const [tab, setTab] = useState<Tab>("profiles");
  const [tick, setTick] = useState(0);
  const snap = useMemo(() => {
    void tick;
    return businessNetworkEngine.inspectorSnapshot();
  }, [tick]);

  useEffect(() => {
    document.title = "Business Network · ADOS";
    rememberModuleRoute("/business-network");
    businessNetworkEngine.startup();
    const id = window.setInterval(() => setTick((n) => n + 1), 2500);
    return () => window.clearInterval(id);
  }, []);

  function refresh() {
    setTick((n) => n + 1);
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "profiles", label: "Profiles" },
    { id: "relationships", label: "Relationships" },
    { id: "graph", label: "Graph" },
    { id: "comms", label: "Comms" },
    { id: "documents", label: "Documents" },
    { id: "city", label: "City" },
  ];

  return (
    <FullLayout>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h1 className="text-2xl font-semibold">Enterprise Business Network</h1>
          <p className="eds-type-helper">
            Sprint {snap.version} · {snap.stats.profiles} profiles · {snap.stats.approved} approved
            relationships · foundation (not a social network)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => {
              businessNetworkEngine.createRelationship({
                fromProfileId: EBN_HOME_PROFILE_ID,
                toProfileId: EBN_PARTNER_PROFILE_ID,
                type: "friend",
              });
              refresh();
            }}
          >
            Request friend link
          </Button>
          <Link to="/enterprise-city" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Enterprise City →
          </Link>
          <Link to="/automation" className="eds-type-helper text-[var(--eds-primary)] self-center">
            Automation →
          </Link>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <Button
            key={t.id}
            size="sm"
            variant={tab === t.id ? "primary" : "ghost"}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </Button>
        ))}
      </div>

      {tab === "profiles" ? (
        <div className="grid gap-3 md:grid-cols-2">
          {snap.cards.map((c) => (
            <Card key={c.id} title={c.companyName}>
              <div className="flex flex-wrap gap-2 mb-2">
                <Badge>{c.category}</Badge>
                <Badge>{c.status}</Badge>
                <Badge>{c.verificationStatus}</Badge>
              </div>
              <p className="eds-type-helper">{c.tagline || "—"}</p>
              <p className="eds-type-small mt-2">
                Trust {c.trustLevel} · Relations {c.relationshipCount}
                {c.headquarters ? ` · ${c.headquarters}` : ""}
              </p>
            </Card>
          ))}
        </div>
      ) : null}

      {tab === "relationships" ? (
        <Card title="Relationships">
          <ul className="space-y-2">
            {snap.relationships.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--eds-border)] pb-2">
                <span className="eds-type-small">
                  {r.type} · {r.fromProfileId} → {r.toProfileId} · <Badge>{r.state}</Badge>
                </span>
                <div className="flex gap-1">
                  {r.state === "pending" ? (
                    <>
                      <Button size="sm" variant="secondary" onClick={() => { businessNetworkEngine.approveRelationship(r.id); refresh(); }}>
                        Approve
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { businessNetworkEngine.rejectRelationship(r.id); refresh(); }}>
                        Reject
                      </Button>
                    </>
                  ) : null}
                  <Button size="sm" variant="ghost" onClick={() => { businessNetworkEngine.removeRelationship(r.id); refresh(); }}>
                    Revoke
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "graph" ? (
        <div className="grid gap-3 md:grid-cols-2">
          <Card title="Nodes">
            <ul className="space-y-1 eds-type-small">
              {snap.graph.nodes.map((n) => (
                <li key={n.id}>
                  {n.label} · trust {n.trustLevel} · {n.category}
                </li>
              ))}
            </ul>
          </Card>
          <Card title="Edges">
            <ul className="space-y-1 eds-type-small">
              {snap.graph.edges.map((e) => (
                <li key={e.id}>
                  {e.from} —{e.type}→ {e.to} ({e.state}, w={e.weight})
                </li>
              ))}
            </ul>
          </Card>
        </div>
      ) : null}

      {tab === "comms" ? (
        <Card title="Conversations">
          <ul className="space-y-2">
            {snap.conversations.map((c) => (
              <li key={c.id} className="eds-type-small border-b border-[var(--eds-border)] pb-2">
                <strong>{c.title}</strong> · {c.kind} · members {c.members.length}
                {c.videoRoomCompatible ? " · video-ready" : ""}
                <div className="mt-1 eds-type-helper">
                  {businessNetworkEngine.listMessages(c.id).slice(-3).map((m) => (
                    <div key={m.id}>
                      {m.senderProfileId}: {m.body}
                    </div>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      {tab === "documents" ? (
        <Card title="Verified Document Links">
          <ul className="space-y-2">
            {snap.documents.map((d) => (
              <li key={d.id} className="eds-type-small">
                <Badge>{d.kind}</Badge> {d.title} · {d.documentRef}
                {d.verified ? " · verified" : ""}
              </li>
            ))}
            {!snap.documents.length ? <li className="eds-type-helper">No links</li> : null}
          </ul>
        </Card>
      ) : null}

      {tab === "city" ? (
        <Card title="City Runtime Facade">
          {snap.city.home ? (
            <ul className="eds-type-small space-y-1">
              <li>Profile: {snap.city.home.companyName}</li>
              <li>Status: {snap.city.home.status}</li>
              <li>Trust: {snap.city.home.trustLevel}</li>
              <li>Relationships: {snap.city.home.relationshipCount}</li>
              <li>HQ: {snap.city.home.headquarters || "—"}</li>
              <li>Verification: {snap.city.home.verificationStatus}</li>
              <li>Reputation (future): {snap.city.home.reputationScore}</li>
            </ul>
          ) : (
            <p className="eds-type-helper">No city facade</p>
          )}
        </Card>
      ) : null}
    </FullLayout>
  );
}
