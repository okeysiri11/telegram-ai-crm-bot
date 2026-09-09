import { useCallback, useEffect, useState } from "react";
import { casinoSound } from "../../casinoSound";
import { INSERT_BILL_CREDITS } from "./cabinetControls";
import type { SlotGameDefinition } from "./slotTypes";
import type { useSlotDemo } from "./useSlotDemo";

type Demo = ReturnType<typeof useSlotDemo>;

export function usePhysicalCabinetControls(def: SlotGameDefinition, demo: Demo) {
  const [bet, setBet] = useState(def.betSteps[0] || 10);
  const [auto, setAuto] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [serviceOpen, setServiceOpen] = useState(false);
  const [cardInserted, setCardInserted] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const play = useCallback(() => {
    if (demo.spinning) return;
    casinoSound.spin();
    const next = demo.spin(bet);
    if (!next) return;
    window.setTimeout(() => {
      casinoSound.slotStop();
      if (next.win > 0) casinoSound.win();
    }, 1100);
  }, [bet, demo]);

  useEffect(() => {
    if (!auto || demo.spinning) return undefined;
    const id = window.setTimeout(() => {
      if (demo.spinning) return;
      play();
    }, 420);
    return () => window.clearTimeout(id);
  }, [auto, demo.spinning, play]);

  const stepBet = useCallback(
    (dir: -1 | 1) => {
      const i = def.betSteps.indexOf(bet);
      const next = def.betSteps[Math.max(0, Math.min(def.betSteps.length - 1, i + dir))];
      if (next != null) setBet(next);
    },
    [bet, def.betSteps],
  );

  const cashOut = useCallback(() => {
    if (demo.spinning) return;
    setAuto(false);
    const amount = demo.cashOut();
    setNotice(amount > 0 ? `Выведено ${amount} демо-кредитов.` : "Баланс уже пуст.");
  }, [demo]);

  const insertBill = useCallback(() => {
    demo.addCredits(INSERT_BILL_CREDITS);
    setNotice(`Купюра принята · +${INSERT_BILL_CREDITS}`);
  }, [demo]);

  const insertCard = useCallback(() => {
    setCardInserted(true);
    setNotice("Карта принята. Демо-режим.");
  }, []);

  return {
    bet,
    setBet,
    auto,
    setAuto,
    historyOpen,
    setHistoryOpen,
    serviceOpen,
    setServiceOpen,
    cardInserted,
    notice,
    play,
    stepBet,
    cashOut,
    insertBill,
    insertCard,
  };
}
