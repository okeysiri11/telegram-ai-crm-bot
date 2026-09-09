import { useCallback, useRef, useState } from "react";
import { resolveSlotSpin } from "./slotEngine";
import type { SlotGameDefinition, SlotHistoryItem, SlotSpinResult } from "./slotTypes";

const STORAGE_KEY = "op-slot-demo-v1";
const HISTORY_LIMIT = 10;
const SPIN_MS = 1200;

type DemoStore = {
  balance: number;
  history: SlotHistoryItem[];
};

function readStore(starting: number): DemoStore {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { balance: starting, history: [] };
    const parsed = JSON.parse(raw) as DemoStore;
    if (typeof parsed.balance !== "number" || !Array.isArray(parsed.history)) {
      return { balance: starting, history: [] };
    }
    return parsed;
  } catch {
    return { balance: starting, history: [] };
  }
}

function writeStore(store: DemoStore) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch {
    /* ignore */
  }
}

export function useSlotDemo(def: SlotGameDefinition) {
  const starting = def.demoStartingBalance;
  const [store, setStore] = useState<DemoStore>(() => readStore(starting));
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState<SlotSpinResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const lock = useRef(false);

  const persist = useCallback((next: DemoStore) => {
    setStore(next);
    writeStore(next);
  }, []);

  const addCredits = useCallback(
    (amount: number) => {
      if (!Number.isFinite(amount) || amount <= 0) return store.balance;
      const next = store.balance + Math.floor(amount);
      persist({ ...store, balance: next });
      setError(null);
      return next;
    },
    [persist, store],
  );

  const cashOut = useCallback(() => {
    if (lock.current || spinning) return 0;
    const amount = store.balance;
    persist({ ...store, balance: 0 });
    setResult(null);
    setError(null);
    return amount;
  }, [persist, spinning, store]);

  const spin = useCallback(
    (bet: number) => {
      if (lock.current || spinning) return null;
      setError(null);
      if (store.balance < bet) {
        setError("Недостаточно демо-кредитов.");
        return null;
      }
      lock.current = true;
      const nextResult = resolveSlotSpin(def, bet);
      persist({
        balance: store.balance - nextResult.bet,
        history: store.history,
      });
      setResult(nextResult);
      setSpinning(true);
      window.setTimeout(() => {
        persist({
          balance: store.balance - nextResult.bet + nextResult.win,
          history: [
            {
              game: def.title,
              machineId: def.id,
              bet: nextResult.bet,
              win: nextResult.win,
              ts: nextResult.ts,
            },
            ...store.history,
          ].slice(0, HISTORY_LIMIT),
        });
        setSpinning(false);
        lock.current = false;
      }, SPIN_MS);
      return nextResult;
    },
    [def, persist, spinning, store.balance, store.history],
  );

  return {
    balance: store.balance,
    history: store.history,
    spinning,
    result,
    error,
    spin,
    addCredits,
    cashOut,
  };
}
