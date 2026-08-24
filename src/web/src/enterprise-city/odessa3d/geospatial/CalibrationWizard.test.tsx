import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { CalibrationWizard } from "./CalibrationWizard";
import { draftFromControlPoints, emptyCalibrationDraft, emptyCheckDraft } from "./calibrationSession";
import { geoToWorld, IDENTITY_AXIS_MAPPING } from "./index";
import { ODESSA_ENU_ORIGIN } from "./localMeters";
import type { GeoCalibration } from "./types";

function truth(): GeoCalibration {
  return {
    origin: { ...ODESSA_ENU_ORIGIN },
    worldOrigin: { x: 12, y: 1, z: -8 },
    metersPerWorldUnit: 1,
    rotationRadians: 0.18,
    axisMapping: IDENTITY_AXIS_MAPPING,
    source: "test",
    confidence: "CALIBRATED",
  };
}

const GEO_A = { ...ODESSA_ENU_ORIGIN };
const GEO_B = { lat: ODESSA_ENU_ORIGIN.lat + 0.004, lon: ODESSA_ENU_ORIGIN.lon + 0.005 };
const GEO_C = { lat: ODESSA_ENU_ORIGIN.lat - 0.003, lon: ODESSA_ENU_ORIGIN.lon + 0.003 };

describe("CalibrationWizard", () => {
  it("starts at step 1/4 and enters GEO PICK for A without jumping camera", () => {
    const onPick = vi.fn();
    render(
      <CalibrationWizard
        open
        draft={emptyCalibrationDraft()}
        check={emptyCheckDraft()}
        pickingSlot={null}
        georeferenceStatus="CALIBRATION_REQUIRED"
        modelMismatch={false}
        onClose={() => undefined}
        onPick={onPick}
        onDraftChange={() => undefined}
        onCheckChange={() => undefined}
        onSave={() => undefined}
        onReset={() => undefined}
      />,
    );
    expect(screen.getByTestId("odessa-cal-wizard").textContent).toMatch(/шаг 1\/4/);
    fireEvent.click(screen.getByTestId("odessa-wizard-pick"));
    expect(onPick).toHaveBeenCalledWith("A");
    expect(screen.getByTestId("odessa-wizard-find-coords")).toBeTruthy();
    expect(screen.getByTestId("odessa-wizard-map-2d")).toBeTruthy();
  });

  it("shows solver preview and CHECK after A/B/C are filled", () => {
    const cal = truth();
    const draft = draftFromControlPoints(
      [GEO_A, GEO_B, GEO_C].map((geo, i) => ({
        id: (["A", "B", "C"] as const)[i],
        label: (["A", "B", "C"] as const)[i],
        geo,
        world: geoToWorld(geo, cal),
      })),
    );
    render(
      <CalibrationWizard
        open
        draft={draft}
        check={emptyCheckDraft()}
        pickingSlot={null}
        georeferenceStatus="CALIBRATION_REQUIRED"
        modelMismatch={false}
        onClose={() => undefined}
        onPick={() => undefined}
        onDraftChange={() => undefined}
        onCheckChange={() => undefined}
        onSave={() => undefined}
        onReset={() => undefined}
      />,
    );
    fireEvent.click(screen.getByTestId("odessa-wizard-next"));
    fireEvent.click(screen.getByTestId("odessa-wizard-next"));
    fireEvent.click(screen.getByTestId("odessa-wizard-next"));
    expect(screen.getByTestId("odessa-wizard-preview")).toBeTruthy();
    expect(screen.getByTestId("odessa-solver-preview").textContent).toMatch(/ПРЕДВАРИТЕЛЬНЫЙ РЕЗУЛЬТАТ/);
    fireEvent.click(screen.getByTestId("odessa-wizard-verify"));
    expect(screen.getByTestId("odessa-check-result").textContent).toMatch(/CONTROL HORIZONTAL RMS/);
    expect(screen.getByTestId("odessa-check-result").textContent).toMatch(/CHECK REAL-WORLD ERROR/);
    expect(screen.getByTestId("odessa-raw-points").textContent).toMatch(/POINT A/);
    expect(screen.getByTestId("odessa-copy-geo-diag")).toBeTruthy();
    expect(screen.getByTestId("odessa-export-geo-json")).toBeTruthy();
  });
});
