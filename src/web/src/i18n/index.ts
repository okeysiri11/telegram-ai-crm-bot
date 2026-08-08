import { create } from "zustand";
import { messages, type Locale } from "./messages";
import { webConfig } from "@/config/webConfig";

type I18nState = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
};

export const useI18n = create<I18nState>((set, get) => ({
  locale: webConfig.defaultLocale,
  setLocale: (locale) => set({ locale }),
  t: (key) => messages[get().locale][key] ?? messages.en[key] ?? key,
}));

export type { Locale };
export { PLATFORM_GLOSSARY, term, localizeLabel, builderDisplayName, BUILDER_NAV_RU } from "./platformGlossary";
