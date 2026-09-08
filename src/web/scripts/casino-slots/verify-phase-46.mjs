import { chromium } from "playwright";
import { existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MACHINES = [
  "olympus-crown",
  "candy-fortune",
  "pharaohs-book",
  "big-catch",
  "buffalo-fortune",
  "lady-emerald",
];

const OUT = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../artifacts/casino");
const BASE = process.env.PHASE46_URL || "http://127.0.0.1:5188";

function findChromium() {
  const candidates = [
    process.env.PLAYWRIGHT_CHROMIUM_PATH,
    resolve(
      process.env.HOME || "",
      "Library/Caches/ms-playwright/chromium-1148/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    ),
  ].filter(Boolean);
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  return undefined;
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const executablePath = findChromium();
  const browser = await chromium.launch({
    executablePath,
    headless: true,
  });
  const failures = [];

  async function shot(page, name) {
    const path = resolve(OUT, name);
    await page.screenshot({ path, fullPage: false });
    return path;
  }

  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.setDefaultTimeout(20000);

  await page.goto(`${BASE}/casino/slots`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("[data-testid='slots-room']");
  const hallScroll = await page.evaluate(
    () => document.documentElement.scrollHeight - document.documentElement.clientHeight,
  );
  if (hallScroll > 2) failures.push(`hall vertical scroll ${hallScroll}px`);
  await shot(page, "phase46-hall.png");

  for (const id of MACHINES) {
    await page.goto(`${BASE}/casino/slots/${id}`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("[data-testid='seated-cabinet']");
    await page.waitForTimeout(700);

    const metrics = await page.evaluate(() => {
      const root = document.documentElement;
      const cabinet = document.querySelector("[data-testid='seated-cabinet']");
      const screenEl = document.querySelector("[data-testid='slot-preview-seated']");
      const reels = document.querySelector("[data-testid='slot-reels']");
      const hud = document.querySelector(".op-seated-hud");
      const webPanel = document.querySelector("[data-testid='slot-web-panel']");
      const cr = cabinet?.getBoundingClientRect();
      const sr = screenEl?.getBoundingClientRect();
      const rr = reels?.getBoundingClientRect();
      return {
        scroll: root.scrollHeight - root.clientHeight,
        cabW: cr?.width || 0,
        cabH: cr?.height || 0,
        screenW: sr?.width || 0,
        screenH: sr?.height || 0,
        reelOverflow:
          rr && sr
            ? rr.left < sr.left - 1 ||
              rr.top < sr.top - 1 ||
              rr.right > sr.right + 1 ||
              rr.bottom > sr.bottom + 1
            : true,
        hudHasGameplay: /SPIN|AUTO|HISTORY|Balance/.test(hud?.textContent || ""),
        webPanel: Boolean(webPanel),
        identity: document.querySelector("[data-testid='slot-game-screen']")?.getAttribute("data-machine"),
        armchair: Boolean(document.querySelector("[data-testid='seated-armchair']")),
        ashtray: Boolean(document.querySelector("[data-testid='seated-ashtray']")),
      };
    });

    if (metrics.scroll > 2) failures.push(`${id} vertical scroll ${metrics.scroll}px`);
    if (metrics.cabH < 900) failures.push(`${id} cabinet too short ${metrics.cabH.toFixed(0)}px`);
    if (metrics.cabW < 620) failures.push(`${id} cabinet too narrow ${metrics.cabW.toFixed(0)}px`);
    if (metrics.screenH < 280) failures.push(`${id} screen too small ${metrics.screenH.toFixed(0)}px`);
    if (metrics.reelOverflow) failures.push(`${id} reel overflow`);
    if (metrics.hudHasGameplay) failures.push(`${id} HUD still has gameplay chrome`);
    if (metrics.webPanel) failures.push(`${id} detached web panel`);
    if (metrics.identity !== id) failures.push(`${id} identity mismatch`);
    if (!metrics.armchair || !metrics.ashtray) failures.push(`${id} missing seated atmosphere`);

    await shot(page, `phase46-${id}-seated.png`);
  }

  await page.goto(`${BASE}/casino/slots/olympus-crown`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("[data-testid='slot-spin']");
  await page.waitForTimeout(500);
  for (const n of [10, 25, 50, 100]) {
    await page.click(`[data-testid='slot-bet-${n}']`);
    const bet = await page.textContent("[data-testid='slot-demo-bet']");
    if (bet?.trim() !== String(n)) failures.push(`BET ${n} display ${bet}`);
  }
  await page.click("[data-testid='slot-bet-25']");
  const before = Number(await page.textContent("[data-testid='slot-demo-balance']"));
  await page.click("[data-testid='slot-spin']");
  const spinning = await page.getAttribute("[data-testid='slot-spin']", "disabled");
  if (spinning === null) failures.push("SPIN did not lock");
  const afterBet = Number(await page.textContent("[data-testid='slot-demo-balance']"));
  if (afterBet !== before - 25) failures.push(`balance did not use bet 25 (${before} -> ${afterBet})`);
  await page.waitForTimeout(1400);
  await shot(page, "phase46-olympus-spin.png");
  await page.click("[data-testid='slot-history-toggle']");
  if (!(await page.$("[data-testid='slot-history']"))) failures.push("HISTORY did not open");
  await page.click("[data-testid='slot-auto']");
  const autoOn = await page.getAttribute("[data-testid='slot-auto']", "class");
  if (!autoOn?.includes("is-on")) failures.push("AUTO did not toggle");
  await page.click("[data-testid='slot-auto']");
  await page.click("[data-testid='slot-back-room']");
  await page.waitForSelector("[data-testid='slots-room']", { timeout: 8000 });

  page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${BASE}/casino/slots/lady-emerald`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("[data-testid='seated-cabinet']");
  await page.waitForTimeout(400);
  await shot(page, "phase46-emerald-1440.png");

  page.setViewportSize({ width: 1366, height: 768 });
  await page.goto(`${BASE}/casino/slots/pharaohs-book`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector("[data-testid='seated-cabinet']");
  await page.waitForTimeout(400);
  await shot(page, "phase46-pharaohs-1366.png");

  await browser.close();
  if (failures.length) {
    console.error("PHASE46_VISUAL_FAIL");
    for (const item of failures) console.error(`- ${item}`);
    process.exit(1);
  }
  console.log("PHASE46_VISUAL_PASS");
  console.log(`OUT=${OUT}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
