/**
 * Odessa 3D 3-point georeference calibration panel.
 */

import { useMemo, useRef, useState } from "react";
import { Badge, Button, Card, FormField, Input, Modal } from "@/ui";
import type { CalibrationSlotId, GeoreferenceStatus } from "./types";
import {
  CALIBRATION_SLOTS,
  applyGpsToSlot,
  clearCalibrationSlot,
  copyCalibrationDebugData,
  emptyCalibrationDraft,
  evaluateCalibrationDraft,
  type CalibrationDraft,
  type DraftControlPoint,
} from "./calibrationSession";

type Props = {
  open: boolean;
  draft: CalibrationDraft;
  pickingSlot: CalibrationSlotId | null;
  georeferenceStatus: GeoreferenceStatus | string;
  modelMismatch: boolean;
  message?: string | null;
  onClose: () => void;
  onAddPoint: (slot: CalibrationSlotId) => void;
  onDraftChange: (next: CalibrationDraft) => void;
  onSave: () => void;
  onReset: () => void;
  onExport: () => void;
  onImportText: (text: string) => void;
  onCopyPoint: (slot: CalibrationSlotId) => void;
  onCameraPreset: (kind: "top" | "tilt45" | "A" | "B" | "C") => void;
  onSavePoor?: () => void;
};

function fmt(n: number | null | undefined, digits = 2): string {
  return n == null || !Number.isFinite(n) ? "—" : n.toFixed(digits);
}

function PointCard({
  point,
  picking,
  gpsError,
  onAdd,
  onLatLon,
  onApplyGps,
  onCopy,
  onClear,
}: {
  point: DraftControlPoint;
  picking: boolean;
  gpsError?: string | null;
  onAdd: () => void;
  onLatLon: (latText: string, lonText: string) => void;
  onApplyGps: () => void;
  onCopy: () => void;
  onClear: () => void;
}) {
  const world = point.world
    ? `${point.world.x.toFixed(2)}, ${point.world.y.toFixed(2)}, ${point.world.z.toFixed(2)}`
    : picking
      ? "Кликните по модели"
      : "Нет точки";

  return (
    <div className="mb-3 rounded-md border border-[var(--eds-border)] p-2" data-testid={`odessa-cal-point-${point.id}`}>
      <div className="mb-2 flex items-center justify-between gap-2">
        <strong>Точка {point.label}</strong>
        <Button size="sm" variant={picking ? "primary" : "ghost"} className="min-h-11" onClick={onAdd}>
          {picking ? "Кликните модель…" : "Добавить точку"}
        </Button>
      </div>
      <p className="mb-2 font-mono text-[11px] opacity-80">World: {world}</p>
      <div className="grid grid-cols-2 gap-2">
        <FormField label="Latitude" htmlFor={`cal-lat-${point.id}`}>
          <Input
            id={`cal-lat-${point.id}`}
            sizeVariant="sm"
            inputMode="decimal"
            value={point.latText}
            onChange={(e) => onLatLon(e.target.value, point.lonText)}
            placeholder="46.4825"
          />
        </FormField>
        <FormField label="Longitude" htmlFor={`cal-lon-${point.id}`}>
          <Input
            id={`cal-lon-${point.id}`}
            sizeVariant="sm"
            inputMode="decimal"
            value={point.lonText}
            onChange={(e) => onLatLon(point.latText, e.target.value)}
            placeholder="30.7233"
          />
        </FormField>
      </div>
      {gpsError ? (
        <p className="mt-1 text-[11px] text-[var(--eds-danger)]" role="alert">
          {gpsError}
        </p>
      ) : null}
      <div className="mt-2 flex flex-wrap gap-2">
        <Button size="sm" variant="ghost" className="min-h-11" onClick={onApplyGps} data-testid={`odessa-cal-apply-gps-${point.id}`}>
          Применить GPS
        </Button>
        <Button size="sm" variant="ghost" className="min-h-11" onClick={onCopy} data-testid={`odessa-cal-copy-${point.id}`}>
          Копировать данные
        </Button>
        <Button size="sm" variant="ghost" className="min-h-11" onClick={onClear} data-testid={`odessa-cal-clear-${point.id}`}>
          Удалить точку
        </Button>
      </div>
    </div>
  );
}

