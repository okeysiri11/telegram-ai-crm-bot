import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchCasinoLedger,
  fetchCasinoRooms,
  fetchCasinoWallet,
  joinCasinoRoom,
  leaveCasinoRoom,
} from "./casinoApi";
import type { CasinoLedgerEntry, CasinoRooms, CasinoTablePresence, CasinoWallet } from "./types";

export function useCasinoWallet() {
  const [wallet, setWallet] = useState<CasinoWallet | null>(null);
  const [ledger, setLedger] = useState<CasinoLedgerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextWallet, nextLedger] = await Promise.all([fetchCasinoWallet(), fetchCasinoLedger()]);
      setWallet(nextWallet);
      setLedger(nextLedger.items);
    } catch (err) {
      const message = err instanceof Error ? err.message : "wallet_failed";
      setError(message);
      if (message === "auth_required") {
        setWallet(null);
        setLedger([]);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { wallet, ledger, loading, error, refresh, setWallet, setLedger };
}

export function useCasinoPresence(venueId: string, roomId = "roulette-royale") {
  const [rooms, setRooms] = useState<CasinoRooms | null>(null);
  const [active, setActive] = useState<CasinoTablePresence | null>(null);
  const activeRef = useRef<CasinoTablePresence | null>(null);
  activeRef.current = active;
  const [reconnecting, setReconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadRooms = useCallback(async () => {
    try {
      setRooms(await fetchCasinoRooms(venueId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "rooms_failed");
    }
  }, [venueId]);

  const join = useCallback(
    async (id?: string) => {
      setError(null);
      try {
        const presence = await joinCasinoRoom(venueId, id || roomId);
        setActive(presence);
        await loadRooms();
        return presence;
      } catch (err) {
        const message = err instanceof Error ? err.message : "join_failed";
        setError(message);
        throw err;
      }
    },
    [loadRooms, roomId, venueId],
  );

  const leave = useCallback(
    async (id?: string) => {
      setError(null);
      const presence = await leaveCasinoRoom(venueId, id || roomId);
      setActive(null);
      await loadRooms();
      return presence;
    },
    [loadRooms, roomId, venueId],
  );

  const reconnect = useCallback(async () => {
    setReconnecting(true);
    try {
      await join(roomId);
    } catch {
      /* join sets error */
    } finally {
      setReconnecting(false);
    }
  }, [join, roomId]);

  useEffect(() => {
    void loadRooms();
  }, [loadRooms]);

  useEffect(() => {
    return () => {
      const current = activeRef.current;
      if (!current) return;
      void leaveCasinoRoom(venueId, current.room_id || roomId).catch(() => undefined);
    };
  }, [roomId, venueId]);

  useEffect(() => {
    const onVisible = () => {
      if (document.visibilityState === "visible" && activeRef.current) void reconnect();
    };
    const onOnline = () => {
      if (activeRef.current) void reconnect();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("online", onOnline);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("online", onOnline);
    };
  }, [reconnect]);

  return { rooms, active, reconnecting, error, join, leave, reconnect, loadRooms };
}
