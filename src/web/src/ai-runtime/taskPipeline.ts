/**
 * Sprint 30.5 — AI task pipeline stages (Waiting → Failed).
 */

import type { AiTaskStage, JobLifecycle } from "@/enterprise-runtime/types";

export const AI_TASK_STAGES: { id: AiTaskStage; label: string; labelRu: string; order: number }[] = [
  { id: "waiting", label: "Waiting", labelRu: "Ожидание", order: 0 },
  { id: "preparing", label: "Preparing", labelRu: "Подготовка", order: 1 },
  { id: "running", label: "Running", labelRu: "Выполнение", order: 2 },
  { id: "review", label: "Review", labelRu: "Проверка", order: 3 },
  { id: "completed", label: "Completed", labelRu: "Завершено", order: 4 },
  { id: "failed", label: "Failed", labelRu: "Ошибка", order: 5 },
];

export function stageFromLifecycle(status: JobLifecycle, progress: number): AiTaskStage {
  if (status === "failed") return "failed";
  if (status === "completed" || status === "cancelled") return "completed";
  if (status === "paused" || status === "waiting" || status === "retrying") {
    return progress < 8 ? "waiting" : "preparing";
  }
  if (status === "running") {
    if (progress < 15) return "preparing";
    if (progress >= 85) return "review";
    return "running";
  }
  return "waiting";
}

export function stageLabelRu(stage: AiTaskStage): string {
  return AI_TASK_STAGES.find((s) => s.id === stage)?.labelRu || stage;
}
