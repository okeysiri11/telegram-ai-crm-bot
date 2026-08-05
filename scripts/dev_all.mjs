#!/usr/bin/env node
/**
 * Sprint 32.6A — one-command local launch orchestrator.
 * Starts: optional Docker infra → API (:8080) → Enterprise Web (:5180)
 * Works without Docker when local Postgres is available; Redis optional.
 */

import { spawn, execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { createConnection } from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const children = [];

function log(msg) {
  console.log(`[dev:all] ${msg}`);
}

async function portOpen(port, host = "127.0.0.1", timeoutMs = 400) {
  return new Promise((resolve) => {
    const sock = createConnection({ port, host });
    const done = (ok) => {
      try {
        sock.destroy();
      } catch {
        /* ignore */
      }
      resolve(ok);
    };
    sock.setTimeout(timeoutMs);
    sock.once("connect", () => done(true));
    sock.once("timeout", () => done(false));
    sock.once("error", () => done(false));
  });
}

function spawnProc(label, command, args, opts = {}) {
  log(`start ${label}: ${command} ${args.join(" ")}`);
  const child = spawn(command, args, {
    cwd: opts.cwd || ROOT,
    env: { ...process.env, ...opts.env },
    stdio: ["ignore", "pipe", "pipe"],
    shell: opts.shell ?? false,
  });
  children.push({ label, child });
  const prefix = (buf) => {
    const text = buf.toString();
    for (const line of text.split(/\r?\n/).filter(Boolean)) {
      console.log(`[${label}] ${line}`);
    }
  };
  child.stdout?.on("data", prefix);
  child.stderr?.on("data", prefix);
  child.on("exit", (code, signal) => {
    log(`${label} exited code=${code} signal=${signal || ""}`);
  });
  return child;
}

function pythonBin() {
  const venv = path.join(ROOT, "venv", "bin", "python");
  const venv3 = path.join(ROOT, ".venv", "bin", "python");
  if (existsSync(venv)) return venv;
  if (existsSync(venv3)) return venv3;
  return process.platform === "win32" ? "python" : "python3";
}

function hasDocker() {
  try {
    execSync("docker info", { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

async function ensureInfra() {
  const pgUp = await portOpen(5432);
  const redisUp = await portOpen(6379);
  log(`postgres :5432 ${pgUp ? "up" : "down"} · redis :6379 ${redisUp ? "up" : "down"}`);

  if (hasDocker()) {
    log("Docker available — starting postgres+redis via docker compose");
    try {
      execSync("docker compose up -d postgres redis", { cwd: ROOT, stdio: "inherit" });
      for (let i = 0; i < 30; i++) {
        if ((await portOpen(5432)) && (await portOpen(6379))) break;
        await new Promise((r) => setTimeout(r, 500));
      }
      return { docker: true, postgres: await portOpen(5432), redis: await portOpen(6379) };
    } catch (e) {
      log(`docker compose failed: ${e.message || e}`);
    }
  } else {
    log("Docker unavailable — using local services (Postgres recommended; Redis optional)");
  }

  if (!pgUp) {
    log("WARNING: PostgreSQL not reachable on :5432 — API health may degrade; demo auth still works");
  }
  if (!redisUp) {
    log("WARNING: Redis not reachable — REDIS_REQUIRED=false for local");
    process.env.REDIS_REQUIRED = "false";
  }
  return { docker: false, postgres: pgUp, redis: redisUp };
}

async function waitForHttp(url, attempts = 60) {
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status === 503) return true;
    } catch {
      /* retry */
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

function shutdown() {
  log("shutting down…");
  for (const { child } of children) {
    try {
      child.kill("SIGTERM");
    } catch {
      /* ignore */
    }
  }
  setTimeout(() => process.exit(0), 800);
}

async function main() {
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);

  const infra = await ensureInfra();
  const py = pythonBin();
  const apiScript = path.join(ROOT, "scripts", "run_api_local.py");
  const webDir = path.join(ROOT, "src", "web");

  if (!existsSync(path.join(webDir, "node_modules"))) {
    log("installing src/web dependencies…");
    execSync("npm install", { cwd: webDir, stdio: "inherit" });
  }

  spawnProc("api", py, [apiScript], {
    env: {
      ENVIRONMENT: process.env.ENVIRONMENT || "development",
      REDIS_REQUIRED: process.env.REDIS_REQUIRED || "false",
      API_HOST: process.env.API_HOST || "127.0.0.1",
      API_PORT: process.env.API_PORT || "8080",
    },
  });

  const apiOk =
    (await waitForHttp("http://127.0.0.1:8080/liveness")) ||
    (await waitForHttp("http://127.0.0.1:8080/health"));
  if (!apiOk) {
    log("WARNING: API not ready — Vite demo auth + local plugins still work");
  } else {
    log("API reachable on :8080 (liveness/health)");
  }

  spawnProc("web", "npm", ["run", "dev", "--", "--host", "127.0.0.1", "--port", "5180"], {
    cwd: webDir,
    shell: true,
    env: {
      VITE_DEMO_AUTH: process.env.VITE_DEMO_AUTH || "true",
      VITE_API_PROXY: process.env.VITE_API_PROXY || "http://127.0.0.1:8080",
    },
  });

  log("────────────────────────────────────────────");
  log("Open http://127.0.0.1:5180/login");
  log("Demo: owner@demo.corp / demo  (tenant demo-corp)");
  log("Owner: http://127.0.0.1:5180/owner");
  log("City:  http://127.0.0.1:5180/city");
  log("AI:    http://127.0.0.1:5180/platform-builder/runtime");
  log("API:   http://127.0.0.1:8080/health");
  log(`Infra: docker=${infra.docker} postgres=${infra.postgres} redis=${infra.redis}`);
  log("────────────────────────────────────────────");
}

main().catch((err) => {
  console.error(err);
  shutdown();
  process.exit(1);
});
