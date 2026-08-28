import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useOutletContext, useLocation } from "react-router-dom";
import { RouletteWheel } from "./RouletteWheel";
import { CasinoBettingBoard, type BoardBet } from "./BettingBoard";
import { DealerPortrait } from "../../components/DealerPortrait";
import { useCasinoPresence, useCasinoWallet } from "../../useCasinoSession";
import { openRouletteRound, placeRouletteBet, spinRoulette } from "../../casinoApi";
import { CHIP_DENOMS, formatPlayBalance } from "../../currency";
import { useBetLock } from "../../hooks/useBetLock";
import { casinoSound } from "../../casinoSound";
import { isLiveRouletteTable } from "../../state/casinoRoutes";
import { ChipSelector } from "../../components/ChipSelector";
import { useCasinoGuest } from "../../components/CasinoGuestModal";
import { RoomNavigation } from "../../components/RoomNavigation";

const PHASE_COPY: Record<string, string> = {
  BETTING_OPEN: "СТАВКИ ПРИНИМАЮТСЯ",
  BETTING_CLOSING: "ДО СТОПА СТАВОК",
  NO_MORE_BETS: "СТАВОК БОЛЬШЕ НЕТ",
  SPINNING: "РУЛЕТКА ВРАЩАЕТСЯ",
  RESULT: "РЕЗУЛЬТАТ",
  SETTLED: "РАУНД ЗАВЕРШЁН",
};

function friendly(message: string): string {
  if (message === "auth_required" || message.includes("Authentication")) return "Войдите, чтобы сделать ставку PLAY.";
  if (message.toLowerCase().includes("insufficient")) return "Недостаточно PLAY.";
  if (message.toLowerCase().includes("cooldown")) return "Демо-фишки пока недоступны.";
  if (message.toLowerCase().includes("wager")) return "Ставка вне лимита стола.";
  return "Не удалось выполнить действие. Попробуйте ещё раз.";
}

