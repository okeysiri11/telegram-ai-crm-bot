import { useI18n } from "@/i18n";

export function LoadingScreen() {
  const t = useI18n((s) => s.t);
  return (
    <div className="flex min-h-full items-center justify-center">
      <div className="text-sm text-[var(--ew-muted)]">{t("common.loading")}</div>
    </div>
  );
}
