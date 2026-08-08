/**
 * Sprint 41.2 — apply interface preferences on boot.
 */

import { useEffect } from "react";
import { usePreferencesStore } from "./preferencesStore";
import { useI18n } from "@/i18n";

export function InterfacePreferencesBoot() {
  const applyToDocument = usePreferencesStore((s) => s.applyToDocument);
  const language = usePreferencesStore((s) => s.language);
  const setLocale = useI18n((s) => s.setLocale);

  useEffect(() => {
    applyToDocument();
    setLocale(language);
  }, [applyToDocument, language, setLocale]);

  return null;
}