export function RouletteTable() {
  const { tableId = "roulette-royale-1" } = useParams();
  const location = useLocation();
  const live = isLiveRouletteTable(tableId);
  const guest = useCasinoGuest();
  const { wallet: walletState } = useOutletContext<{ wallet: ReturnType<typeof useCasinoWallet> }>();
  const presence = useCasinoPresence("odessa-prime", "roulette-royale-1");
  const [chip, setChip] = useState(10);
  const [stacks, setStacks] = useState<Record<string, number>>({});
  const [bets, setBets] = useState<BoardBet[]>([]);
  const lastBets = useRef<BoardBet[]>([]);
  const [phase, setPhase] = useState("BETTING_OPEN");
  const [seconds, setSeconds] = useState(18);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ n: number; color: string } | null>(null);
  const [spinning, setSpinning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<number[]>([]);
  const lock = useBetLock(phase);
  const total = useMemo(() => Object.values(stacks).reduce((a, b) => a + b, 0), [stacks]);
  const alive = useRef(true);
  const roundTimers = useRef<number[]>([]);

  useEffect(() => {
    alive.current = true;
    void presence.join("roulette-royale-1").catch(() => undefined);
    return () => {
      alive.current = false;
      roundTimers.current.forEach((id) => window.clearTimeout(id));
      void presence.leave("roulette-royale-1").catch(() => undefined);
    };
  }, [tableId]);

  const addBet = useCallback(
    (bet: BoardBet) => {
      if (lock.locked) return;
      casinoSound.chip();
      lock.spawnChip(50, 40);
      setStacks((prev) => ({ ...prev, [bet.key]: (prev[bet.key] || 0) + chip }));
      setBets((prev) => [...prev, { ...bet }]);
    },
    [chip, lock],
  );

  function clear() {
    if (lock.locked) return;
    setStacks({});
    setBets([]);
  }

  async function confirmAndSpin() {
    if (!live || lock.locked && phase !== "BETTING_OPEN") return;
    setBusy(true);
    setError(null);
    try {
      const opened = await openRouletteRound("odessa-prime");
      const grouped = new Map<string, { bet: BoardBet; amount: number }>();
      for (const [key, amount] of Object.entries(stacks)) {
        const sample = bets.find((b) => b.key === key);
        if (!sample || amount <= 0) continue;
        grouped.set(key, { bet: sample, amount });
      }
      let i = 0;
      for (const [key, item] of grouped) {
        await placeRouletteBet(opened.round_id, {
          bet_type: item.bet.bet_type,
          amount_chips: item.amount,
          numbers: item.bet.bet_type === "straight" ? item.bet.numbers : undefined,
          idempotency_key: `${opened.round_id}-${key}-${i++}`,
        });
      }
      lastBets.current = bets;
      setPhase("BETTING_CLOSING");
      setSeconds(3);
      await new Promise((r) => setTimeout(r, 900));
      if (!alive.current) return;
      setPhase("NO_MORE_BETS");
      const spun = await spinRoulette(opened.round_id);
      if (spun.result_number == null) throw new Error("empty_result");
      casinoSound.spin();
      setResult({ n: spun.result_number, color: spun.result_color || "green" });
      setPhase("SPINNING");
      setSpinning(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : "spin_failed";
      if (message === "auth_required") {
        guest.openGuest(`${location.pathname}${location.search}` || "/casino/roulette/royale-1");
        return;
      }
      setError(friendly(message));
      setPhase("BETTING_OPEN");
    } finally {
      setBusy(false);
    }
  }

  function onWheelDone() {
    setSpinning(false);
    setPhase("RESULT");
    if (result) setHistory((h) => [result.n, ...h].slice(0, 12));
    void walletState.refresh();
    roundTimers.current.push(
      window.setTimeout(() => {
        setPhase("SETTLED");
        setStacks({});
        setBets([]);
        roundTimers.current.push(
          window.setTimeout(() => {
            setPhase("BETTING_OPEN");
            setSeconds(18);
            setResult(null);
          }, 1600),
        );
      }, 1400),
    );
  }

  useEffect(() => {
    if (phase !== "BETTING_OPEN" && phase !== "BETTING_CLOSING") return;
    const t = window.setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => window.clearInterval(t);
  }, [phase]);

  if (!live) {
    return <p className="op-status">Этот стол скоро откроется.</p>;
  }

  return (
    <div className="op-table op-table-scene" data-testid="roulette-table" data-phase={phase}>
      <div className="op-pit">
        <span className="op-table-lamp" aria-hidden />
        <span className="op-felt-bloom" aria-hidden />
        <span className="op-wood-rail" aria-hidden />
        <DealerPortrait />
        <RouletteWheel target={result?.n ?? null} spinning={spinning} onDone={onWheelDone} />
        <p className="op-phase" data-testid="round-phase">
          {PHASE_COPY[phase] || phase}
          {phase === "BETTING_OPEN" || phase === "BETTING_CLOSING" ? ` — ${seconds} сек` : ""}
        </p>
        {result && (phase === "RESULT" || phase === "SETTLED" || phase === "SPINNING") ? (
          <p data-testid="roulette-result">
            {phase === "SPINNING" ? "шар в движении…" : `ВЫПАЛО: ${result.n} ${result.color.toUpperCase()}`}
          </p>
        ) : null}
        <p>История: {history.join(" · ") || "—"}</p>
      </div>
      <div className={lock.locked ? "is-bet-locked" : undefined} data-testid="bet-lock">
        {lock.flies.map((fly) => (
          <span key={fly.id} className="op-chip-fly" style={{ left: fly.x, top: fly.y }} data-testid="chip-fly" />
        ))}
        {error ? <p className="op-status" role="alert">{error}</p> : null}
        <CasinoBettingBoard stacks={stacks} onPick={addBet} win={result && phase !== "SPINNING" ? result.n : null} />
        <div className="op-sticky">
          <ChipSelector value={chip} options={[...CHIP_DENOMS]} onChange={(n) => { casinoSound.tick(); setChip(n); }} disabled={lock.locked} />
          <div>Ставка: {formatPlayBalance(total)}</div>
          <div>Баланс: {walletState.wallet ? formatPlayBalance(walletState.wallet.balance_chips) : "—"}</div>
          <div className="op-actions">
            <button className="op-ghost" type="button" onClick={clear} disabled={lock.locked}>
              ОЧИСТИТЬ
            </button>
            <button className={`op-cta${busy ? " is-loading" : ""}`} type="button" disabled={busy || !total || lock.locked} onClick={() => void confirmAndSpin()}>
              {busy ? "РАУНД…" : "СДЕЛАТЬ СТАВКУ"}
            </button>
          </div>
        </div>
      </div>
      <aside className="op-sidebar" aria-label="Игроки">
        <div className="op-kicker">ИГРОКИ ({presence.active?.seats_taken ?? 0}/{presence.active?.seats_total ?? 6})</div>
        {(presence.active?.seats || []).map((seat) => (
          <div key={seat.seat} className="op-seat">
            <span className="op-avatar">{seat.display_name?.slice(-3) || seat.seat}</span>
            <span>{seat.occupied ? seat.display_name : `Место ${seat.seat}`}</span>
          </div>
        ))}
      </aside>
      <RoomNavigation current="roulette" />
    </div>
  );
}

export default RouletteTable;
