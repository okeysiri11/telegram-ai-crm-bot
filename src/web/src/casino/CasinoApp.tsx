import { Navigate, Route, Routes } from "react-router-dom";
import { CasinoShell } from "./components/CasinoShell";
import { EntranceScene } from "./scenes/EntranceScene";
import { LobbyScene } from "./scenes/LobbyScene";
import { CasinoGamesPage } from "./CasinoGamesPage";
import { CasinoTableBrowserPage } from "./CasinoTableBrowserPage";
import { RoomNavigation } from "./components/RoomNavigation";
import { CasinoSoonPage } from "./components/CasinoSoonModal";
import { lazyCasinoPage } from "./lazyCasinoPage";

const RouletteHall = lazyCasinoPage(() => import("./rooms/RouletteHall"));
const BlackjackSalon = lazyCasinoPage(() => import("./rooms/BlackjackSalon"));
const SlotParlor = lazyCasinoPage(() => import("./rooms/SlotParlor"));
const PokerRoom = lazyCasinoPage(() => import("./rooms/PokerRoom"));
const VipRoom = lazyCasinoPage(() => import("./rooms/VipRoom"));
const RestaurantRoom = lazyCasinoPage(() => import("./rooms/RestaurantRoom"));
const BarRoom = lazyCasinoPage(() => import("./rooms/BarRoom"));
const RouletteTable = lazyCasinoPage(() => import("./games/roulette/RouletteTable"));
const OdessaGoldMachine = lazyCasinoPage(() => import("./games/slots/OdessaGoldMachine"));

function CasinoUnknown() {
  return (
    <section className="op-room" data-testid="casino-unknown">
      <p className="op-kicker">ODESSA PRIME</p>
      <h1 className="op-title">Зал не найден</h1>
      <p className="op-sub">Вернитесь в лобби или откройте карту. Вы остаётесь в казино.</p>
      <RoomNavigation current="roulette" />
    </section>
  );
}

export function CasinoApp() {
  return (
    <Routes>
      <Route element={<CasinoShell />}>
        <Route index element={<EntranceScene />} />
        <Route path="lobby" element={<LobbyScene />} />
        <Route path="floor" element={<LobbyScene />} />
        <Route path="map" element={<LobbyScene view="map" />} />
        <Route path="games" element={<CasinoGamesPage />} />
        <Route path="halls" element={<CasinoGamesPage />} />
        <Route path="tables" element={<CasinoTableBrowserPage />} />
        <Route path="rooms/roulette" element={<RouletteHall />} />
        <Route path="rooms/blackjack" element={<BlackjackSalon />} />
        <Route path="rooms/slots" element={<SlotParlor />} />
        <Route path="rooms/poker" element={<PokerRoom />} />
        <Route path="rooms/vip" element={<VipRoom />} />
        <Route path="rooms/restaurant" element={<RestaurantRoom />} />
        <Route path="rooms/bar" element={<BarRoom />} />
        <Route path="blackjack" element={<BlackjackSalon />} />
        <Route path="slots" element={<SlotParlor />} />
        <Route path="poker" element={<PokerRoom />} />
        <Route path="vip" element={<VipRoom />} />
        <Route path="restaurant" element={<RestaurantRoom />} />
        <Route path="bar" element={<BarRoom />} />
        <Route path="roulette" element={<RouletteHall />} />
        <Route path="roulette/table/:tableId" element={<RouletteTable />} />
        <Route path="roulette/royale-1" element={<RouletteTable />} />
        <Route path="roulette/:tableId" element={<RouletteTable />} />
        <Route path="slots/odessa-gold" element={<OdessaGoldMachine />} />
        <Route path="venues/:venueId/roulette" element={<Navigate to="/casino/roulette/royale-1" replace />} />
        <Route path="venues/:venueId" element={<Navigate to="/casino" replace />} />
        <Route path="promos" element={<CasinoSoonPage title="Акции" />} />
        <Route path="tournaments" element={<CasinoSoonPage title="Турниры" />} />
        <Route path="support" element={<CasinoSoonPage title="Поддержка" />} />
        <Route path="*" element={<CasinoUnknown />} />
      </Route>
    </Routes>
  );
}