export function CalibrationPanel({
  open,
  draft,
  pickingSlot,
  georeferenceStatus,
  modelMismatch,
  message,
  onClose,
  onAddPoint,
  onDraftChange,
  onSave,
  onReset,
  onExport,
  onImportText,
  onCopyPoint,
  onCameraPreset,
  onSavePoor,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [resetOpen, setResetOpen] = useState(false);
  const [poorOpen, setPoorOpen] = useState(false);
  const [gpsErrors, setGpsErrors] = useState<Partial<Record<CalibrationSlotId, string | null>>>({});
  const evaluation = useMemo(() => evaluateCalibrationDraft(draft), [draft]);

  if (!open) return null;

  const applyGps = (slot: CalibrationSlotId) => {
    const point = draft[slot];
    const others = CALIBRATION_SLOTS.filter((id) => id !== slot).map((id) => draft[id].geo);
    const result = applyGpsToSlot(point.latText, point.lonText, others);
    if (!result.ok) {
      setGpsErrors((prev) => ({ ...prev, [slot]: result.error }));
      return;
    }
    setGpsErrors((prev) => ({ ...prev, [slot]: result.warning ?? null }));
    onDraftChange({
      ...draft,
      [slot]: { ...point, geo: result.geo, latText: String(result.geo.lat), lonText: String(result.geo.lon) },
    });
  };

  const axis =
    evaluation.final?.calibration?.axisMapping ?? evaluation.provisional?.calibration?.axisMapping ?? null;

  return (
    <div className="ec-3d-calibration-panel pointer-events-auto" data-testid="odessa-calibration-panel">
      <Card
        className="max-h-[calc(100%-0.5rem)] overflow-auto text-sm"
        title="Калибровка геопривязки"
        actions={
          <Button size="sm" variant="ghost" className="min-h-11" onClick={onClose}>
            Закрыть
          </Button>
        }
      >
        <div className="mb-2 flex flex-wrap gap-2">
          <Badge tone={modelMismatch ? "warning" : georeferenceStatus === "READY_CALIBRATED" ? "success" : "info"}>
            {modelMismatch ? "CALIBRATION_MODEL_MISMATCH" : georeferenceStatus}
          </Badge>
          {evaluation.provisionalStatus === "PROVISIONAL" ? <Badge tone="warning">PROVISIONAL</Badge> : null}
        </div>
        {modelMismatch ? (
          <p className="mb-2 text-[var(--eds-warning)]">
            Модель изменилась. Не используйте сохранённую калибровку без проверки точек A/B/C.
          </p>
        ) : null}
        {message ? <p className="mb-2 text-[var(--eds-text-muted)]">{message}</p> : null}

        {CALIBRATION_SLOTS.map((id) => (
          <PointCard
            key={id}
            point={draft[id]}
            picking={pickingSlot === id}
            gpsError={gpsErrors[id]}
            onAdd={() => onAddPoint(id)}
            onLatLon={(latText, lonText) => onDraftChange({ ...draft, [id]: { ...draft[id], latText, lonText } })}
            onApplyGps={() => applyGps(id)}
            onCopy={() => {
              const text = copyCalibrationDebugData(draft[id]);
              if (navigator.clipboard?.writeText) void navigator.clipboard.writeText(text);
              onCopyPoint(id);
            }}
            onClear={() => onDraftChange(clearCalibrationSlot(draft, id))}
          />
        ))}

        <details className="mb-3 text-xs" open data-testid="odessa-cal-distances">
          <summary className="cursor-pointer opacity-70">Точки · расстояния</summary>
          <p className="mt-1">A↔B: {fmt(evaluation.distances.ab)} m</p>
          <p>A↔C: {fmt(evaluation.distances.ac)} m</p>
          <p>B↔C: {fmt(evaluation.distances.bc)} m</p>
          {evaluation.distances.shortPairs.length ? (
            <p className="text-[var(--eds-warning)]">
              Рекомендуется &gt; {evaluation.distances.recommendedM} m: {evaluation.distances.shortPairs.join(", ")}
            </p>
          ) : null}
          <Button size="sm" variant="ghost" className="mt-2 min-h-11" onClick={() => onDraftChange(emptyCalibrationDraft())}>
            Очистить
          </Button>
        </details>

        <details className="mb-3 text-xs" open data-testid="odessa-cal-solver">
          <summary className="cursor-pointer opacity-70">Решение / ошибка</summary>
          <p className="mt-1">2 точки: {evaluation.provisionalStatus}</p>
          <p>WORLD EAST: {axis?.east ?? "—"}</p>
          <p>WORLD NORTH: {axis?.north ?? "—"}</p>
          <p>YAW: {fmt(evaluation.final?.rotation ?? evaluation.provisional?.rotation, 4)} rad</p>
          <p>SCALE: {fmt(evaluation.final?.scale ?? evaluation.provisional?.scale, 4)}</p>
          <p>TRANSLATION: {evaluation.final?.worldOrigin
            ? `${fmt(evaluation.final.worldOrigin.x)} ${fmt(evaluation.final.worldOrigin.y)} ${fmt(evaluation.final.worldOrigin.z)}`
            : "—"}</p>
          <p>RESIDUAL mean {fmt(evaluation.final?.meanErrorMeters)} m · max {fmt(evaluation.final?.maxErrorMeters)} m</p>
          {(evaluation.final?.pointErrors ?? []).map((e) => (
            <p key={e.id}>
              {e.id} error: {fmt(e.errorMeters)} m
            </p>
          ))}
          <p>Качество: {evaluation.final?.quality ?? "—"}</p>
        </details>

        <p className="mb-1 text-xs opacity-70">Камера калибровки (временно)</p>
        <div className="mb-3 flex flex-wrap gap-2">
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => onCameraPreset("top")}>
            Сверху
          </Button>
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => onCameraPreset("tilt45")}>
            Наклон 45°
          </Button>
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => onCameraPreset("A")}>
            К точке A
          </Button>
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => onCameraPreset("B")}>
            К точке B
          </Button>
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => onCameraPreset("C")}>
            К точке C
          </Button>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button size="sm" className="min-h-11" disabled={!evaluation.canSave} onClick={onSave} data-testid="odessa-cal-save">
            Сохранить геопривязку
          </Button>
          {evaluation.canSavePoor ? (
            <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setPoorOpen(true)} data-testid="odessa-cal-save-poor">
              Сохранить POOR
            </Button>
          ) : null}
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setResetOpen(true)} data-testid="odessa-cal-reset">
            Сбросить калибровку
          </Button>
          <Button size="sm" variant="ghost" className="min-h-11" onClick={onExport} data-testid="odessa-cal-export">
            Экспорт JSON
          </Button>
          <Button size="sm" variant="ghost" className="min-h-11" onClick={() => fileRef.current?.click()} data-testid="odessa-cal-import">
            Импорт JSON
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = "";
              if (!file) return;
              void file.text().then(onImportText);
            }}
          />
        </div>
      </Card>

      <Modal open={poorOpen} title="Калибровка POOR" onClose={() => setPoorOpen(false)}>
        <p className="mb-3">Ошибка &gt; 15 m. Production READY не будет включён без этого подтверждения.</p>
        <div className="flex gap-2">
          <Button variant="ghost" className="min-h-11" onClick={() => setPoorOpen(false)}>
            Отмена
          </Button>
          <Button
            className="min-h-11"
            onClick={() => {
              setPoorOpen(false);
              onSavePoor?.();
            }}
            data-testid="odessa-cal-save-poor-confirm"
          >
            Подтвердить POOR
          </Button>
        </div>
      </Modal>
      <Modal open={resetOpen} title="Сбросить калибровку?" onClose={() => setResetOpen(false)}>
        <p className="mb-3">
          Будет удалена только сохранённая геопривязка. Модель города, CRM, 2D-карта и объекты Enterprise не изменятся.
        </p>
        <div className="flex gap-2">
          <Button variant="ghost" className="min-h-11" onClick={() => setResetOpen(false)}>
            Отмена
          </Button>
          <Button
            className="min-h-11"
            onClick={() => {
              setResetOpen(false);
              onReset();
            }}
            data-testid="odessa-cal-reset-confirm"
          >
            Сбросить калибровку
          </Button>
        </div>
      </Modal>
    </div>
  );
}
