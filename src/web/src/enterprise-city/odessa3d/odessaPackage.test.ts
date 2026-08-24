import { afterEach, describe, expect, it } from "vitest";
import {
  ODESSA_DEFAULT_PACKAGE,
  ODESSA_PACKAGES,
  activeOdessaPackage,
  readStoredPackageId,
  storePackageId,
} from "./odessaPackage";

describe("STEP 29.9 Odessa package A/B", () => {
  afterEach(() => {
    storePackageId(null);
  });

  it("defaults production to REBUILT_METRIC with no runtime geometry recovery", () => {
    expect(ODESSA_DEFAULT_PACKAGE).toBe("REBUILT_METRIC");
    const pkg = activeOdessaPackage();
    expect(pkg.id).toBe("REBUILT_METRIC");
    expect(pkg.worldUnitsPerMeter).toBe(1);
    expect(pkg.runtimeGeometryRecovery).toBe(false);
    expect(pkg.manifestUrl).toBe("/assets/odessa_metric/odessa_manifest.json");
    expect(pkg.decalYScale).toBe(100);
  });

  it("keeps CURRENT_BROKEN as rollback with the 29.5–29.8 recovery chain", () => {
    const broken = ODESSA_PACKAGES.CURRENT_BROKEN;
    expect(broken.runtimeGeometryRecovery).toBe(true);
    expect(broken.worldUnitsPerMeter).toBe(0.01);
    expect(broken.decalYScale).toBe(1);
    expect(broken.manifestUrl).toBe("/assets/odessa/odessa_manifest.json");
  });

  it("stores and restores the DEV A/B selection without destroying the other package", () => {
    storePackageId("CURRENT_BROKEN");
    expect(readStoredPackageId()).toBe("CURRENT_BROKEN");
    expect(activeOdessaPackage().id).toBe("CURRENT_BROKEN");
    expect(ODESSA_PACKAGES.REBUILT_METRIC.manifestUrl).toContain("odessa_metric");
    storePackageId(null);
    expect(activeOdessaPackage().id).toBe("REBUILT_METRIC");
  });
});
