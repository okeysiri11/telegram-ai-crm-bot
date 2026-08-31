import { useOutletContext } from "react-router-dom";
import { useState } from "react";
import { dealBlackjack, doubleBlackjack, hitBlackjack, standBlackjack, type BlackjackHand } from "../../casinoApi";
import { formatPlayBalance } from "../../currency";
import { useCasinoWallet } from "../../useCasinoSession";
import { casinoSound } from "../../casinoSound";
import { DealerPortrait } from "../../components/DealerPortrait";
import { ChipSelector } from "../../components/ChipSelector";
import { useCasinoGuest } from "../../components/CasinoGuestModal";
import { RoomNavigation } from "../../components/RoomNavigation";

const SUIT: Record<string, string> = { s: "♠", h: "♥", d: "♦", c: "♣" };

function Card({ card, deal }: { card: { rank: string; suit: string; hidden?: boolean }; deal: number }) {
  const hidden = Boolean(card.hidden) || card.rank === "?";
  const red = card.suit === "h" || card.suit === "d";
  return (
    <span
      className={`op-card${hidden ? " is-back" : ""}${red ? " is-red-suit" : ""}`}
      style={{ animationDelay: `${deal * 140}ms` }}
      data-testid="bj-card"
    >
      {hidden ? "◆" : `${card.rank}${SUIT[card.suit] || card.suit}`}
    </span>
  );
}

export function BlackjackTable() {
  const outlet = useOutletContext<{ wallet?: ReturnType<typeof useCasinoWallet> }>();
  const wallet = outlet?.wallet ?? { wallet: null, refresh: async () => undefined };
  const guest = useCasinoGuest();
  const [wager, setWager] = useState(50);
  const [hand, setHand] = useState<BlackjackHand | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const playing = Boolean(hand) && !hand?.settled;
  const canDouble = Boolean(hand && !hand.settled && (hand.available_actions || []).includes("double"));

  async function run(fn: () => Promise<BlackjackHand>) {
    setBusy(true);
    setError(null);
    casinoSound.tick();
    try {
      const next = await fn();
      setHand(next);
      casinoSound.card();
      if (next.settled) {
        casinoSound.win();
        await wallet.refresh();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "bj_failed";
      if (message === "auth_required") {
        guest.openGuest("/casino/blackjack");
        return;
      }
      setError(message.includes("Authentication") ? "Войдите, чтобы играть." : "Недостаточно PLAY или ошибка стола.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="op-bj-salon"
      data-testid="blackjack-table"
      data-phase={hand?.settled ? "result" : hand ? "dealing" : "initial"}
    >
      <div className="op-bj-stage">
        <span className="op-bj-lamp" aria-hidden />
        <span className="op-felt-bloom" aria-hidden />
        <span className="op-bj-rail" aria-hidden />
        <div className="op-shoe" aria-hidden>
          <span />
          <span />
        </div>
        <DealerPortrait name="MARINA" />
        <div className="op-bj-felt-table">
          <div className="op-card-row is-dealer" data-testid="dealer-cards">
            {(hand?.dealer_cards || [
              { rank: "?", suit: "?", hidden: true },
              { rank: "?", suit: "?", hidden: true },
            ]).map((card, i) => (
              <Card key={`d${i}`} card={card} deal={i} />
            ))}
          </div>
          <div className="op-bj-arc">BLACKJACK · 21</div>
          <div className="op-card-row is-player" data-testid="player-cards">
            {(hand?.player_cards || []).map((card, i) => (
              <Card key={`p${i}`} card={card} deal={i + 2} />
            ))}
          </div>
          <div className="op-bj-seat" aria-label="Место игрока">
            ВЫ
          </div>
        </div>
      </div>
      <p className="op-status">
        {hand
          ? `Игрок ${hand.player_total}${hand.dealer_total != null ? ` · дилер ${hand.dealer_total}` : ""} · ${formatPlayBalance(hand.wager_chips)}`
          : "Выберите фишку и сдайте карты"}
      </p>
      {hand?.settlement ? (
        <p data-testid="bj-result">
          {hand.settlement.outcome.toUpperCase()} · {formatPlayBalance(hand.settlement.payout_chips)}
        </p>
      ) : null}
      {error ? (
        <p className="op-status" role="alert">
          {error}
        </p>
      ) : null}
      <ChipSelector value={wager} options={[25, 50, 100]} onChange={setWager} disabled={playing} />
      <div className="op-actions">
        <button className="op-cta" type="button" disabled={busy} onClick={() => void run(() => dealBlackjack(wager))}>
          {busy ? "…" : "СДАТЬ"}
        </button>
        <button className="op-cta secondary" type="button" disabled={busy || !playing} data-testid="bj-hit" onClick={() => hand && void run(() => hitBlackjack(hand.hand_id))}>
          ЕЩЁ
        </button>
        <button className="op-cta secondary" type="button" disabled={busy || !playing} data-testid="bj-stand" onClick={() => hand && void run(() => standBlackjack(hand.hand_id))}>
          ХВАТИТ
        </button>
        <button className="op-cta secondary" type="button" disabled={busy || !canDouble} data-testid="bj-double" onClick={() => hand && void run(() => doubleBlackjack(hand.hand_id))}>
          УДВОИТЬ
        </button>
      </div>
      <p className="op-chip-balance">{wallet.wallet ? formatPlayBalance(wallet.wallet.balance_chips) : "PLAY"}</p>
      <RoomNavigation current="blackjack" />
    </div>
  );
}
