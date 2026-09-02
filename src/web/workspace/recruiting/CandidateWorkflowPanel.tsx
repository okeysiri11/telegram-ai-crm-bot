import { Button } from "@/ui";
import { pick } from "./recruitingApi";
import { RecruitingApplicationDetails } from "./RecruitingApplicationDetails";
import {
  CANDIDATE_FLOW,
  createdLabel,
  recruiterLabel,
  sourceLabel,
  vacancyTitle,
  type WorkflowRow,
} from "./recruitingWorkflow";

type Props = {
  candidate: WorkflowRow;
  lead?: WorkflowRow | null;
  vacancies: WorkflowRow[];
  canOperate: boolean;
  onStage: (stage: string) => Promise<boolean>;
  onOpenLead: (leadId: string) => void;
};

export function CandidateWorkflowPanel({ candidate, lead, vacancies, canOperate, onStage, onOpenLead }: Props) {
  const stage = String(candidate.pipeline_stage || candidate.status || "NEW");
  const vacancy = vacancies.find((v) => String(v.id) === String(candidate.vacancy_id || lead?.vacancy_id || ""));
  const applications = Array.isArray(candidate.applications)
    ? (candidate.applications as WorkflowRow[])
    : [];
  const leadIds = [
    ...new Set(
      [
        ...((candidate.lead_ids as string[]) || []),
        String(candidate.lead_id || ""),
        String(lead?.id || ""),
        ...applications.map((app) => String(app.lead_id || "")),
      ].filter(Boolean),
    ),
  ];

  return (
    <div className="grid gap-3" data-testid="candidate-workflow-panel">
      <h3 className="eds-type-title text-lg">{pick(candidate, "name")}</h3>
      <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2 eds-type-small">
        <div>
          <dt className="eds-type-helper">Имя</dt>
          <dd>{pick(candidate, "name")}</dd>
        </div>
        <div>
          <dt className="eds-type-helper">Телефон</dt>
          <dd>{pick(candidate, "phone")}</dd>
        </div>
        <div>
          <dt className="eds-type-helper">Email</dt>
          <dd>{pick(candidate, "email")}</dd>
        </div>
        {pick(candidate, "age") !== "—" ? (
          <div>
            <dt className="eds-type-helper">Возраст</dt>
            <dd>{pick(candidate, "age")}</dd>
          </div>
        ) : null}
        {pick(candidate, "preferred_language") !== "—" ? (
          <div>
            <dt className="eds-type-helper">Язык</dt>
            <dd>{pick(candidate, "preferred_language")}</dd>
          </div>
        ) : null}
        <div>
          <dt className="eds-type-helper">Вакансия</dt>
          <dd>{vacancyTitle(vacancy || { title: candidate.vacancy || lead?.vacancy })}</dd>
        </div>
        <div>
          <dt className="eds-type-helper">Текущий этап</dt>
          <dd>{CANDIDATE_FLOW.find((item) => item.id === stage)?.label || stage}</dd>
        </div>
        <div>
          <dt className="eds-type-helper">Ответственный</dt>
          <dd>{recruiterLabel(candidate.assignee || lead?.assignee)}</dd>
        </div>
        <div>
          <dt className="eds-type-helper">Источник</dt>
          <dd data-testid="candidate-source">{sourceLabel(candidate)}</dd>
        </div>
        <div>
          <dt className="eds-type-helper">Дата заявки</dt>
          <dd>{createdLabel(candidate)}</dd>
        </div>
      </dl>

      {leadIds.length ? (
        <div data-testid="candidate-applications">
          <p className="eds-type-helper">Заявки: {leadIds.length}</p>
          <div className="mt-1 flex flex-wrap gap-2" data-testid="candidate-open-lead">
            {leadIds.map((id) => (
              <Button key={id} size="sm" variant="secondary" onClick={() => onOpenLead(id)}>
                Открыть лид
              </Button>
            ))}
          </div>
        </div>
      ) : null}

      <div data-testid="candidate-pipeline">
        <p className="mb-2 eds-type-helper">Этап</p>
        <div className="flex flex-wrap items-center gap-1">
          {CANDIDATE_FLOW.map((item, index) => (
            <span key={item.id} className="flex flex-wrap items-center gap-1">
              {index > 0 ? <span className="eds-type-helper">→</span> : null}
              <Button
                size="sm"
                variant={stage === item.id ? "primary" : "secondary"}
                disabled={!canOperate || stage === item.id}
                data-testid={`candidate-stage-${item.id}`}
                aria-current={stage === item.id ? "step" : undefined}
                onClick={() => void onStage(item.id)}
              >
                {item.label}
              </Button>
            </span>
          ))}
        </div>
        {canOperate && stage !== "REJECTED" ? (
          <Button
            className="mt-2"
            size="sm"
            variant={stage === "REJECTED" ? "primary" : "ghost"}
            data-testid="candidate-stage-REJECTED"
            onClick={() => void onStage("REJECTED")}
          >
            Отклонён
          </Button>
        ) : (
          <p className="mt-2 eds-type-helper">Отклонён</p>
        )}
      </div>

      <RecruitingApplicationDetails row={candidate} testId="recruiting-candidate-details" />
    </div>
  );
}
