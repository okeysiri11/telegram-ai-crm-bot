import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { CasinoShell } from "./components/CasinoShell";
import { EntranceScene } from "./scenes/EntranceScene";
import { LobbyScene } from "./scenes/LobbyScene";
import { CasinoMap } from "./scenes/CasinoMap";
import { CasinoGamesPage } from "./CasinoGamesPage";
import { CasinoTableBrowserPage } from "./CasinoTableBrowserPage";
import { RouletteHall } from "./rooms/RouletteHall";
import { BlackjackSalon } from "./rooms/BlackjackSalon";
import { SlotParlor } from "./rooms/SlotParlor";
import { OdessaGoldMachine } from "./games/slots/OdessaGoldMachine";
import { RouletteTable } from "./games/roulette/RouletteTable";
import { RoomSkeleton } from "./components/RoomSkeleton";

const PokerRoom = lazy(() => import("./rooms/PokerRoom"));
const VipRoom = lazy(() => import("./rooms/VipRoom"));
const RestaurantRoom = lazy(() => import("./rooms/RestaurantRoom"));
const BarRoom = lazy(() => import("./rooms/BarRoom"));

export function CasinoApp() {
  return (
    <Routes>
      <Route element={<CasinoShell />}>
        <Route index element={<EntranceScene />} />
        <Route path="lobby" element={<Navigate to="/casino/floor" replace />} />
        <Route path="floor" element={<LobbyScene />} />
        <Route path="map" element={<CasinoMap />} />
        <Route path="games" element={<CasinoGamesPage />} />
        <Route path="rooms/roulette" element={<RouletteHall />} />
        <Route path="rooms/blackjack" element={<BlackjackSalon />} />
        <Route path="rooms/slots" element={<SlotParlor />} />
        <Route
          path="rooms/poker"
          element={
            <Suspense fallback={<RoomSkeleton />}>
              <PokerRoom />
            </Suspense>
          }
        />
        <Route
          path="rooms/vip"
          element={
            <Suspense fallback={<RoomSkeleton />}>
              <VipRoom />
            </Suspense>
          }
        />
        <Route
          path="rooms/restaurant"
          element={
            <Suspense fallback={<RoomSkeleton />}>
              <RestaurantRoom />
            </Suspense>
          }
        />
        <Route
          path="rooms/bar"
          element={
            <Suspense fallback={<RoomSkeleton />}>
              <BarRoom />
            </Suspense>
          }
        />
        <Route path="blackjack" element={<Navigate to="/casino/rooms/blackjack" replace />} />
        <Route path="slots" element={<Navigate to="/casino/rooms/slots" replace />} />
        <Route path="poker" element={<Navigate to="/casino/rooms/poker" replace />} />
        <Route path="vip" element={<Navigate to="/casino/rooms/vip" replace />} />
        <Route path="restaurant" element={<Navigate to="/casino/rooms/restaurant" replace />} />
        <Route path="bar" element={<Navigate to="/casino/rooms/bar" replace />} />
        <Route path="roulette" element={<CasinoTableBrowserPage />} />
        <Route path="roulette/:tableId" element={<RouletteTable />} />
        <Route path="slots/odessa-gold" element={<OdessaGoldMachine />} />
        <Route path="venues/:venueId/roulette" element={<Navigate to="/casino/roulette/roulette-royale-1" replace />} />
        <Route path="venues/:venueId" element={<Navigate to="/casino" replace />} />
        <Route path="*" element={<Navigate to="/casino" replace />} />
      </Route>
    </Routes>
  );
}
