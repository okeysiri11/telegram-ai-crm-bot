import { Link, useOutletContext } from "react-router-dom";
import { fetchCasinoRooms } from "../casinoApi";
import { formatPlayBalance } from "../currency";
import { useEffect, useState } from "react";
import { useCasinoWallet } from "../useCasinoSession";
import { CASINO_ROUTES } from "../state/casinoRoutes";

export function EntranceScene() {
  const outlet = useOutletContext<{ wallet?: ReturnType<typeof useCasinoWallet> }>();
  const wallet = outlet?.wallet ?? { wallet: null, ledger: [], loading: false, error: null, refresh: async () => undefined, setWallet: () => undefined, setLedger: () => undefined };
  const [live, setLive] = useState(0);
  const [tables, setTables] = useState(3);

  useEffect(() => {
    fetchCasinoRooms("odessa-prime")
      .then((rooms) => {
        setLive(rooms.online_count);
        setTables(rooms.tables.filter((t) => !t.coming_soon).length || 3);
      })
      .catch(() => undefined);
  }, []);

  return (
    <section className="op-entrance op-cinematic" aria-label="Вход Odessa Prime" data-testid="casino-entrance">
      <div className="op-scene">
        <div className="op-layer op-layer-back" />
        <div className="op-layer op-layer-hall" />
        <div className="op-chandelier" aria-hidden />
        <div className="op-columns" aria-hidden>
          <span className="op-col" />
          <span className="op-col" />
          <span className="op-col" />
          <span className="op-col" />
        </div>
        <div className="op-tables-depth" aria-hidden>
          <span className="op-felt-oval" />
          <span className="op-felt-oval" />
          <span className="op-felt-oval" />
        </div>
        <div className="op-marble" />
        <div className="op-doors" aria-hidden />
      </div>
      <div className="op-hero">
        <p className="op-kicker op-sign-shimmer">ОДЕССА · MONACO HALL</p>
        <h1 className="op-title">ODESSA PRIME CASINO</h1>
        <p className="op-sub">Игровой мир · рулетка · blackjack · Odessa Gold · только PLAY / DEMO CHIPS</p>
        <div className="op-cta-row">
          <Link className="op-cta" to={CASINO_ROUTES.lobbyAlias}>
            ВОЙТИ В КАЗИНО
          </Link>
          <Link className="op-cta secondary" to={CASINO_ROUTES.games}>
            ВЫБРАТЬ ИГРУ
          </Link>
          <Link className="op-cta secondary" to={CASINO_ROUTES.cityReturn}>
            ВЕРНУТЬСЯ В ГОРОД
          </Link>
        </div>
        <div className="op-stats">
          <div>
            LIVE PLAYERS
            <b>{live}</b>
          </div>
          <div>
            DEMO BALANCE
            <b>{wallet.wallet ? formatPlayBalance(wallet.wallet.balance_chips) : "—"}</b>
          </div>
          <div>
            ACTIVE TABLES
            <b>{tables}</b>
          </div>
        </div>
      </div>
    </section>
  );
}
