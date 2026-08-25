import { Link } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { fetchCasinoLobby } from "./casinoApi";
import { CasinoLedgerPanel, CasinoWalletBar } from "./CasinoPanels";
import { useCasinoWallet } from "./useCasinoSession";
import type { CasinoFloorArea, CasinoLobby } from "./types";
import { useEffect, useState } from "react";
import "./casino.css";

const FALLBACK_FLOOR: CasinoFloorArea[] = [
  { id: "reception", label: "RECEPTION", label_ru: "РЕЦЕПЦИЯ", status: "soon", status_label: "Скоро", coming_soon: true },
  { id: "bar", label: "BAR", label_ru: "БАР", status: "soon", status_label: "Скоро", coming_soon: true },
  {
    id: "roulette",
    label: "ROULETTE",
    label_ru: "РУЛЕТКА",
    status: "open",
    status_label: "Идет прием ставок",
    coming_soon: false,
    route: "/casino/venues/odessa-prime/roulette",
  },
  { id: "blackjack", label: "BLACKJACK", label_ru: "БЛЭКДЖЕК", status: "soon", status_label: "Скоро", coming_soon: true },
  { id: "poker", label: "POKER", label_ru: "ПОКЕР", status: "soon", status_label: "Скоро", coming_soon: true },
  { id: "slots", label: "SLOTS", label_ru: "СЛОТЫ", status: "soon", status_label: "Скоро", coming_soon: true },
  { id: "vip", label: "VIP", label_ru: "VIP", status: "soon", status_label: "Скоро", coming_soon: true },
];

export function CasinoLobbyPage() {
  const [lobby, setLobby] = useState<CasinoLobby | null>(null);
  const [error, setError] = useState<string | null>(null);
  const walletState = useCasinoWallet();

  useEffect(() => {
    fetchCasinoLobby()
      .then(setLobby)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "lobby_failed"));
  }, []);

  const floor = lobby?.floor?.length ? lobby.floor : FALLBACK_FLOOR;

  return (
    <WorkspaceLayout>
      <div className="casino-floor">
        <p className="casino-kicker">Odessa Prime · DEMO ONLY</p>
        <h1 className="casino-title">Казино</h1>
        <p className="casino-copy">
          Вы входите глубже в зал: рецепция, бар, игровые столы. Работает европейская рулетка на PLAY / DEMO CHIPS.
          Реальных денег, карт и вывода нет.
        </p>
        <div className="casino-banner">
          <Badge>PLAY</Badge>
          <Badge>DEMO CHIPS</Badge>
          <Badge>No real money</Badge>
        </div>
        {error ? (
          <p className="casino-status" role="alert">
            {error}
          </p>
        ) : null}
        <Card title="Кошелек PLAY">
          <CasinoWalletBar
            wallet={walletState.wallet}
            loading={walletState.loading}
            error={walletState.error}
            onRefresh={() => void walletState.refresh()}
            onGranted={(next) => {
              walletState.setWallet(next);
              void walletState.refresh();
            }}
          />
        </Card>
        <div className="casino-map" aria-label="Карта зала">
          {floor.map((area) =>
            area.coming_soon ? (
              <div key={area.id} className="casino-area is-soon">
                <span className="casino-area-label">{area.label}</span>
                <span className="casino-area-ru">{area.label_ru}</span>
                <span className="eds-type-helper">Скоро</span>
              </div>
            ) : (
              <Link
                key={area.id}
                className="casino-area is-live"
                to={area.route || "/casino/venues/odessa-prime/roulette"}
                aria-label="Открыть рулетку"
              >
                <span className="casino-area-label">{area.label}</span>
                <span className="casino-area-ru">{area.label_ru}</span>
                <span className="eds-type-helper">{area.status_label}</span>
                <span>Войти за стол →</span>
              </Link>
            ),
          )}
        </div>
        {!lobby && !error ? <p className="eds-type-helper">Загрузка лобби…</p> : null}
        <Card title="История PLAY">
          <CasinoLedgerPanel items={walletState.ledger} loading={walletState.loading} error={walletState.error} />
        </Card>
        <div className="casino-nav">
          <Link to="/enterprise-city">
            <Button variant="secondary">Вернуться в City</Button>
          </Link>
          <Link to="/casino/venues/odessa-prime">
            <Button variant="ghost">Зал Odessa Prime</Button>
          </Link>
        </div>
      </div>
    </WorkspaceLayout>
  );
}
