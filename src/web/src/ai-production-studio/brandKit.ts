/**
 * Sprint 32.0 — Enterprise Brand Kit (Production Studio).
 * Applies to prompt variables · allowed models · default providers.
 * No second brand engine — themes deepLink remains Platform Builder.
 */

export type BrandKit = {
  name: string;
  logoUrl: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  typography: string;
  voice: string;
  writingStyle: string;
  visualStyle: string;
  allowedModels: string[];
  defaultProviders: string[];
  forbiddenPhrases: string[];
  updatedAt: string;
};

export const DEFAULT_BRAND_KIT: BrandKit = {
  name: "ADOS Enterprise",
  logoUrl: "/brand/ados-mark.svg",
  primaryColor: "#0B6E4F",
  secondaryColor: "#1B2838",
  accentColor: "#C4A35A",
  typography: "EDS Sans · Display: EDS Display",
  voice: "уверенный · ясный · корпоративный",
  writingStyle: "кратко · без жаргона · CTA в конце",
  visualStyle: "тёмная поверхность · спокойный motion · без неона",
  allowedModels: ["gpt-4o-mini", "claude-haiku", "gemini-1.5-flash", "llama-3.1-8b", "corp-llm"],
  defaultProviders: ["litellm", "openai", "anthropic", "groq"],
  forbiddenPhrases: ["гарантия 100%", "без риска", "медицинское чудо"],
  updatedAt: new Date().toISOString(),
};

const BRAND_KEY = "ews_brand_kit_v1";

export function readBrandKit(): BrandKit {
  try {
    const raw = localStorage.getItem(BRAND_KEY);
    if (!raw) return { ...DEFAULT_BRAND_KIT };
    return { ...DEFAULT_BRAND_KIT, ...(JSON.parse(raw) as Partial<BrandKit>) };
  } catch {
    return { ...DEFAULT_BRAND_KIT };
  }
}

export function writeBrandKit(kit: BrandKit): BrandKit {
  const next = { ...kit, updatedAt: new Date().toISOString() };
  try {
    localStorage.setItem(BRAND_KEY, JSON.stringify(next));
  } catch {
    /* ignore */
  }
  return next;
}

/** Inject brand defaults into prompt variable map. */
export function brandVariables(kit: BrandKit = readBrandKit()): Record<string, string> {
  return {
    brand: kit.name,
    tone: kit.voice,
    style: kit.visualStyle,
    colors: `${kit.primaryColor}, ${kit.secondaryColor}, ${kit.accentColor}`,
    forbidden: kit.forbiddenPhrases.join("; "),
    typography: kit.typography,
    writing: kit.writingStyle,
  };
}
