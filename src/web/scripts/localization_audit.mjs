#!/usr/bin/env node
/**
 * Sprint 42.5 — Localization Audit (critical RU-first surfaces).
 *
 * Usage: node scripts/localization_audit.mjs
 * Exit 1 if critical surfaces have hardcoded English UI (beyond allowlist).
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.resolve(__dirname, "..");

const CRITICAL_DIRS = [
  "platform-builder/concierge",
  "platform-builder/ai-builder",
  "platform-builder/ai-team",
  "platform-builder/framework",
  "src/ai-builder-studio",
];

const CRITICAL_FILES = [
  "src/i18n/platformGlossary.ts",
  "src/i18n/platformGlossary.ru.ts",
  "platform-builder/i18n/builderUiRu.ts",
];

const DICT_BASENAMES = new Set([
  "builderUiRu.ts",
  "platformGlossary.ts",
  "platformGlossary.ru.ts",
]);

const ALLOW_EXACT = new Set([
  "AI",
  "CRM",
  "ERP",
  "API",
  "MCP",
  "JWT",
  "OAuth",
  "OpenAI",
  "Anthropic",
  "Gemini",
  "Telegram",
  "WhatsApp",
  "Email",
  "PDF",
  "Word",
  "Excel",
  "Crypto",
  "Crypto OTC",
  "HR",
  "OKR",
  "SDK",
  "Bidex",
  "Follow-up CRM",
]);

const UI_EN =
  /\b(Create|Preview|Dashboard|Workflow|Summary|Organization|Coming Soon|Cancel|Confirm|Loading|Register|Settings|Help|Purpose|Benefits|Actions|Details|Overview|Configuration|Templates|Components|Schema|Version|Validation|Validate|Failed|Error|Success|Status|Description|Permissions|Search|Filter|Continue|Finish|Skip|Refresh|Working|Ready|Close|Edit|Delete|Remove|Update|Submit|Select|Choose|Start|Stop|Pause|Resume|Assign|Engine|Registry|Intelligence|Orchestration|Why use|Helps win|Supports|Shapes messages|Automatically register|Save as template|Architecture only|Run live|Custom name|Describe the|Every AI|Hello,|Visual illustration|System ·|Corporate ·|User ·|Favorite ·|Mission Control|Enterprise City|AI Builder Studio|Builder|Studio →|Automation →|Network →|skills|Info)\b/;

const STR_RE = /"((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'/g;
const HAS_CYR = /[А-Яа-яЁё]/;
const HAS_LAT = /[A-Za-z]/;

function walk(dir, acc = []) {
  if (!fs.existsSync(dir)) return acc;
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      if (ent.name === "node_modules" || ent.name === "dist") continue;
      walk(p, acc);
    } else if (/\.(tsx|ts)$/.test(ent.name) && !/\.test\.(tsx|ts)$/.test(ent.name)) {
      if (DICT_BASENAMES.has(ent.name)) continue;
      acc.push(p);
    }
  }
  return acc;
}

function looksLikeCssOrCode(s) {
  if (s.startsWith("@/") || s.startsWith("/") || s.startsWith("http")) return true;
  if (s.startsWith("application/") || /^Content-Type$/i.test(s)) return true;
  if (/^(flex|grid|block|inline|hidden|relative|absolute|eds-|pb-|abs-|mt-|mb-|ml-|mr-|px-|py-|p-|gap-|text-|bg-|border-|w-|h-|max-|min-|space-|list-|overflow-|rounded-|items-|justify-|col-|row-|lg:|md:|sm:|font-|is-|underline|decoration-)/.test(s)) {
    return true;
  }
  const toks = s.trim().split(/\s+/);
  if (
    toks.length >= 2 &&
    toks.every(
      (tok) =>
        /[-:/]/.test(tok) ||
        /^(flex|grid|block|inline|hidden|relative|absolute|font|medium|bold|sm|md|lg|xl)$/.test(tok) ||
        /^(eds-|pb-|abs-|is-|text-|bg-|border-|mt-|mb-|gap-|space-|rounded-|items-|justify-|col-|row-|w-|h-|p-|px-|py-|max-|min-|overflow-)/.test(
          tok,
        ),
    )
  ) {
    return true;
  }
  if (/^[a-z0-9_./:?&=%-]+$/i.test(s) && !/\s/.test(s)) return true;
  if (/^define_|^register_|^attach_|^save_|^clone_|^run_|^org_|^avatar_/.test(s)) return true;
  return false;
}

function isUserFacingEnglish(s) {
  if (!s || s.length < 2) return false;
  if (HAS_CYR.test(s)) return false;
  if (!HAS_LAT.test(s)) return false;
  if (ALLOW_EXACT.has(s) || ALLOW_EXACT.has(s.trim())) return false;
  if (looksLikeCssOrCode(s)) return false;
  if (UI_EN.test(s)) return true;
  // Sentence-like English (space + capital Latin word of length >= 4)
  if (/\s/.test(s) && /\b[A-Z][a-z]{3,}\b/.test(s) && s.length >= 10) return true;
  return false;
}

function scanFiles(files) {
  let ru = 0;
  let en = 0;
  const enHits = [];
  for (const file of files) {
    const text = fs.readFileSync(file, "utf8");
    let m;
    STR_RE.lastIndex = 0;
    while ((m = STR_RE.exec(text))) {
      const inner = (m[1] ?? m[2] ?? "").replace(/\\n/g, " ");
      if (HAS_CYR.test(inner)) {
        ru += 1;
        continue;
      }
      if (isUserFacingEnglish(inner)) {
        en += 1;
        if (enHits.length < 100) {
          enHits.push({ file: path.relative(WEB_ROOT, file), text: inner.slice(0, 120) });
        }
      }
    }
  }
  return { ru, en, hardcoded: en, enHits };
}

const criticalFiles = [
  ...CRITICAL_DIRS.flatMap((d) => walk(path.join(WEB_ROOT, d))),
  ...CRITICAL_FILES.map((f) => path.join(WEB_ROOT, f)).filter((f) => fs.existsSync(f) && !DICT_BASENAMES.has(path.basename(f))),
];
// Glossaries counted only for RU presence, not EN keys — skip dict files entirely for EN gate
const allPb = walk(path.join(WEB_ROOT, "platform-builder"));
const critical = scanFiles(criticalFiles);
const all = scanFiles(allPb);

const missingTranslation = critical.en;
const coverageCritical =
  critical.ru + critical.en === 0
    ? 100
    : Math.round((critical.ru / (critical.ru + critical.en)) * 1000) / 10;
const coverageAll =
  all.ru + all.en === 0 ? 100 : Math.round((all.ru / (all.ru + all.en)) * 1000) / 10;

const report = {
  sprint: "42.5",
  critical: {
    russianStrings: critical.ru,
    englishStrings: critical.en,
    hardcodedEnglish: critical.hardcoded,
    missingTranslation,
    localizationCoverage: coverageCritical,
  },
  platformBuilder: {
    russianStrings: all.ru,
    englishStrings: all.en,
    hardcodedEnglish: all.hardcoded,
    localizationCoverage: coverageAll,
  },
  samples: critical.enHits.slice(0, 50),
};

const outDir = path.join(WEB_ROOT, "reports");
fs.mkdirSync(outDir, { recursive: true });
const outFile = path.join(outDir, "localization_audit_42_5.json");
fs.writeFileSync(outFile, JSON.stringify(report, null, 2));

console.log("=== Localization Audit (Sprint 42.5) ===");
console.log("Critical surfaces (Concierge / AI Builder / AI Team / Framework / Studio):");
console.log(`  Русских строк:         ${critical.ru}`);
console.log(`  Английских строк:      ${critical.en}`);
console.log(`  Hardcoded строк:       ${critical.hardcoded}`);
console.log(`  Missing translation:   ${missingTranslation}`);
console.log(`  Localization coverage: ${coverageCritical}%`);
console.log("All platform-builder:");
console.log(`  Русских строк:         ${all.ru}`);
console.log(`  Английских строк:      ${all.en}`);
console.log(`  Localization coverage: ${coverageAll}%`);
console.log(`Report: ${outFile}`);

if (critical.en > 0) {
  console.error("\nFAIL: critical surfaces still contain English UI strings.");
  for (const h of critical.enHits.slice(0, 40)) {
    console.error(`  - ${h.file}: ${h.text}`);
  }
  process.exit(1);
}

console.log("\nPASS: critical surfaces — English UI = 0, coverage gate OK.");
process.exit(0);
