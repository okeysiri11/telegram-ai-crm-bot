import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, devices } from "@playwright/test";

const webDir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(webDir, "../..");
const venvPython = path.join(root, ".venv", "bin", "python");
const python = process.env.PYTHON || (existsSync(venvPython) ? venvPython : "python3");
const apiScript = path.join(root, "scripts", "run_vanguard_e2e_api.py");
const chromeChannel =
  process.env.PLAYWRIGHT_CHANNEL === "chrome" || process.env.PLAYWRIGHT_CHANNEL === "msedge"
    ? process.env.PLAYWRIGHT_CHANNEL
    : undefined;

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5180",
    trace: "retain-on-failure",
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
  webServer: [
    {
      command: `${JSON.stringify(python)} ${JSON.stringify(apiScript)}`,
      url: "http://127.0.0.1:8080/api/vanguard-site/v1/health",
      reuseExistingServer: true,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5180",
      url: "http://127.0.0.1:5180/vanguard",
      reuseExistingServer: true,
      timeout: 90_000,
    },
  ],
});
