import type { EngineeringSpecification } from "./types.js";

export interface AnalyzedSpec {
  readonly specification: EngineeringSpecification;
  readonly needsDeveloper: boolean;
  readonly needsUi: boolean;
  readonly needsDocs: boolean;
  readonly needsQa: boolean;
  readonly needsReview: boolean;
  readonly needsBuild: boolean;
  readonly needsDeploy: boolean;
  readonly hasTests: boolean;
  readonly hasUiSignals: boolean;
  readonly hasDeploySignals: boolean;
}

/**
 * Analyzes an engineering specification structure (no architecture invention).
 */
export class TaskAnalyzer {
  analyze(
    input: EngineeringSpecification | string | Record<string, unknown>,
  ): AnalyzedSpec {
    const specification = normalizeSpec(input);
    const blob = [
      specification.mission,
      specification.objective,
      ...specification.requirements,
      ...specification.files,
      ...specification.modules,
      ...specification.tests,
      ...specification.acceptanceCriteria,
      specification.raw ?? "",
    ]
      .join("\n")
      .toLowerCase();

    const hasUiSignals =
      /\bui\b|frontend|react|tsx|css|page|dashboard|layout|component/.test(blob) ||
      specification.files.some((f) => /\.(tsx|jsx|css)$/i.test(f));
    const hasTests =
      specification.tests.length > 0 ||
      /\btest\b|qa|coverage|vitest|jest/.test(blob);
    const hasDeploySignals =
      /\bdeploy|release|ci\/?cd|production|publish/.test(blob);
    const hasDocs =
      specification.modules.length > 0 ||
      /\bdocs?|readme|documentation|guide/.test(blob) ||
      specification.files.some((f) => /\.md$/i.test(f));

    const needsDeveloper =
      specification.files.length > 0 ||
      specification.requirements.length > 0 ||
      /\bimplement|code|feature|api|backend|module/.test(blob) ||
      Boolean(specification.mission);

    return {
      specification,
      needsDeveloper,
      needsUi: hasUiSignals,
      needsDocs: hasDocs || specification.acceptanceCriteria.length > 0,
      needsQa: hasTests || specification.acceptanceCriteria.length > 0,
      needsReview: true,
      needsBuild: true,
      needsDeploy: hasDeploySignals,
      hasTests,
      hasUiSignals,
      hasDeploySignals,
    };
  }
}

function normalizeSpec(
  input: EngineeringSpecification | string | Record<string, unknown>,
): EngineeringSpecification {
  if (typeof input === "string") {
    return parseFreeform(input);
  }
  if (isSpec(input)) return input;

  const obj = input;
  const str = (k: string) =>
    typeof obj[k] === "string" ? (obj[k] as string) : "";
  const arr = (k: string) =>
    Array.isArray(obj[k])
      ? (obj[k] as unknown[]).map(String)
      : typeof obj[k] === "string"
        ? String(obj[k])
            .split(/\n|,/)
            .map((s) => s.trim())
            .filter(Boolean)
        : [];

  const mission = str("mission") || str("Mission") || "Engineering mission";
  const objective =
    str("objective") || str("Objective") || str("goal") || mission;
  return {
    mission,
    objective,
    requirements: arr("requirements").length
      ? arr("requirements")
      : arr("Requirements"),
    files: arr("files").length ? arr("files") : arr("Files"),
    modules: arr("modules").length ? arr("modules") : arr("Modules"),
    tests: arr("tests").length ? arr("tests") : arr("Tests"),
    acceptanceCriteria: arr("acceptanceCriteria").length
      ? arr("acceptanceCriteria")
      : arr("Acceptance Criteria").length
        ? arr("Acceptance Criteria")
        : arr("acceptance"),
    ...(typeof obj["raw"] === "string" ? { raw: obj["raw"] as string } : {}),
  };
}

function isSpec(v: unknown): v is EngineeringSpecification {
  return (
    typeof v === "object" &&
    v !== null &&
    "mission" in v &&
    "objective" in v &&
    "requirements" in v
  );
}

function parseFreeform(text: string): EngineeringSpecification {
  const section = (name: string): string[] => {
    const re = new RegExp(
      `${name}\\s*[:\\n]+([\\s\\S]*?)(?=\\n\\s*(?:Mission|Objective|Requirements|Files|Modules|Tests|Acceptance)|$)`,
      "i",
    );
    const m = text.match(re);
    if (!m?.[1]) return [];
    return m[1]
      .split(/\n/)
      .map((l) => l.replace(/^[-*•]\s*/, "").trim())
      .filter(Boolean);
  };
  const firstLine = (name: string): string => {
    const lines = section(name);
    return lines[0] ?? "";
  };
  return {
    mission: firstLine("Mission") || text.split("\n")[0]?.trim() || "Mission",
    objective: firstLine("Objective") || firstLine("Mission"),
    requirements: section("Requirements"),
    files: section("Files"),
    modules: section("Modules"),
    tests: section("Tests"),
    acceptanceCriteria: section("Acceptance Criteria").length
      ? section("Acceptance Criteria")
      : section("Acceptance"),
    raw: text,
  };
}

export function createTaskAnalyzer(): TaskAnalyzer {
  return new TaskAnalyzer();
}
