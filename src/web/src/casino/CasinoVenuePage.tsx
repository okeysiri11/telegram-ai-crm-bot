import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { fetchCasinoVenue } from "./casinoApi";
import type { CasinoVenue } from "./types";

type Wallet = { balance_chips: number; currency_code: string; play_money_only: boolean };

export function CasinoVenuePage() {
  const { venueId = "odessa-prime" } = useParams();
  const [venue, setVenue] = useState<CasinoVenue | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastSpin, setLastSpin] = useState<string>("");

  useEffect(() => {
    fetchCasinoVenue(venueId)
      .then(setVenue)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "venue_failed"));
    apiFetch(`${webConfig.casinoPrefix}/wallet`)
      .then(async (res) => {
        if (!res.ok) return;
        setWallet((await res.json()) as Wallet);
      })
      .catch(() => undefined);
  }, [venueId]);

  async function playDemo() {
    setError(null);
    const prefix = webConfig.casinoPrefix;
    const opened = await apiFetch(`${prefix}/venues/${encodeURIComponent(venueId)}/roulette/rounds`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    if (!opened.ok) {
      setError(`round_${opened.status}`);
      return;
    }
    const round = (await opened.json()) as { round_id: string };
    const bet = await apiFetch(`${prefix}/roulette/rounds/${round.round_id}/bets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bet_type: "red", amount_chips: 10, idempotency_key: `ui-${round.round_id}` }),
    });
    if (!bet.ok) {
      setError(`bet_${bet.status}`);
      return;
    }
    const spun = await apiFetch(`${prefix}/roulette/rounds/${round.round_id}/spin`, { method: "POST" });
    if (!spun.ok) {
      setError(`spin_${spun.status}`);
      return;
    }
    const result = (await spun.json()) as { result_number: number; result_color: string };
    setLastSpin(`${result.result_number} ${result.result_color}`);
    const w = await apiFetch(`${prefix}/wallet`);
    if (w.ok) setWallet((await w.json()) as Wallet);
  }

  return (
    <WorkspaceLayout>
      <div className="p-6 space-y-4">
        <div className="flex items-center gap-3 flex-wrap">
          <h1 className="eds-type-h1">{venue?.name ?? "Casino venue"}</h1>
          <Badge>Play chips</Badge>
        </div>
        <p className="eds-type-body">
          Server-authoritative European roulette demo. Results are generated on the API. There is no
          deposit and no payment form.
        </p>
        {error ? <p className="eds-type-status">{error}</p> : null}
        <Card title="Play-money wallet">
          <p className="eds-type-body">
            {wallet
              ? `${wallet.balance_chips} ${wallet.currency_code}`
              : "Sign in to load your chip wallet."}
          </p>
        </Card>
        <Card title="Roulette demo" actions={<Button onClick={() => void playDemo()}>Spin demo (10 chips on red)</Button>}>
          <p className="eds-type-helper">Last server result: {lastSpin || "—"}</p>
        </Card>
        <div className="flex gap-4 flex-wrap">
          <Link to="/casino">Lobby</Link>
          <Link to="/enterprise-city">City</Link>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
