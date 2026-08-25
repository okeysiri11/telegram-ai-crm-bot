import { Navigate, Route, Routes } from "react-router-dom";
import { CasinoShell } from "./CasinoShell";
import { CasinoEntrancePage } from "./CasinoEntrancePage";
import { CasinoFloorPage } from "./CasinoFloorPage";
import { CasinoGamesPage } from "./CasinoGamesPage";
import { CasinoTableBrowserPage } from "./CasinoTableBrowserPage";
import { CasinoRouletteExperience } from "./CasinoRouletteExperience";

export function CasinoApp() {
  return (
    <Routes>
      <Route element={<CasinoShell />}>
        <Route index element={<CasinoEntrancePage />} />
        <Route path="floor" element={<CasinoFloorPage />} />
        <Route path="games" element={<CasinoGamesPage />} />
        <Route path="roulette" element={<CasinoTableBrowserPage />} />
        <Route path="roulette/:tableId" element={<CasinoRouletteExperience />} />
        <Route path="venues/:venueId/roulette" element={<Navigate to="/casino/roulette/roulette-royale-1" replace />} />
        <Route path="venues/:venueId" element={<Navigate to="/casino" replace />} />
      </Route>
    </Routes>
  );
}
