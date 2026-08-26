import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { CasinoShell } from "./components/CasinoShell";
import { EntranceScene } from "./scenes/EntranceScene";
import { LobbyScene } from "./scenes/LobbyScene";
import { CasinoGamesPage } from "./CasinoGamesPage";
import { CasinoTableBrowserPage } from "./CasinoTableBrowserPage";
import { RouletteHall } from "./rooms/RouletteHall";
import { BlackjackSalon } from "./rooms/BlackjackSalon";
import { SlotParlor } from "./rooms/SlotParlor";
import { OdessaGoldMachine } from "./games/slots/OdessaGoldMachine";
import { RouletteTable } from "./games/roulette/RouletteTable";
import { RoomSkeleton } from "./components/RoomSkeleton";
import { RoomNavigation } from "./components/RoomNavigation";
import { CasinoSoonPage } from "./components/CasinoSoonModal";

const PokerRoom = lazy(() => import("./rooms/PokerRoom"));
const VipRoom = lazy(() => import("./rooms/VipRoom"));
const RestaurantRoom = lazy(() => import("./rooms/RestaurantRoom"));
const BarRoom = lazy(() => import("./rooms/BarRoom"));

function LiveRoulette() {
  return <RouletteTable />;
}

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
        <Route path="rooms/poker" element={<Suspense fallback={<RoomSkeleton />}><PokerRoom /></Suspense>} />
        <Route path="rooms/vip" element={<Suspense fallback={<RoomSkeleton />}><VipRoom /></Suspense>} />
        <Route path="rooms/restaurant" element={<Suspense fallback={<RoomSkeleton />}><RestaurantRoom /></Suspense>} />
        <Route path="rooms/bar" element={<Suspense fallback={<RoomSkeleton />}><BarRoom /></Suspense>} />
        <Route path="blackjack" element={<BlackjackSalon />} />
        <Route path="slots" element={<SlotParlor />} />
        <Route path="poker" element={<Suspense fallback={<RoomSkeleton />}><PokerRoom /></Suspense>} />
        <Route path="vip" element={<Suspense fallback={<RoomSkeleton />}><VipRoom /></Suspense>} />
        <Route path="restaurant" element={<Suspense fallback={<RoomSkeleton />}><RestaurantRoom /></Suspense>} />
        <Route path="bar" element={<Suspense fallback={<RoomSkeleton />}><BarRoom /></Suspense>} />
        <Route path="roulette" element={<RouletteHall />} />
        <Route path="roulette/table/:tableId" element={<LiveRoulette />} />
        <Route path="roulette/royale-1" element={<RouletteTable />} />
        <Route path="roulette/:tableId" element={<LiveRoulette />} />
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
