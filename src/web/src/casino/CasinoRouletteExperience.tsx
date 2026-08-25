import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useOutletContext } from "react-router-dom";
import { RouletteWheel } from "./RouletteWheel";
import { CasinoBettingBoard, type BoardBet } from "./CasinoBettingBoard";
import { useCasinoPresence, useCasinoWallet } from "./useCasinoSession";
import { openRouletteRound, placeRouletteBet, spinRoulette } from "./casinoApi";
import { CHIP_DENOMS, formatPlayBalance } from "./currency";
import { casinoSound } from "./casinoSound";
import { loginRedirect } from "@/navigation/safeReturnTo";

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

export function CasinoRouletteExperience() {
  const { tableId = "roulette-royale-1" } = useParams();
  const live = tableId === "roulette-royale-1" || tableId === "roulette-royale";
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
  const roundId = useRef<string | null>(null);

  const total = useMemo(() => Object.values(stacks).reduce((a, b) => a + b, 0), [stacks]);

  useEffect(() => {
    void presence.join("roulette-royale-1").catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tableId]);

  const addBet = useCallback((bet: BoardBet) => {
    if (phase !== "BETTING_OPEN") return;
    casinoSound.chip();
    setStacks((prev) => ({ ...prev, [bet.key]: (prev[bet.key] || 0) + chip }));
    setBets((prev) => [...prev, { ...bet }]);
  }, [chip, phase]);

  function clear() {
    setStacks({});
    setBets([]);
  }

  function repeat() {
    const saved = lastBets.current;
    if (!saved.length) return;
    setBets(saved);
    const next: Record<string, number> = {};
    for (const bet of saved) {
      next[bet.key] = (next[bet.key] || 0) + chip;
    }
    setStacks(next);
  }

  function doubleDown() {
    setStacks((prev) => {
      const next: Record<string, number> = {};
      for (const [k, v] of Object.entries(prev)) next[k] = v * 2;
      return next;
    });
    setBets((prev) => [...prev, ...prev]);
  }

  async function confirmAndSpin() {
    if (!live) return;
    setBusy(true);
    setError(null);
    try {
      const opened = await openRouletteRound("odessa-prime");
      roundId.current = opened.round_id;
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
        window.location.assign(loginRedirect(`/casino/roulette/${tableId}`));
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
    window.setTimeout(() => {
      setPhase("SETTLED");
      clear();
      window.setTimeout(() => {
        setPhase("BETTING_OPEN");
        setSeconds(18);
        setResult(null);
      }, 1600);
    }, 1400);
  }

  useEffect(() => {
    if (phase !== "BETTING_OPEN" && phase !== "BETTING_CLOSING") return;
    const t = window.setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => window.clearInterval(t);
  }, [phase]);

  if (!live) {
    return (
      <div className="op-floor">
        <p className="op-status">Этот стол скоро откроется.</p>
      </div>
    );
  }

  return (
    <div className="op-table">
      <div>
        <RouletteWheel target={result?.n ?? null} spinning={spinning} onDone={onWheelDone} />
        <p className="op-phase">
          {PHASE_COPY[phase] || phase}
          {phase === "BETTING_OPEN" || phase === "BETTING_CLOSING" ? ` — ${seconds} сек` : ""}
        </p>
        {result && (phase === "RESULT" || phase === "SETTLED" || phase === "SPINNING") ? (
          <p>
            {phase === "SPINNING" ? "…" : `ВЫПАЛО: ${result.n} ${result.color.toUpperCase()}`}
          </p>
        ) : null}
        <p>История: {history.join(" · ") || "—"}</p>
      </div>
      <div>
        {error ? <p className="op-status" role="alert">{error}</p> : null}
        {walletState.error === "auth_required" ? (
          <p className="op-status">
            <a href={loginRedirect(`/casino/roulette/${tableId}`)}>Войти</a>, чтобы играть на PLAY.
          </p>
        ) : null}
        <CasinoBettingBoard stacks={stacks} onPick={addBet} />
        <div className="op-sticky">
          <div className="op-rail" role="group" aria-label="Фишки PLAY">
            {CHIP_DENOMS.map((value) => (
              <button
                key={value}
                type="button"
                className={`op-chip${chip === value ? " is-on" : ""}`}
                onClick={() => setChip(value)}
              >
                {value >= 1000 ? `${value / 1000}k` : value}
              </button>
            ))}
          </div>
          <div>Ставка: {formatPlayBalance(total)}</div>
          <div>Баланс: {walletState.wallet ? formatPlayBalance(walletState.wallet.balance_chips) : "—"}</div>
          <div className="op-actions">
            <button className="op-ghost" type="button" onClick={clear}>
              ОЧИСТИТЬ
            </button>
            <button className="op-ghost" type="button" onClick={repeat}>
              ПОВТОРИТЬ
            </button>
            <button className="op-ghost" type="button" onClick={doubleDown}>
              УДВОИТЬ
            </button>
            <button className="op-cta" type="button" disabled={busy || !total} onClick={() => void confirmAndSpin()}>
              СДЕЛАТЬ СТАВКУ
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
        <p className="op-status">Чат стола — скоро</p>
      </aside>
    </div>
  );
}
