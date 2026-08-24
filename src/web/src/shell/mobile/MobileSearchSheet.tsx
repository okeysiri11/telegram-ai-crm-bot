import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button, Input } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { autoOpsGet, asList } from "../../../workspace/business-ops/opsApi";
import { useMobileChromeStore } from "./mobileChromeStore";
import { closeMobileOverlay, navigateFromMobileOverlay } from "./useMobileOverlayHistory";

type Hit = { kind?: string; id?: string; title?: string; extra?: string };

export function MobileSearchSheet() {
  const open = useMobileChromeStore((s) => s.searchOpen);
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const organizationId = useOrgSelector((s) => s.organizationId);
  const roleId = useRoleSwitcher((s) => s.activeRoleId);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const auto = pathname.startsWith("/workspace/auto");

  if (!open) return null;

  async function run(value: string) {
    setQ(value);
    setError(null);
    if (!value.trim()) {
      setHits([]);
      return;
    }
    if (!auto) {
      navigateFromMobileOverlay(navigate, `/search?q=${encodeURIComponent(value)}`);
      return;
    }
    setBusy(true);
    const res = await autoOpsGet(`/search?q=${encodeURIComponent(value)}`, {
      "X-Organization-Id": organizationId,
      "X-Tenant-Id": organizationId,
      "X-Role": roleId,
    });
    setBusy(false);
    if (!res.ok) {
      setError(String((res.json as { message_ru?: string })?.message_ru || "Поиск недоступен"));
      return;
    }
    setHits(asList(res.json) as Hit[]);
  }

  function openHit(hit: Hit) {
    if (hit.kind === "vehicle" && hit.id) {
      navigateFromMobileOverlay(navigate, `/workspace/auto?view=vehicles&vehicle=${hit.id}`);
      return;
    }
    navigateFromMobileOverlay(navigate, `/search?q=${encodeURIComponent(q)}`);
  }

  return (
    <>
      <button type="button" className="ados-mobile-overlay" aria-label="Закрыть поиск" onClick={closeMobileOverlay} />
      <div className="ados-mobile-sheet" data-testid="mobile-search-sheet" role="dialog" aria-modal="true">
        <div className="ados-mobile-sheet__head">
          <h2 className="font-semibold">Поиск</h2>
          <Button size="sm" variant="ghost" onClick={closeMobileOverlay}>
            Закрыть
          </Button>
        </div>
        <div className="ados-mobile-sheet__body space-y-3">
          <Input
            autoFocus
            value={q}
            placeholder={auto ? "VIN, контейнер, клиент" : "Найти в платформе"}
            onChange={(e) => void run(e.target.value)}
            data-testid="mobile-search-input"
          />
          {busy ? <p className="eds-type-caption">Ищем…</p> : null}
          {error ? <p className="eds-type-caption text-[var(--eds-danger)]">{error}</p> : null}
          {hits.length ? (
            <ul className="space-y-1">
              {hits.slice(0, 12).map((hit) => (
                <li key={`${hit.kind}-${hit.id}`}>
                  <button type="button" className="ados-mobile-card w-full text-left" onClick={() => openHit(hit)}>
                    {String(hit.kind || "hit")}: {String(hit.title || hit.id || "")} {String(hit.extra || "")}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => {
              navigateFromMobileOverlay(navigate, q.trim() ? `/search?q=${encodeURIComponent(q)}` : "/search");
            }}
          >
            Открыть глобальный поиск
          </Button>
        </div>
      </div>
    </>
  );
}
