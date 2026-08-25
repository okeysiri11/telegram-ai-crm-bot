import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { spinOdessaGold, type SlotSpin } from "../../casinoApi";
import { formatPlayBalance } from "../../currency";
import { loginRedirect } from "@/navigation/safeReturnTo";
import { useCasinoWallet } from "../../useCasinoSession";
import { casinoSound } from "../../casinoSound";

const ICONS: Record<string, string> = {
  CHERRY: "🍒",
  ANCHOR: "⚓",
  WAVE: "🌊",
  BAR: "BAR",
  SEVEN: "7",
  WILD: "★",
  ODESSA: "◆",
  CROWN: "♛",
};

export function SlotReels({ grid, spinning }: { grid: string[][]; spinning: boolean }) {
  return (
    <div className={`op-reels${spinning ? " is-spinning" : ""}`} data-testid="slot-reels">
      {(grid.length ? grid : Array.from({ length: 5 }, () => ["CHERRY", "BAR", "SEVEN"])).map((col, c) => (
        <div key={c} className="op-reel" style={{ animationDelay: `${c * 120}ms` }}>
          {col.map((sym, r) => (
            <span key={`${c}-${r}`}>{ICONS[sym] || sym}</span>
          ))}
        </div>
      ))}
    </div>
  );
}

export function OdessaGoldMachine() {
  const outlet = useOutletContext<{ wallet?: ReturnType<typeof useCasinoWallet> }>();
  const wallet = outlet?.wallet ?? { refresh: async () => undefined };
  const [wager, setWager] = useState(10);
  const [spin, setSpin] = useState<SlotSpin | null>(null);
  const [spinning, setSpinning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!spinning) return;
    const t = window.setTimeout(() => {
      setSpinning(false);
      casinoSound.slotStop();
    }, 1600);
    return () => window.clearTimeout(t);
  }, [spinning]);

  async function play() {
    setError(null);
    setSpinning(true);
    casinoSound.spin();
    try {
      const result = await spinOdessaGold(wager);
      setSpin(result);
      if (result.payout_chips > 0) casinoSound.win();
      await wallet.refresh();
    } catch (err) {
      const message = err instanceof Error ? err.message : "slot_failed";
      if (message === "auth_required") {
        window.location.assign(loginRedirect("/casino/slots/odessa-gold"));
        return;
      }
      setError("Недостаточно PLAY или ошибка автомата.");
      setSpinning(false);
    }
  }

  return (
    <section
      className="op-slot-machine"
      data-testid="odessa-gold"
      data-phase={spinning ? "spinning" : spin ? "result" : "idle"}
      aria-label="Odessa Gold"
    >
      <p className="op-kicker">ODESSA GOLD</p>
      <h1 className="op-title">Чёрное море · PLAY</h1>
      <SlotReels grid={spin?.reels || []} spinning={spinning} />
      {spin && !spinning ? (
        <p data-testid="slot-result">
          {spin.outcome.toUpperCase()} · {formatPlayBalance(spin.payout_chips)}
        </p>
      ) : (
        <p className="op-status">{spinning ? "Барабаны вращаются…" : "Ставка PLAY · результат только с сервера"}</p>
      )}
      {error ? <p className="op-status" role="alert">{error}</p> : null}
      <div className="op-actions">
        {[10, 50, 100].map((n) => (
          <button key={n} className={`op-ghost${wager === n ? " is-on" : ""}`} type="button" onClick={() => setWager(n)}>
            {n}
          </button>
        ))}
        <button className="op-cta" type="button" disabled={spinning} data-testid="slot-spin" onClick={() => void play()}>
          КРУТИТЬ {formatPlayBalance(wager)}
        </button>
      </div>
    </section>
  );
}
