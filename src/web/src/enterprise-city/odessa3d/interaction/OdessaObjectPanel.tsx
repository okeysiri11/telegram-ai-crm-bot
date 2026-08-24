/**
 * Compact selected-object panel. BOUND uses catalog data only; UNBOUND stays technical.
 */

import { useState } from "react";
import { Badge, Button, Card } from "@/ui";
import { isFavorite, toggleFavorite } from "./favorites";
import { NO_DATA, objectPanelFacts } from "./objectPanelFacts";
import type { EntityBindingResult, PickableEntity } from "./types";

type Props = {
  pickable: PickableEntity | null;
  binding: EntityBindingResult | null;
  selectedActive: boolean;
  showDev?: boolean;
  clickGeo?: { lat: number; lon: number } | null;
  objectGeo?: { lat: number; lon: number } | null;
  georeferenceReady?: boolean;
  onOpen?: () => void;
  onFocus?: () => void;
  onClear?: () => void;
  onCopyCoords?: () => void;
  onShowIn2d?: () => void;
};

export function OdessaObjectPanel({
  pickable,
  binding,
  selectedActive,
  showDev = false,
  clickGeo = null,
  objectGeo = null,
  georeferenceReady = false,
  onOpen,
  onFocus,
  onClear,
  onCopyCoords,
  onShowIn2d,
}: Props) {
  const [favTick, setFavTick] = useState(0);
  if (!pickable || !binding) return null;
  const bound = binding.status === "BOUND";
  const ambiguous = binding.status === "AMBIGUOUS";
  const facts = objectPanelFacts(pickable, binding);
  const favorited = favTick >= 0 && isFavorite(pickable.pickId);

  return (
    <div className="ec-3d-object-panel pointer-events-auto" data-testid="odessa-object-panel">
    <Card
      className="max-w-sm text-sm"
      title={facts.name === NO_DATA ? "3D объект" : facts.name}
      actions={
        <Button size="sm" variant="ghost" className="min-h-11" onClick={onClear}>
          Снять выбор
        </Button>
      }
    >
      {!selectedActive ? (
        <p className="mb-2 text-[var(--eds-warning)]" data-testid="odessa-object-inactive">
          Объект сейчас не активен
        </p>
      ) : null}

      {ambiguous ? (
        <p className="mb-2 text-[var(--eds-warning)]">Неоднозначная привязка — показаны только 3D данные.</p>
      ) : null}
      {!bound ? (
        <p className="mb-2 text-[var(--eds-text-muted)]" data-testid="odessa-object-unbound">
          Нет связи с объектом Enterprise City
        </p>
      ) : null}

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1" data-testid="odessa-object-facts">
        <dt className="opacity-70">Название</dt>
        <dd className="truncate">{facts.name}</dd>
        <dt className="opacity-70">Тип объекта</dt>
        <dd className="truncate">{facts.type}</dd>
        <dt className="opacity-70">ID</dt>
        <dd className="truncate font-mono text-[11px]">{facts.id}</dd>
        <dt className="opacity-70">Позиция XYZ</dt>
        <dd className="font-mono text-[11px]">
          {facts.position.x}, {facts.position.y}, {facts.position.z}
        </dd>
        <dt className="opacity-70">Размеры</dt>
        <dd className="font-mono text-[11px]">
          {facts.size.x} × {facts.size.y} × {facts.size.z}
        </dd>
        {binding.module ? (
          <>
            <dt className="opacity-70">Модуль</dt>
            <dd>{binding.module}</dd>
          </>
        ) : null}
        {binding.statusLabel ? (
          <>
            <dt className="opacity-70">Статус</dt>
            <dd>{binding.statusLabel}</dd>
          </>
        ) : null}
        {pickable.layerId ? (
          <>
            <dt className="opacity-70">Слой</dt>
            <dd>{pickable.layerId}</dd>
          </>
        ) : null}
        {showDev ? (
          <>
            <dt className="opacity-70">pickId</dt>
            <dd className="truncate font-mono text-[11px]">{pickable.pickId}</dd>
          </>
        ) : null}
      </dl>

      <div className="mt-3 flex flex-wrap gap-2">
        {bound && binding.route ? (
          <Button size="sm" className="min-h-11" onClick={onOpen} data-testid="odessa-open-object">
            Открыть объект
          </Button>
        ) : null}
        <Button
          size="sm"
          variant="ghost"
          className="min-h-11"
          onClick={onFocus}
          disabled={!selectedActive}
          data-testid="odessa-focus-object"
        >
          Приблизить
        </Button>
        <Button
          size="sm"
          variant={favorited ? "primary" : "ghost"}
          className="min-h-11"
          onClick={() => {
            toggleFavorite({
              pickId: pickable.pickId,
              name: facts.name,
              assetId: pickable.assetId,
            });
            setFavTick((n) => n + 1);
          }}
          data-testid="odessa-favorite-object"
        >
          {favorited ? "В избранном" : "Добавить в избранное"}
        </Button>
        <Button size="sm" variant="ghost" className="min-h-11" onClick={onClear} data-testid="odessa-clear-selection">
          Снять выбор
        </Button>
        {bound ? <Badge tone="success">BOUND</Badge> : <Badge>UNBOUND</Badge>}
      </div>
      <div className="mt-3 border-t border-[var(--eds-border)] pt-2" data-testid="odessa-object-geo">
        {!georeferenceReady ? (
          <p className="text-[var(--eds-text-muted)]" data-testid="odessa-geo-unready">
            Геопривязка не выполнена
          </p>
        ) : (
          <>
            {objectGeo ? (
              <div data-testid="odessa-object-centroid-geo">
                <p className="opacity-70">Географическая позиция объекта</p>
                <p className="font-mono text-xs">
                  {objectGeo.lat.toFixed(6)}
                  <br />
                  {objectGeo.lon.toFixed(6)}
                </p>
              </div>
            ) : null}
            {clickGeo ? (
              <div className="mt-2" data-testid="odessa-click-geo">
                <p className="opacity-70">Координаты</p>
                <p className="font-mono text-xs">
                  {clickGeo.lat.toFixed(6)}
                  <br />
                  {clickGeo.lon.toFixed(6)}
                </p>
                <p className="mt-1 text-[11px] opacity-60">Точка клика, не адрес здания</p>
              </div>
            ) : null}
            <div className="mt-2 flex flex-wrap gap-2">
              <Button size="sm" variant="ghost" className="min-h-11" onClick={onCopyCoords} data-testid="odessa-copy-coords">
                Копировать координаты
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={onShowIn2d} data-testid="odessa-show-in-2d">
                Показать в 2D
              </Button>
            </div>
          </>
        )}
      </div>
    </Card>
    </div>
  );
}
