import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { openRouletteRound, placeRouletteBet, spinRoulette } from "./casinoApi";
import { CasinoLedgerPanel, CasinoNav, CasinoWalletBar } from "./CasinoPanels";
import { CasinoPresencePanel } from "./CasinoPresencePanel";
import { CasinoRouletteTable, type RouletteSelection } from "./CasinoRouletteTable";
import { useCasinoPresence, useCasinoWallet } from "./useCasinoSession";
import "./casino.css";

export function CasinoRoulettePage() {
  const { venueId = "odessa-prime" } = useParams();
  const walletState = useCasinoWallet();
  const presence = useCasinoPresence(venueId, "roulette-royale");
  const [chip, setChip] = useState(10);
  const [selection, setSelection] = useState<RouletteSelection | null>({ bet_type: "red" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastNumber, setLastNumber] = useState<number | null>(null);
  const [lastColor, setLastColor] = useState<string | null>(null);

  useEffect(() => {
    void presence.join("roulette-royale").catch(() => undefined);
    // Join the live table when the roulette surface mounts; reconnect is handled by presence.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [venueId]);

  async function play() {
    if (!selection) return;
    setBusy(true);
    setError(null);
    try {
      const opened = await openRouletteRound(venueId);
      await placeRouletteBet(opened.round_id, {
        bet_type: selection.bet_type,
        amount_chips: chip,
        numbers: selection.bet_type === "straight" ? selection.numbers : undefined,
        idempotency_key: `ui-${opened.round_id}-${selection.bet_type}-${chip}`,
      });
      const result = await spinRoulette(opened.round_id);
      setLastNumber(result.result_number);
      setLastColor(result.result_color);
      await walletState.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "spin_failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspaceLayout>
      <div className="casino-floor">
        <p className="casino-kicker">Roulette Royale · DEMO ONLY</p>
        <h1 className="casino-title">Европейская рулетка</h1>
        <p className="casino-copy">
          Результат считает сервер. Клиент не передаёт выигрышное число. Ставки только в PLAY / DEMO CHIPS.
        </p>
        <div className="casino-banner">
          <Badge>PLAY</Badge>
          <Badge>DEMO CHIPS</Badge>
          <Badge>Server RNG</Badge>
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
        <Card title="Стол">
          <CasinoRouletteTable
            chip={chip}
            selection={selection}
            busy={busy}
            lastNumber={lastNumber}
            lastColor={lastColor}
            onChip={setChip}
            onSelect={setSelection}
            onPlay={() => void play()}
          />
        </Card>
        <Card title="Игроки за столом">
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
        <Card title="История PLAY">
          <CasinoLedgerPanel items={walletState.ledger} loading={walletState.loading} error={walletState.error} />
        </Card>
        <CasinoNav venueId={venueId} />
      </div>
    </WorkspaceLayout>
  );
}
