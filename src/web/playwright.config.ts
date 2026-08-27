import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const webDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(webDir, "../..");
const venvPython = path.join(root, ".venv", "bin", "python");
const python = process.env.PYTHON || (existsSync(venvPython) ? venvPython : "python3");
const stackScript = path.join(root, "scripts/run_vanguard_e2e_stack.sh");
const chromeChannel =
  process.env.PLAYWRIGHT_CHANNEL === "chrome" || process.env.PLAYWRIGHT_CHANNEL === "msedge"
    ? process.env.PLAYWRIGHT_CHANNEL
    : undefined;
const inCi = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  fullyParallel: false,
  retries: inCi ? 1 : 0,
  reporter: inCi ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5180",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        ...(chromeChannel ? { channel: chromeChannel } : {}),
      },
    },
  ],
  webServer: {
    command: `env PYTHON=${JSON.stringify(python)} bash ${JSON.stringify(stackScript)}`,
    url: "http://127.0.0.1:5180/vanguard",
    reuseExistingServer: !inCi,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
