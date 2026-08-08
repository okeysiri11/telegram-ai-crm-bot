import { Card } from "@/ui";
import { bu } from "../i18n/builderUiRu";

type Props = {
  errors?: Array<string | { message?: string; field?: string }>;
  suggestions?: Array<string | { message?: string }>;
  ok?: boolean;
};

function asText(item: string | { message?: string; field?: string }): string {
  if (typeof item === "string") return item;
  const field = item.field ? `${item.field}: ` : "";
  return `${field}${item.message || ""}`.trim() || "—";
}

export function LiveValidation({ errors = [], suggestions = [], ok }: Props) {
  return (
    <Card title={bu("liveValidation")}>
      {ok ? <p className="text-sm text-emerald-700">{bu("valid")}</p> : null}
      {errors.length ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-rose-700">
          {errors.map((e, i) => (
            <li key={`${asText(e)}-${i}`}>{asText(e)}</li>
          ))}
        </ul>
      ) : null}
      {suggestions.length ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
          {suggestions.map((s, i) => (
            <li key={`${asText(s)}-${i}`}>{asText(s)}</li>
          ))}
        </ul>
      ) : null}
    </Card>
  );
}
