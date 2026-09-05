/** Sprint 3.3.2 — honest no-credential copy. Do not invent CONNECTED. */

export const ADS_PROVIDER_MISSING_CONFIG_RU: Record<string, string> = {
  meta: "Не настроен META_ADS_APP_ID / META_ADS_APP_SECRET",
  google: "Не настроены GOOGLE_ADS_CLIENT_ID / GOOGLE_ADS_CLIENT_SECRET / GOOGLE_ADS_DEVELOPER_TOKEN",
  tiktok: "Не настроены TIKTOK_ADS_APP_ID / TIKTOK_ADS_APP_SECRET",
};

export const PROVIDER_WIZARD_LOAD_ERROR_RU =
  "Не удалось загрузить мастер подключения.\nОбновите страницу или повторите попытку.";

const UNCONFIGURED = new Set(["NOT_CONFIGURED", "not_connected", "WAITING_PROVIDER", ""]);

export function adsMissingConfigMessage(provider?: string | null, status?: string | null): string | null {
  if (!provider) return null;
  const copy = ADS_PROVIDER_MISSING_CONFIG_RU[provider];
  if (!copy) return null;
  if (status && !UNCONFIGURED.has(status)) return null;
  return copy;
}
