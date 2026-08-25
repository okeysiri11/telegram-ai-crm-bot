import { Link, useParams } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { fetchCasinoVenue } from "./casinoApi";
import { CasinoLedgerPanel, CasinoNav, CasinoWalletBar } from "./CasinoPanels";
import { CasinoPresencePanel } from "./CasinoPresencePanel";
import { useCasinoPresence, useCasinoWallet } from "./useCasinoSession";
import type { CasinoVenue } from "./types";
import { useEffect, useState } from "react";
import "./casino.css";

export function CasinoVenuePage() {
  const { venueId = "odessa-prime" } = useParams();
  const [venue, setVenue] = useState<CasinoVenue | null>(null);
  const [error, setError] = useState<string | null>(null);
  const walletState = useCasinoWallet();
  const presence = useCasinoPresence(venueId);

  useEffect(() => {
    fetchCasinoVenue(venueId)
      .then(setVenue)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "venue_failed"));
  }, [venueId]);

  return (
    <WorkspaceLayout>
      <div className="casino-floor">
        <p className="casino-kicker">Зал · DEMO ONLY</p>
        <h1 className="casino-title">{venue?.name ?? "Odessa Prime Casino"}</h1>
        <p className="casino-copy">
          Серверная европейская рулетка. Валюта — PLAY / DEMO CHIPS. Никаких депозитов и вывода.
        </p>
        <div className="casino-banner">
          <Badge>PLAY</Badge>
          <Badge>DEMO CHIPS</Badge>
        </div>
        {error ? (
          <p className="casino-status" role="alert">
            {error}
          </p>
        ) : null}
        <Card title="Кошелек PLAY">
          <CasinoWalletBar
            wallet={walletState.wallet}
            loading={walletState.loading}
            error={walletState.error}
            onRefresh={() => void walletState.refresh()}
            onGranted={(next) => {
              walletState.setWallet(next);
              void walletState.refresh();
            }}
          />
        </Card>
        <Card title="Столы">
          <CasinoPresencePanel
            rooms={presence.rooms}
            active={presence.active}
            reconnecting={presence.reconnecting}
            error={presence.error}
            onJoin={(roomId) => void presence.join(roomId)}
            onLeave={(roomId) => void presence.leave(roomId)}
            onReconnect={() => void presence.reconnect()}
          />
        </Card>
        <div className="casino-actions">
          <Link to={`/casino/venues/${venueId}/roulette`}>
            <Button>Открыть рулетку</Button>
          </Link>
        </div>
        <Card title="История PLAY">
          <CasinoLedgerPanel items={walletState.ledger} loading={walletState.loading} error={walletState.error} />
        </Card>
        <CasinoNav venueId={venueId} />
      </div>
    </WorkspaceLayout>
  );
}
