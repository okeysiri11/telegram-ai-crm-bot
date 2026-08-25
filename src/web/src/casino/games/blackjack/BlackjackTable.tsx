import { useOutletContext } from "react-router-dom";
import { useState } from "react";
import { dealBlackjack, hitBlackjack, standBlackjack, type BlackjackHand } from "../../casinoApi";
import { formatPlayBalance } from "../../currency";
import { loginRedirect } from "@/navigation/safeReturnTo";
import { useCasinoWallet } from "../../useCasinoSession";
import { casinoSound } from "../../casinoSound";
import { DealerPortrait } from "../../components/DealerPortrait";

function Card({ card, deal }: { card: { rank: string; suit: string; hidden?: boolean }; deal: number }) {
  const hidden = Boolean(card.hidden) || card.rank === "?";
  return (
    <span className={`op-card${hidden ? " is-back" : ""}`} style={{ animationDelay: `${deal * 120}ms` }} data-testid="bj-card">
      {hidden ? "♦" : `${card.rank}${card.suit}`}
    </span>
  );
}

export function BlackjackTable() {
  const outlet = useOutletContext<{ wallet?: ReturnType<typeof useCasinoWallet> }>();
  const wallet = outlet?.wallet ?? {
    wallet: null,
    refresh: async () => undefined,
  };
  const [wager, setWager] = useState(50);
  const [hand, setHand] = useState<BlackjackHand | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dealing = Boolean(hand);

  async function run(fn: () => Promise<BlackjackHand>) {
    setBusy(true);
    setError(null);
    try {
      const next = await fn();
      setHand(next);
      casinoSound.chip();
      if (next.settled) {
        casinoSound.win();
        await wallet.refresh();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "bj_failed";
      if (message === "auth_required") {
        window.location.assign(loginRedirect("/casino/rooms/blackjack"));
        return;
      }
      setError(message.includes("Authentication") ? "Войдите, чтобы играть." : "Недостаточно PLAY или ошибка стола.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="op-bj-table" data-testid="blackjack-table">
      <DealerPortrait name="MARINA" />
      <p className="op-kicker">BLACKJACK SALON · PLAY</p>
      <div className="op-card-row" data-testid="dealer-cards">
        {(hand?.dealer_cards || [{ rank: "?", suit: "?", hidden: true }, { rank: "?", suit: "?", hidden: true }]).map((card, i) => (
          <Card key={`d${i}`} card={card} deal={i} />
        ))}
      </div>
      <div className="op-bj-felt">21</div>
      <div className="op-card-row" data-testid="player-cards">
        {(hand?.player_cards || []).map((card, i) => (
          <Card key={`p${i}`} card={card} deal={i + 2} />
        ))}
      </div>
      <p>{hand ? `Игрок ${hand.player_total}${hand.dealer_total != null ? ` · дилер ${hand.dealer_total}` : ""}` : "Сделайте ставку PLAY"}</p>
      {hand?.settlement ? <p data-testid="bj-result">{hand.settlement.outcome.toUpperCase()} · {formatPlayBalance(hand.settlement.payout_chips)}</p> : null}
      {error ? <p className="op-status" role="alert">{error}</p> : null}
      <div className="op-actions">
        <button className="op-ghost" type="button" disabled={dealing && !hand?.settled} onClick={() => setWager(25)}>25</button>
        <button className="op-ghost" type="button" disabled={dealing && !hand?.settled} onClick={() => setWager(50)}>50</button>
        <button className="op-ghost" type="button" disabled={dealing && !hand?.settled} onClick={() => setWager(100)}>100</button>
        <button className="op-cta" type="button" disabled={busy} onClick={() => void run(() => dealBlackjack(wager))}>
          РАЗДАТЬ {formatPlayBalance(wager)}
        </button>
        <button className="op-cta secondary" type="button" disabled={busy || !hand || hand.settled} data-testid="bj-hit" onClick={() => hand && void run(() => hitBlackjack(hand.hand_id))}>
          HIT
        </button>
        <button className="op-cta secondary" type="button" disabled={busy || !hand || hand.settled} data-testid="bj-stand" onClick={() => hand && void run(() => standBlackjack(hand.hand_id))}>
          STAND
        </button>
      </div>
    </div>
  );
}
