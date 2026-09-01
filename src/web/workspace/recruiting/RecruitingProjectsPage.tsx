/**
 * Recruiting projects catalog — Vanguard is a project, not a vertical.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card } from "@/ui";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useRoleSwitcher } from "@/navigation/roleSwitcherStore";
import { asList, recruitingOpsGet, recruitingOpsUserError, pick, recruitingWorkspaceHeaders } from "./recruitingApi";
import { mapUiRoleToRecruiting } from "./recruitingLabels";
import { RecruitingOpsFrame, displayMetric } from "./RecruitingOpsFrame";

type ProjectRow = Record<string, unknown>;

function asRecord(json: unknown): Record<string, unknown> {
  return json && typeof json === "object" ? (json as Record<string, unknown>) : {};
}

function statusLabel(value: unknown): string {
  const rec = value && typeof value === "object" ? (value as Record<string, unknown>) : {};
  return displayMetric(rec.label_ru || rec.code);
}

export function RecruitingProjectsPage() {
  const navigate = useNavigate();
  const organizationId = useOrgSelector((s) => s.organizationId);
  const recruitingRole = mapUiRoleToRecruiting(useRoleSwitcher((s) => s.activeRoleId));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<ProjectRow[]>([]);

  const headers = useMemo(
    () => recruitingWorkspaceHeaders(organizationId, recruitingRole),
    [organizationId, recruitingRole],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const res = await recruitingOpsGet("/projects", headers);
    if (!res.ok) {
      setError(recruitingOpsUserError(res.status, res.json));
      setProjects([]);
      setLoading(false);
      return;
    }
    setProjects(asList(res.json) as ProjectRow[]);
    setLoading(false);
  }, [headers]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <RecruitingOpsFrame
      title="Проекты рекрутинга"
      subtitle="Сайты и источники заявок внутри Рекрутинга. Не отдельный бизнес-вертикаль."
      testId="recruiting-projects-page"
      error={error}
      onRefresh={() => void load()}
    >
      <div className="grid gap-4 md:grid-cols-2" data-testid="recruiting-project-cards">
        {projects.map((project) => {
          const key = pick(project, "project_key", "id");
          return (
            <Card key={key} title={pick(project, "name")}>
              <div data-testid={`recruiting-project-card-${key}`}>
              <p className="eds-type-helper">Тип: {pick(project, "type_ru", "type")}</p>
              <dl className="mt-3 grid grid-cols-2 gap-2 eds-type-small">
                <dt>Статус сайта</dt>
                <dd>{statusLabel(project.website_status)}</dd>
                <dt>Статус интеграции</dt>
                <dd>{statusLabel(project.integration_status)}</dd>
                <dt>Лиды</dt>
                <dd>{displayMetric(project.leads)}</dd>
                <dt>Кандидаты</dt>
                <dd>{displayMetric(project.candidates)}</dd>
                <dt>Активные вакансии</dt>
                <dd>{displayMetric(project.active_vacancies)}</dd>
                <dt>Последняя заявка</dt>
                <dd>{displayMetric(project.last_application_at)}</dd>
                <dt>Последняя синхронизация</dt>
                <dd>{displayMetric(project.last_sync_at)}</dd>
              </dl>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button onClick={() => navigate(`/workspace/recruiting/projects/${key}`)}>Открыть проект</Button>
                {project.public_url ? (
                  <Button variant="secondary" onClick={() => window.open(String(project.public_url), "_blank", "noopener")}>
                    Открыть сайт
                  </Button>
                ) : (
                  <Button variant="secondary" disabled>
                    Открыть сайт
                  </Button>
                )}
                <Button variant="secondary" onClick={() => navigate(`/workspace/recruiting/projects/${key}?tab=integration`)}>
                  Проверить интеграцию
                </Button>
              </div>
              </div>
            </Card>
          );
        })}
        {!loading && !projects.length && !error ? (
          <Card title="Проектов нет">
            <p>Нет данных</p>
          </Card>
        ) : null}
      </div>
    </RecruitingOpsFrame>
  );
}
