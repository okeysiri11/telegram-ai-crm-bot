import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { fetchCasinoLobby } from "./casinoApi";
import type { CasinoLobby } from "./types";

export function CasinoLobbyPage() {
  const [lobby, setLobby] = useState<CasinoLobby | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCasinoLobby()
      .then(setLobby)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "lobby_failed"));
  }, []);

  return (
    <WorkspaceLayout>
      <div className="p-6 space-y-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="eds-type-h1">Casino</h1>
          <Badge>Play money only</Badge>
        </div>
        <p className="eds-type-body">
          Demo chips only. No deposits, no cards, no real-money wagering.
        </p>
        {error ? <p className="eds-type-status">{error}</p> : null}
        <Card title="Lobby">
          <div className="space-y-3">
            {(lobby?.venues ?? []).map((venue) => (
              <div key={venue.venue_id} className="flex items-center justify-between gap-3 flex-wrap">
                <div>
                  <div className="eds-type-h3">{venue.name}</div>
                  <div className="eds-type-helper">
                    City building: {venue.city_building_id} · {venue.game}
                  </div>
                </div>
                <Link to={`/casino/venues/${venue.slug}`}>
                  <Button>Enter venue</Button>
                </Link>
              </div>
            ))}
            {!lobby && !error ? <p className="eds-type-helper">Loading lobby…</p> : null}
          </div>
        </Card>
        <Link to="/enterprise-city" className="eds-type-helper">
          Back to Enterprise City
        </Link>
      </div>
    </WorkspaceLayout>
  );
}
