import { useEffect, useMemo, useState } from "react";
import { Button, Input } from "@/ui";
import { pick } from "./recruitingApi";
import { ruLeadStatus } from "./recruitingLabels";
import { RecruitingApplicationDetails } from "./RecruitingApplicationDetails";
import {
  LEAD_STATUS_CHOICES,
  type RecruiterOption,
  type WorkflowRow,
  isActiveVacancy,
  recruiterLabel,
  vacancyTitle,
} from "./recruitingWorkflow";

type Props = {
  lead: WorkflowRow;
  vacancies: WorkflowRow[];
  recruiters: RecruiterOption[];
  canOperate: boolean;
  canConvert: boolean;
  canCreate: boolean;
  onAssign: (assignee: string) => Promise<boolean>;
  onVacancy: (vacancyId: string) => Promise<boolean>;
  onStatus: (status: string) => Promise<boolean>;
  onQualify: () => Promise<boolean>;
  onConvert: () => Promise<boolean>;
  onNote: (notes: string) => Promise<boolean>;
  onOpenCandidate: (candidateId: string) => void;
  onCreateVacancy: () => void;
};

export function LeadWorkflowPanel({
  lead,
  vacancies,
  recruiters,
  canOperate,
  canConvert,
  canCreate,
  onAssign,
  onVacancy,
  onStatus,
  onQualify,
  onConvert,
  onNote,
  onOpenCandidate,
  onCreateVacancy,
}: Props) {
  const status = String(lead.status || "new");
  const converted = status === "converted";
  const lost = status === "lost";
  const candidateId = String(lead.candidate_id || "").trim();
  const activeVacancies = vacancies.filter(isActiveVacancy);
  const [assignee, setAssignee] = useState(String(lead.assignee || ""));
  const [vacancyId, setVacancyId] = useState(String(lead.vacancy_id || ""));
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [confirmVacancy, setConfirmVacancy] = useState(false);
  const [confirmUnassigned, setConfirmUnassigned] = useState(false);

  useEffect(() => {
    setAssignee(String(lead.assignee || ""));
    setVacancyId(String(lead.vacancy_id || ""));
    setNote("");
    setConfirmVacancy(false);
    setConfirmUnassigned(false);
    setMsg(null);
    setErr(null);
  }, [lead.id, lead.assignee, lead.vacancy_id]);

  const recruiterChoices = useMemo(() => {
    const options = [...recruiters];
    if (assignee && !options.some((r) => r.id === assignee)) {
      options.unshift({ id: assignee, label: recruiterLabel(assignee) });
    }
    return options;
  }, [recruiters, assignee]);

  async function run(action: () => Promise<boolean>, success: string) {
    setBusy(true);
    setErr(null);
    setMsg(null);
    try {
      const ok = await action();
      if (ok) setMsg(success);
      else setErr("Не удалось сохранить. Попробуйте ещё раз.");
      return ok;
    } finally {
      setBusy(false);
    }
  }

  async function convertFlow() {
    if (!assignee) setConfirmUnassigned(true);
    if (!vacancyId && !confirmVacancy) {
      setConfirmVacancy(true);
      return;
    }
    setConfirmVacancy(false);
    await run(onConvert, "Кандидат создан");
  }

  return (
    <div className="grid gap-3" data-testid="lead-workflow-panel">
      <div>
        <h3 className="eds-type-title text-lg" data-testid="lead-workflow-name">
          {pick(lead, "name")}
        </h3>
        {converted ? (
          <p className="mt-1 eds-type-helper" data-testid="lead-converted-banner">
            Кандидат создан
          </p>
        ) : null}
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        <label className="grid gap-1 eds-type-small">
          <span>Статус</span>
          {converted || !canOperate ? (
            <p data-testid="lead-status-readonly">{ruLeadStatus(status)}</p>
          ) : (
            <select
              className="eds-input"
              data-testid="lead-status-select"
              disabled={busy}
              value={status === "converted" ? "new" : status}
              onChange={(e) => {
                const next = e.target.value;
                if (next === "converted") return;
                void run(() => onStatus(next), "Статус сохранён");
              }}
            >
              {LEAD_STATUS_CHOICES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          )}
        </label>
        <label className="grid gap-1 eds-type-small">
          <span>Ответственный</span>
          {canOperate && !converted ? (
            <select
              className="eds-input"
              data-testid="lead-recruiter-select"
              disabled={busy}
              value={assignee}
              onChange={(e) => {
                const next = e.target.value;
                const previous = assignee;
                setAssignee(next);
                void (async () => {
                  const ok = await run(() => onAssign(next), "Ответственный сохранён");
                  if (!ok) setAssignee(previous);
                })();
              }}
            >
              <option value="">Не назначен</option>
              {recruiterChoices.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          ) : (
            <p data-testid="lead-recruiter-readonly">{recruiterLabel(lead.assignee)}</p>
          )}
        </label>
        <label className="grid gap-1 eds-type-small">
          <span>Вакансия</span>
          {canOperate && !converted ? (
            activeVacancies.length ? (
              <select
                className="eds-input"
                data-testid="lead-vacancy-select"
                disabled={busy}
                value={vacancyId}
                onChange={(e) => {
                  const next = e.target.value;
                  const previous = vacancyId;
                  setVacancyId(next);
                  if (!next) return;
                  void (async () => {
                    const ok = await run(() => onVacancy(next), "Вакансия сохранена");
                    if (!ok) setVacancyId(previous);
                  })();
                }}
              >
                <option value="">Не выбрана</option>
                {activeVacancies.map((item) => (
                  <option key={String(item.id)} value={String(item.id)}>
                    {vacancyTitle(item)}
                  </option>
                ))}
              </select>
            ) : (
              <div data-testid="lead-vacancy-empty">
                <p>Нет активных вакансий</p>
                {canCreate ? (
                  <Button size="sm" className="mt-1" variant="secondary" onClick={onCreateVacancy}>
                    Создать вакансию
                  </Button>
                ) : null}
              </div>
            )
          ) : (
            <p>{vacancyTitle(vacancies.find((v) => String(v.id) === String(lead.vacancy_id)) || { title: lead.vacancy })}</p>
          )}
        </label>
      </div>

      {canOperate && recruiterChoices.length === 1 && !assignee && !converted ? (
        <Button
          size="sm"
          variant="secondary"
          data-testid="lead-auto-assign"
          disabled={busy}
          onClick={() => {
            const only = recruiterChoices[0];
            if (!only) return;
            setAssignee(only.id);
            void run(() => onAssign(only.id), "Ответственный сохранён");
          }}
        >
          Назначить автоматически
        </Button>
      ) : null}

      {canOperate ? (
        <div className="flex flex-wrap gap-2" data-testid="lead-primary-actions">
          {!converted && status !== "qualified" && !lost ? (
            <Button size="sm" disabled={busy} data-testid="lead-qualify" onClick={() => void run(onQualify, "Статус сохранён")}>
              Квалифицировать
            </Button>
          ) : null}
          {converted && candidateId ? (
            <Button size="sm" data-testid="lead-open-candidate" onClick={() => onOpenCandidate(candidateId)}>
              Открыть кандидата
            </Button>
          ) : canConvert && !converted && !lost ? (
            <Button size="sm" disabled={busy} data-testid="lead-convert" onClick={() => void convertFlow()}>
              Перевести в кандидаты
            </Button>
          ) : null}
        </div>
      ) : null}

      {confirmUnassigned ? (
        <p className="eds-type-helper" data-testid="lead-unassigned-warning">
          Ответственный не назначен. Можно продолжить.
        </p>
      ) : null}
      {confirmVacancy ? (
        <div className="flex flex-wrap items-center gap-2" data-testid="lead-vacancy-confirm">
          <p>Вакансия не выбрана. Продолжить без вакансии?</p>
          <Button size="sm" variant="ghost" onClick={() => setConfirmVacancy(false)}>
            Отмена
          </Button>
          <Button
            size="sm"
            onClick={() => {
              setConfirmVacancy(true);
              void run(onConvert, "Кандидат создан");
              setConfirmVacancy(false);
            }}
          >
            Продолжить
          </Button>
        </div>
      ) : null}

      {canOperate && !converted ? (
        <form
          className="flex flex-wrap gap-2"
          data-testid="lead-note-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (!note.trim()) return;
            void run(() => onNote(note.trim()), "Заметка сохранена").then((ok) => {
              if (ok) setNote("");
            });
          }}
        >
          <Input placeholder="Заметка" value={note} onChange={(e) => setNote(e.target.value)} />
          <Button type="submit" size="sm" variant="secondary" disabled={busy}>
            Добавить заметку
          </Button>
          {!lost ? (
            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={busy}
              data-testid="lead-reject"
              onClick={() => void run(() => onStatus("lost"), "Статус сохранён")}
            >
              Отклонить
            </Button>
          ) : null}
        </form>
      ) : null}

      {msg ? (
        <p className="eds-type-helper" data-testid="lead-workflow-success">
          {msg}
        </p>
      ) : null}
      {err ? (
        <p className="eds-type-helper text-[var(--eds-danger,#b91c1c)]" data-testid="lead-workflow-error">
          {err}
        </p>
      ) : null}

      <RecruitingApplicationDetails row={lead} testId="recruiting-lead-details" />
    </div>
  );
}
