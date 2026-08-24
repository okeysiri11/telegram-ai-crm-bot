/**
 * Owner-facing 4-step georeference wizard. Technical panel stays behind cityDebug.
 * Does not invent GPS or identify landmarks.
 */

import { useMemo, useState } from "react";
import { Badge, Button, Card, FormField, Input, Modal } from "@/ui";
import type { CalibrationSlotId, GeoreferenceStatus } from "./types";
import {
  applyGpsPasteToSlot,
  CALIBRATION_SLOTS,
  completeControlPoints,
  evaluateCalibrationDraft,
  evaluateCheckPoint,
  type CalibrationDraft,
  type CheckDraft,
  type CheckEvaluation,
} from "./calibrationSession";
import { applyPasteToGpsFields, odessaMapHelperUrl } from "./gpsValidation";
import {
  IDENTITY_MODEL_ROOT,
  PICK_COORDINATE_SPACE,
  SCALE_CONVENTION,
  leaveOneOut,
  pairScaleRows,
  type ModelRootTransform,
} from "./calibrationDiagnostics";

export type WizardStep = 1 | 2 | 3 | 4;

type Props = {
  open: boolean;
  draft: CalibrationDraft;
  check: CheckDraft;
  pickingSlot: CalibrationSlotId | "CHECK" | null;
  georeferenceStatus: GeoreferenceStatus | string;
  modelMismatch: boolean;
  message?: string | null;
  savedReady?: boolean;
  cursorWorld?: { x: number; y: number; z: number } | null;
  onClose: () => void;
  onPick: (slot: CalibrationSlotId | "CHECK") => void;
  onDraftChange: (next: CalibrationDraft) => void;
  onCheckChange: (next: CheckDraft) => void;
  onSave: () => void;
  onReset: () => void;
  onCopyDiagnostic?: () => void;
  onExportJson?: () => void;
  modelRoot?: ModelRootTransform;
  pickCoordinateSpace?: string;
};

const SLOT_BY_STEP: Record<1 | 2 | 3, CalibrationSlotId> = { 1: "A", 2: "B", 3: "C" };

function fmt(n: number | null | undefined, digits = 2): string {
  return n == null || !Number.isFinite(n) ? "—" : n.toFixed(digits);
}

function openMapHelper() {
  window.open(odessaMapHelperUrl(), "_blank", "noopener,noreferrer");
}

