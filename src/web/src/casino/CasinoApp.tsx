import { Navigate, Route, Routes } from "react-router-dom";
import { CasinoShell } from "./components/CasinoShell";
import { EntranceScene } from "./scenes/EntranceScene";
import { LobbyScene } from "./scenes/LobbyScene";
import { CasinoMap } from "./scenes/CasinoMap";
import { CasinoGamesPage } from "./CasinoGamesPage";
import { CasinoTableBrowserPage } from "./CasinoTableBrowserPage";
import { RouletteTable } from "./games/roulette/RouletteTable";
import { RouletteHall } from "./rooms/RouletteHall";
import { BlackjackSalon } from "./rooms/BlackjackSalon";
import { SlotParlor } from "./rooms/SlotParlor";
import { OdessaGoldMachine } from "./games/slots/OdessaGoldMachine";

export function CasinoApp() {
  return (
    <Routes>
      <Route element={<CasinoShell />}>
        <Route index element={<EntranceScene />} />
        <Route path="floor" element={<LobbyScene />} />
        <Route path="map" element={<CasinoMap />} />
        <Route path="games" element={<CasinoGamesPage />} />
        <Route path="rooms/roulette" element={<RouletteHall />} />
        <Route path="rooms/blackjack" element={<BlackjackSalon />} />
        <Route path="rooms/slots" element={<SlotParlor />} />
        <Route path="roulette" element={<CasinoTableBrowserPage />} />
        <Route path="roulette/:tableId" element={<RouletteTable />} />
        <Route path="slots/odessa-gold" element={<OdessaGoldMachine />} />
        <Route path="venues/:venueId/roulette" element={<Navigate to="/casino/roulette/roulette-royale-1" replace />} />
        <Route path="venues/:venueId" element={<Navigate to="/casino" replace />} />
      </Route>
    </Routes>
  );
}
