import { Button } from "@/ui";
import { pick } from "./recruitingApi";
import { PIPELINE_LABELS } from "./recruitingLabels";
import {
  applicationCountLabel,
  candidateSourceList,
  candidateVacancyList,
  createdLabel,
  recruiterLabel,
  type WorkflowRow,
} from "./recruitingWorkflow";

type Preview = {
  name?: string;
  application_count?: number;
  lead_count?: number;
  pipeline_stage?: string;
  assignee?: string;
  source_count?: number;
};

type Props = {
  left: WorkflowRow;
  right: WorkflowRow;
  vacancies: WorkflowRow[];
  preview: Preview | null;
  safety: string;
  error: string | null;
  conflict: boolean;
  success: boolean;
  busy: boolean;
  canForce: boolean;
  onCancel: () => void;
  onConfirm: (force: boolean) => void;
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="eds-type-helper">{label}</dt>
      <dd>{value || "—"}</dd>
    </div>
  );
}

function PersonCard({ title, row, vacancies }: { title: string; row: WorkflowRow; vacancies: WorkflowRow[] }) {
  const apps = Array.isArray(row.applications) ? row.applications.length : 0;
  return (
    <div className="grid gap-2 rounded-lg border border-[var(--eds-border)] p-3" data-testid={`merge-person-${title === "Кандидат 1" ? "left" : "right"}`}>
      <h4 className="eds-type-title text-base">{title}</h4>
      <dl className="grid gap-x-4 gap-y-2 eds-type-small">
        <Field label="Имя" value={pick(row, "name")} />
        <Field label="Телефон" value={pick(row, "phone")} />
        <Field label="Email" value={pick(row, "email")} />
        <Field label="Рекрутер" value={recruiterLabel(row.assignee)} />
        <Field label="Текущий этап" value={PIPELINE_LABELS[String(row.pipeline_stage || "")] || String(row.pipeline_stage || "—")} />
        <Field label="Вакансии" value={candidateVacancyList(row, vacancies)} />
        <Field label="Количество заявок" value={apps ? applicationCountLabel(row) : "0"} />
        <Field label="Источники" value={candidateSourceList(row)} />
        <Field label="Дата первой заявки" value={createdLabel(row)} />
        <Field label="Дата последней заявки" value={createdLabel({ created_at: row.updated_at || row.created_at })} />
      </dl>
      <details className="eds-type-small" data-testid="merge-technical-details">
        <summary className="cursor-pointer eds-type-helper">Технические детали</summary>
        <p className="mt-1 eds-type-helper">ID: {String(row.id || "—")}</p>
      </details>
    </div>
  );
}

export function CandidateMergePanel({
  left,
  right,
  vacancies,
  preview,
  safety,
  error,
  conflict,
  success,
  busy,
  canForce,
  onCancel,
  onConfirm,
}: Props) {
  const forceNeeded = safety === "ambiguous" || safety === "unsafe";
  const stageLabel = PIPELINE_LABELS[String(preview?.pipeline_stage || "")] || String(preview?.pipeline_stage || "—");

  return (
    <div className="grid gap-3" data-testid="candidate-merge-panel">
      <h3 className="eds-type-title text-lg">Объединить кандидатов</h3>
      <div className="grid gap-3 md:grid-cols-2" data-testid="merge-comparison">
        <PersonCard title="Кандидат 1" row={left} vacancies={vacancies} />
        <PersonCard title="Кандидат 2" row={right} vacancies={vacancies} />
      </div>

      {preview ? (
        <div className="rounded-lg border border-[var(--eds-border)] p-3" data-testid="merge-preview">
          <h4 className="eds-type-title text-base">После объединения</h4>
          <dl className="mt-2 grid gap-x-6 gap-y-2 sm:grid-cols-2 eds-type-small">
            <Field label="Кандидат" value={String(preview.name || pick(left, "name"))} />
            <Field label="Заявок" value={String(preview.application_count ?? "—")} />
            <Field label="Лидов" value={String(preview.lead_count ?? "—")} />
            <Field label="Текущий этап" value={stageLabel} />
            <Field label="Рекрутер" value={recruiterLabel(preview.assignee)} />
            <Field label="Источников" value={String(preview.source_count ?? "—")} />
          </dl>
        </div>
      ) : null}

      {forceNeeded ? (
        <p className="eds-type-helper" data-testid="merge-force-warning">
          Внимание: идентичность {safety === "unsafe" ? "небезопасна" : "неоднозначна"}. Объединение может связать разных людей и требует подтверждения владельца.
        </p>
      ) : null}

      {error ? (
        <p className="eds-type-helper" data-testid={conflict ? "merge-conflict" : "merge-error"}>
          {error}
        </p>
      ) : null}

      {success ? (
        <p data-testid="merge-success">Кандидаты объединены</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="ghost" data-testid="merge-cancel" onClick={onCancel} disabled={busy}>
            Отмена
          </Button>
          <Button
            size="sm"
            data-testid="merge-confirm"
            disabled={busy || (forceNeeded && !canForce)}
            onClick={() => onConfirm(forceNeeded)}
          >
            Объединить
          </Button>
        </div>
      )}
    </div>
  );
}