export function CalibrationWizard({
  open,
  draft,
  check,
  pickingSlot,
  georeferenceStatus,
  modelMismatch,
  message,
  savedReady = false,
  cursorWorld = null,
  onClose,
  onPick,
  onDraftChange,
  onCheckChange,
  onSave,
  onReset,
  onCopyDiagnostic,
  onExportJson,
  modelRoot = IDENTITY_MODEL_ROOT,
  pickCoordinateSpace = PICK_COORDINATE_SPACE,
}: Props) {
  const [step, setStep] = useState<WizardStep>(1);
  const [gpsError, setGpsError] = useState<string | null>(null);
  const [resetOpen, setResetOpen] = useState(false);
  const [previewed, setPreviewed] = useState(false);
  const evaluation = useMemo(() => evaluateCalibrationDraft(draft), [draft]);
  const checkEval = useMemo<CheckEvaluation>(() => evaluateCheckPoint(check, evaluation.final), [check, evaluation.final]);
  const horizVals = (evaluation.final?.pointErrors ?? []).map((e) => e.horizontalErrorMeters ?? e.errorMeters);
  const horizRms =
    horizVals.length > 0 ? Math.sqrt(horizVals.reduce((s, n) => s + n * n, 0) / horizVals.length) : null;
  const d3Vals = (evaluation.final?.pointErrors ?? []).map((e) => e.error3dMeters).filter((n): n is number => n != null);
  const d3Rms = d3Vals.length > 0 ? Math.sqrt(d3Vals.reduce((s, n) => s + n * n, 0) / d3Vals.length) : evaluation.final?.meanErrorMeters3d;
  const forensics = useMemo(() => {
    const points = completeControlPoints(draft);
    if (points.length < 3) return null;
    const pairs = pairScaleRows(points);
    const loo = leaveOneOut(points);
    return { pairs, loo };
  }, [draft]);

  if (!open) return null;

  const slot = step === 1 || step === 2 || step === 3 ? SLOT_BY_STEP[step] : null;
  const point = slot ? draft[slot] : null;
  const stepReady =
    step === 4 ? evaluation.complete.length === 3 : !!(point?.world && point.geo);

  const applyGps = (target: CalibrationSlotId | "CHECK") => {
    if (target === "CHECK") {
      const others = CALIBRATION_SLOTS.map((id) => draft[id].geo);
      const result = applyGpsPasteToSlot(check.latText, check.lonText, others);
      if (!result.ok) {
        setGpsError(result.error);
        return;
      }
      setGpsError(null);
      onCheckChange({
        ...check,
        geo: result.geo,
        latText: String(result.geo.lat),
        lonText: String(result.geo.lon),
      });
      return;
    }
    const others = CALIBRATION_SLOTS.filter((id) => id !== target).map((id) => draft[id].geo);
    const result = applyGpsPasteToSlot(draft[target].latText, draft[target].lonText, others);
    if (!result.ok) {
      setGpsError(result.error);
      return;
    }
    setGpsError(null);
    onDraftChange({
      ...draft,
      [target]: {
        ...draft[target],
        geo: result.geo,
        latText: String(result.geo.lat),
        lonText: String(result.geo.lon),
      },
    });
  };

  return (
    <div className="ec-3d-calibration-panel pointer-events-auto" data-testid="odessa-cal-wizard">
      <Card
        className="max-h-[calc(100%-0.5rem)] overflow-auto text-sm"
        title={`Геопривязка · шаг ${step}/4`}
        actions={
          <Button size="sm" variant="ghost" className="min-h-11" onClick={onClose}>
            Закрыть
          </Button>
        }
      >
        <div className="mb-2 flex flex-wrap gap-2">
          <Badge tone={savedReady ? "success" : "info"}>{georeferenceStatus}</Badge>
          {modelMismatch ? <Badge tone="warning">CALIBRATION_MODEL_MISMATCH</Badge> : null}
        </div>
        {savedReady ? (
          <p className="mb-2 text-[var(--eds-success)]" data-testid="odessa-cal-saved-banner">
            ГЕОПРИВЯЗКА СОХРАНЕНА
          </p>
        ) : null}
        {message ? <p className="mb-2 text-[var(--eds-text-muted)]">{message}</p> : null}

        <p className="mb-2 text-xs leading-snug opacity-80">
          Выбирайте хорошо узнаваемые точки, расположенные далеко друг от друга: угол крупного
          здания, конец пирса, пересечение крупных дорог, характерный угол квартала, чёткая точка
          береговой инфраструктуры. Не берите центр моря, случайную землю, деревья и мелкие
          неизвестные объекты.
        </p>

        {step < 4 && point ? (
          <div data-testid={`odessa-wizard-step-${step}`}>
            <p className="mb-2 font-medium">
              {pickingSlot === slot ? "GEO PICK: кликните точку на модели" : `Выберите точку ${slot}`}
            </p>
            <Button
              size="sm"
              className="mb-3 min-h-11"
              variant={pickingSlot === slot ? "primary" : "ghost"}
              onClick={() => onPick(slot!)}
              data-testid="odessa-wizard-pick"
            >
              {pickingSlot === slot ? "Кликните модель…" : `Выбрать точку ${slot}`}
            </Button>
            {point.world ? (
              <dl className="mb-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-mono text-[11px]" data-testid="odessa-wizard-world">
                <dt>World X</dt>
                <dd>{point.world.x.toFixed(3)}</dd>
                <dt>World Y</dt>
                <dd>{point.world.y.toFixed(3)}</dd>
                <dt>World Z</dt>
                <dd>{point.world.z.toFixed(3)}</dd>
              </dl>
            ) : (
              <p className="mb-3 text-xs opacity-70">Точка — intersection.point клика, не центр здания.</p>
            )}
            {step === 1 && point.world && cursorWorld ? (
              <p className="mb-2 text-xs" data-testid="odessa-wizard-cursor-dist">
                До курсора: {fmt(Math.hypot(point.world.x - cursorWorld.x, point.world.z - cursorWorld.z))} m
              </p>
            ) : null}
            {step === 2 && draft.A.world && cursorWorld && !point.world ? (
              <p className="mb-2 text-xs" data-testid="odessa-wizard-cursor-dist">
                A → курсор: {fmt(Math.hypot(draft.A.world.x - cursorWorld.x, draft.A.world.z - cursorWorld.z))} m
              </p>
            ) : null}
            {step === 2 && evaluation.worldDistances.ab != null ? (
              <p className="mb-2 text-xs">A–B (модель): {fmt(evaluation.worldDistances.ab)} m</p>
            ) : null}
            {step === 3 ? (
              <p className="mb-2 text-xs">
                A–B {fmt(evaluation.worldDistances.ab)} · A–C {fmt(evaluation.worldDistances.ac)} · B–C{" "}
                {fmt(evaluation.worldDistances.bc)}
              </p>
            ) : null}

            <div className="grid grid-cols-2 gap-2">
              <FormField label="Широта" htmlFor={`wiz-lat-${slot}`}>
                <Input
                  id={`wiz-lat-${slot}`}
                  sizeVariant="sm"
                  inputMode="decimal"
                  value={point.latText}
                  placeholder="46.xxxxxx"
                  onChange={(e) => {
                    const split = applyPasteToGpsFields(e.target.value, point.lonText);
                    onDraftChange({ ...draft, [slot!]: { ...point, latText: split.latText, lonText: split.lonText } });
                  }}
                />
              </FormField>
              <FormField label="Долгота" htmlFor={`wiz-lon-${slot}`}>
                <Input
                  id={`wiz-lon-${slot}`}
                  sizeVariant="sm"
                  inputMode="decimal"
                  value={point.lonText}
                  placeholder="30.xxxxxx"
                  onChange={(e) => {
                    const split = applyPasteToGpsFields(point.latText, e.target.value);
                    onDraftChange({ ...draft, [slot!]: { ...point, latText: split.latText, lonText: split.lonText } });
                  }}
                />
              </FormField>
            </div>
            <p className="mt-1 text-[11px] opacity-60">Placeholder — не координата этой точки. Можно вставить «46.48, 30.72».</p>
            {gpsError ? (
              <p className="mt-1 text-[11px] text-[var(--eds-danger)]" role="alert">
                {gpsError}
              </p>
            ) : null}
            <div className="mt-2 flex flex-wrap gap-2">
              <Button size="sm" className="min-h-11" onClick={() => applyGps(slot!)} data-testid="odessa-wizard-apply-gps">
                Применить GPS
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={openMapHelper} data-testid="odessa-wizard-find-coords">
                Найти координаты
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={openMapHelper} data-testid="odessa-wizard-map-2d">
                Указать эту точку на 2D
              </Button>
            </div>
            <p className="mt-2 text-[11px] opacity-70">
              2D-карта Enterprise City не в WGS84. «Найти координаты» открывает карту Одессы — скопируйте GPS
              того же места и вставьте сюда.
            </p>
          </div>
        ) : null}

        {step === 4 ? (
          <div data-testid="odessa-wizard-preview">
            <p className="mb-2 font-medium">Проверка и сохранение</p>
            {evaluation.collinear ? (
              <p className="mb-2 text-[var(--eds-warning)]" data-testid="odessa-cal-collinear">
                Контрольные точки расположены слишком линейно. Точность геопривязки может быть низкой.
              </p>
            ) : null}
            <p className="mb-1 text-xs">
              A–B {fmt(evaluation.worldDistances.ab)} · A–C {fmt(evaluation.worldDistances.ac)} · B–C{" "}
              {fmt(evaluation.worldDistances.bc)}
            </p>
            <p className="mb-2 text-xs">Площадь треугольника: {fmt(evaluation.triangleArea)} м²</p>
            <div className="mb-3 rounded-md border border-[var(--eds-border)] p-2 font-mono text-[11px]" data-testid="odessa-raw-points">
              {(["A", "B", "C"] as const).map((id) => (
                <div key={id} className="mb-2">
                  <p className="font-sans font-medium">POINT {id}</p>
                  <p>WORLD X: {draft[id].world ? draft[id].world.x.toFixed(3) : "—"}</p>
                  <p>WORLD Y: {draft[id].world ? draft[id].world.y.toFixed(3) : "—"}</p>
                  <p>WORLD Z: {draft[id].world ? draft[id].world.z.toFixed(3) : "—"}</p>
                  <p>GPS LAT: {draft[id].geo ? draft[id].geo.lat.toFixed(6) : "—"}</p>
                  <p>GPS LON: {draft[id].geo ? draft[id].geo.lon.toFixed(6) : "—"}</p>
                </div>
              ))}
              <p className="font-sans font-medium">CHECK</p>
              <p>WORLD X: {check.world ? check.world.x.toFixed(3) : "—"}</p>
              <p>WORLD Y: {check.world ? check.world.y.toFixed(3) : "—"}</p>
              <p>WORLD Z: {check.world ? check.world.z.toFixed(3) : "—"}</p>
              <p>ACTUAL GPS: {check.geo ? `${check.geo.lat.toFixed(6)}, ${check.geo.lon.toFixed(6)}` : "—"}</p>
              <p>PREDICTED GPS: {checkEval.predicted ? `${checkEval.predicted.lat.toFixed(6)}, ${checkEval.predicted.lon.toFixed(6)}` : "—"}</p>
            </div>
            <div className="mb-3 rounded-md border border-[var(--eds-border)] p-2 text-xs" data-testid="odessa-solver-preview">
              <p className="mb-1 font-medium">ПРЕДВАРИТЕЛЬНЫЙ РЕЗУЛЬТАТ</p>
              <p>CONTROL HORIZONTAL RMS: {fmt(horizRms)} m</p>
              <p>CONTROL HORIZONTAL MAX: {fmt(evaluation.final?.maxErrorMeters)} m</p>
              <p>CONTROL 3D RMS: {fmt(d3Rms)} m</p>
              <p>CONTROL 3D MAX: {fmt(evaluation.final?.maxErrorMeters3d)} m</p>
              <p>Scale (WORLD_UNITS_PER_METER): {fmt(evaluation.final?.scale ?? evaluation.provisional?.scale, 4)}</p>
              <p>Rotation: {fmt(evaluation.final?.rotation ?? evaluation.provisional?.rotation, 4)}</p>
              <p>Quality (horizontal): {evaluation.final?.quality ?? "—"}</p>
              {forensics
                ? forensics.pairs.map((row) => (
                    <p key={row.pair}>
                      {row.pair}_SCALE: {fmt(row.worldUnitsPerMeter, 4)} ({SCALE_CONVENTION}) · world {fmt(row.worldHorizontalDistance)} · GPS {fmt(row.gpsDistanceM)} m
                    </p>
                  ))
                : null}
              {forensics ? <p>LIKELY_BAD_POINT: {forensics.loo.likelyBadPoint} (not removed)</p> : null}
              <p>PICK_COORDINATE_SPACE: {pickCoordinateSpace}</p>
              <p>
                MODEL_ROOT_POSITION: {modelRoot.position.x.toFixed(3)}, {modelRoot.position.y.toFixed(3)},{" "}
                {modelRoot.position.z.toFixed(3)}
              </p>
              <p>
                MODEL_ROOT_ROTATION: {modelRoot.rotation.x.toFixed(3)}, {modelRoot.rotation.y.toFixed(3)},{" "}
                {modelRoot.rotation.z.toFixed(3)}
              </p>
              <p>
                MODEL_ROOT_SCALE: {modelRoot.scale.x.toFixed(3)}, {modelRoot.scale.y.toFixed(3)},{" "}
                {modelRoot.scale.z.toFixed(3)}
              </p>
              {pickCoordinateSpace !== PICK_COORDINATE_SPACE ? (
                <p className="text-[var(--eds-warning)]">PICK_PIPELINE_WARNING: expected {PICK_COORDINATE_SPACE}</p>
              ) : null}
            </div>

            <p className="mb-1 font-medium">Проверка геопривязки (CHECK)</p>
            <p className="mb-2 text-[11px] opacity-70">
              Четвёртая точка не входит в solver. Кликните узнаваемое место на модели, затем введите GPS
              того же места с карты.
            </p>
            <Button
              size="sm"
              variant={pickingSlot === "CHECK" ? "primary" : "ghost"}
              className="mb-2 min-h-11"
              onClick={() => onPick("CHECK")}
              data-testid="odessa-wizard-pick-check"
            >
              {pickingSlot === "CHECK" ? "Кликните CHECK…" : "Выбрать CHECK"}
            </Button>
            {check.world ? (
              <p className="mb-2 font-mono text-[11px]">
                CHECK world {check.world.x.toFixed(2)}, {check.world.y.toFixed(2)}, {check.world.z.toFixed(2)}
              </p>
            ) : null}
            <div className="grid grid-cols-2 gap-2">
              <FormField label="CHECK широта" htmlFor="wiz-check-lat">
                <Input
                  id="wiz-check-lat"
                  sizeVariant="sm"
                  value={check.latText}
                  placeholder="46.xxxxxx"
                  onChange={(e) => {
                    const split = applyPasteToGpsFields(e.target.value, check.lonText);
                    onCheckChange({ ...check, latText: split.latText, lonText: split.lonText });
                  }}
                />
              </FormField>
              <FormField label="CHECK долгота" htmlFor="wiz-check-lon">
                <Input
                  id="wiz-check-lon"
                  sizeVariant="sm"
                  value={check.lonText}
                  placeholder="30.xxxxxx"
                  onChange={(e) => {
                    const split = applyPasteToGpsFields(check.latText, e.target.value);
                    onCheckChange({ ...check, latText: split.latText, lonText: split.lonText });
                  }}
                />
              </FormField>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <Button size="sm" variant="ghost" className="min-h-11" onClick={() => applyGps("CHECK")}>
                Применить GPS CHECK
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={openMapHelper}>
                Найти координаты
              </Button>
            </div>
            {previewed ? (
              <div className="mt-3 text-xs" data-testid="odessa-check-result">
                <p>CONTROL HORIZONTAL RMS: {fmt(horizRms)} m</p>
                <p>CHECK REAL-WORLD ERROR: {fmt(checkEval.errorMeters)} m</p>
                <p>CHECK EAST: {fmt(checkEval.eastErrorMeters)} m · NORTH: {fmt(checkEval.northErrorMeters)} m</p>
                {checkEval.predicted ? (
                  <p>
                    CHECK predicted GPS: {checkEval.predicted.lat.toFixed(6)}, {checkEval.predicted.lon.toFixed(6)}
                  </p>
                ) : null}
              </div>
            ) : null}

            <div className="mt-3 flex flex-wrap gap-2">
              <Button size="sm" className="min-h-11" onClick={() => setPreviewed(true)} data-testid="odessa-wizard-verify">
                Проверить
              </Button>
              <Button
                size="sm"
                className="min-h-11"
                disabled={!evaluation.canSave}
                onClick={onSave}
                data-testid="odessa-wizard-save"
              >
                Сохранить геопривязку
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setStep(1)}>
                Изменить A
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setStep(2)}>
                Изменить B
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setStep(3)}>
                Изменить C
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setResetOpen(true)} data-testid="odessa-cal-reset">
                Сбросить геопривязку
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={onCopyDiagnostic} data-testid="odessa-copy-geo-diag">
                КОПИРОВАТЬ GEO ДИАГНОСТИКУ
              </Button>
              <Button size="sm" variant="ghost" className="min-h-11" onClick={onExportJson} data-testid="odessa-export-geo-json">
                ЭКСПОРТ GEO JSON
              </Button>
            </div>
          </div>
        ) : null}

        <div className="mt-4 flex flex-wrap gap-2">
          {step > 1 ? (
            <Button size="sm" variant="ghost" className="min-h-11" onClick={() => setStep((s) => (s - 1) as WizardStep)}>
              Назад
            </Button>
          ) : null}
          {step < 4 ? (
            <Button
              size="sm"
              className="min-h-11"
              disabled={!stepReady}
              onClick={() => setStep((s) => (s + 1) as WizardStep)}
              data-testid="odessa-wizard-next"
            >
              Далее
            </Button>
          ) : null}
        </div>
      </Card>

      <Modal open={resetOpen} title="Удалить сохранённую геопривязку?" onClose={() => setResetOpen(false)}>
        <p className="mb-3">Модель города не изменится. Будет удалена калибровка v3 и сырые точки A/B/C.</p>
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
            Сбросить геопривязку
          </Button>
        </div>
      </Modal>
    </div>
  );
}
