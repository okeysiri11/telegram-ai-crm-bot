import { Tooltip } from "@/ui";
import { useLocation } from "react-router-dom";
import { helpForRoute, type ModuleHelp } from "./moduleHelpCatalog";

export function ModuleHelpIcon({
  pathname,
  help,
}: {
  pathname?: string;
  help?: ModuleHelp;
}) {
  const loc = useLocation();
  const entry = help || helpForRoute(pathname || loc.pathname);
  if (!entry) return null;
  const text = [
    `Назначение: ${entry.purpose}`,
    `Когда: ${entry.why}`,
    `Результат: ${entry.expectedResult}`,
    `Сценарий: ${entry.workflow}`,
    `Сложность: ${entry.difficulty}`,
    `Время: ~${entry.setupMinutes} мин`,
    `Пример: ${entry.example}`,
    entry.related?.length ? `Связанные: ${entry.related.join(", ")}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  return (
    <Tooltip label={text}>
      <button
        type="button"
        className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-[var(--ew-border)] eds-type-caption"
        aria-label="Справка по модулю"
        data-testid="module-help-icon"
      >
        i
      </button>
    </Tooltip>
  );
}
