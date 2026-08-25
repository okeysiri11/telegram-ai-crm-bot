import { useState } from "react";

export function useBetLock(phase: string) {
  const locked = phase !== "BETTING_OPEN";
  const [flies, setFlies] = useState<Array<{ id: number; x: number; y: number }>>([]);

  function spawnChip(x: number, y: number) {
    if (locked) return;
    const id = Date.now() + Math.random();
    setFlies((prev) => [...prev.slice(-8), { id, x, y }]);
    window.setTimeout(() => {
      setFlies((prev) => prev.filter((item) => item.id !== id));
    }, 700);
  }

  return { locked, flies, spawnChip };
}
