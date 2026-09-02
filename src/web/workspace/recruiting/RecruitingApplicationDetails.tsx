import { pick } from "./recruitingApi";
import { recruitingClickLabel, recruitingConsentLabel, recruitingUtmLabel } from "./recruitingLabels";

type Row = Record<string, unknown>;

function createdLabel(row: Row): string {
  const raw = String(row.created_at || row.submitted_at || "").trim();
  if (!raw) return "—";
  return raw.replace("T", " ").replace(/\.\d+Z$/, " UTC").slice(0, 19);
}

export function RecruitingApplicationDetails({
  row,
  testId = "recruiting-application-details",
}: {
  row: Row | null | undefined;
  testId?: string;
}) {
  if (!row) return null;
  const fields: [string, string][] = [
    ["Имя", pick(row, "name")],
    ["Телефон", pick(row, "phone")],
    ["Email", pick(row, "email")],
    ["Возраст", pick(row, "age")],
    ["Страна", pick(row, "country")],
    ["Язык", pick(row, "preferred_language")],
    ["Программа", pick(row, "program_of_interest", "vacancy", "vacancy_id")],
    ["Подразделение", pick(row, "unit_of_interest")],
    ["Мотивация", pick(row, "application_message")],
    ["Источник", pick(row, "source")],
    ["Проект", pick(row, "project_key")],
    ["Согласие", recruitingConsentLabel(row.contact_consent)],
    ["Создана", createdLabel(row)],
  ];
  const technical: [string, string][] = [
    ["UTM", recruitingUtmLabel(row)],
    ["Клики", recruitingClickLabel(row)],
    ["Reference", pick(row, "external_id", "idempotency_key")],
  ];
  return (
    <div data-testid={testId}>
      <dl className="mt-3 grid gap-x-6 gap-y-2 sm:grid-cols-2 eds-type-small">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt className="eds-type-helper">{label}</dt>
            <dd className="whitespace-pre-wrap break-words">{value}</dd>
          </div>
        ))}
      </dl>
      <details className="mt-2 eds-type-small" data-testid={`${testId}-attribution`}>
        <summary className="cursor-pointer eds-type-helper">Технические детали заявки</summary>
        <dl className="mt-2 grid gap-x-6 gap-y-2 sm:grid-cols-2">
          {technical.map(([label, value]) => (
            <div key={label}>
              <dt className="eds-type-helper">{label}</dt>
              <dd className="whitespace-pre-wrap break-words">{value}</dd>
            </div>
          ))}
        </dl>
      </details>
    </div>
  );
}
