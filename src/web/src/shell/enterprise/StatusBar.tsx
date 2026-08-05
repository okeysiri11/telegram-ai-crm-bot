import { webConfig } from "@/config/webConfig";
import { useRuntimeHealth, toStatusSnapshots } from "./useRuntimeHealth";
import { useEnterpriseStatus } from "@/command-center-runtime/useEnterpriseStatus";
import { useShellLayoutStore } from "./shellLayoutStore";

/**
 * Sprint 27.5 / 30.2 — Enterprise Status Bar (Russian chrome).
 */
export function StatusBar() {
  const { items } = useRuntimeHealth(45_000);
  const statusItems = toStatusSnapshots(items).filter((i) =>
    ["runtime", "api", "providers", "mcp"].includes(i.id),
  );
  const ent = useEnterpriseStatus();
  const setActivityOpen = useShellLayoutStore((s) => s.setActivityOpen);
  const toggleDock = useShellLayoutStore((s) => s.toggleDock);

  const connTone = ent.connection === "online" ? "ok" : ent.connection === "degraded" ? "warn" : "err";
  const connRu =
    ent.connection === "online"
      ? "онлайн"
      : ent.connection === "degraded"
        ? "ограничен"
        : "офлайн";

  return (
    <footer className="ews-status ews-glass" role="status" aria-label="Статус предприятия">
      <div className="ews-status-inner">
        <div className="ews-status-item" title="Окружение">
          <span className="ews-status-label">Среда</span>
          <span className="ews-status-detail">{ent.environment}</span>
        </div>
        <div className="ews-status-item" title="Активное пространство">
          <span className="ews-status-label">Пространство</span>
          <span className="ews-status-detail">{ent.workspace}</span>
        </div>
        <div className="ews-status-item" title="Текущий пользователь">
          <span className="ews-status-label">Пользователь</span>
          <span className="ews-status-detail">{ent.userLabel}</span>
        </div>
        <div className="ews-status-item" title={`Среда выполнения: ${ent.runtime}`}>
          <span className={`ews-dot ews-dot--${statusItems.find((i) => i.id === "runtime")?.tone || "unknown"}`} aria-hidden />
          <span className="ews-status-label">Runtime</span>
          <span className="ews-status-detail">{ent.runtime}</span>
        </div>
        <div className="ews-status-item" title="Ветка Git">
          <span className="ews-status-label">Git</span>
          <span className="ews-status-detail">{ent.gitBranch}</span>
        </div>
        <div className="ews-status-item" title="Соединение">
          <span className={`ews-dot ews-dot--${connTone}`} aria-hidden />
          <span className="ews-status-label">Сеть</span>
          <span className="ews-status-detail">{connRu}</span>
        </div>
        <div className="ews-status-item" title="Статус AI">
          <span className={`ews-dot ews-dot--${statusItems.find((i) => i.id === "providers")?.tone || "ok"}`} aria-hidden />
          <span className="ews-status-label">AI</span>
          <span className="ews-status-detail">{ent.aiStatus}</span>
        </div>
        <button
          type="button"
          className="ews-status-item ews-status-btn"
          title="Открыть уведомления"
          onClick={() => setActivityOpen(true)}
        >
          <span className="ews-status-label">Уведомления</span>
          <span className="ews-status-detail">{ent.unread}</span>
        </button>
        <button
          type="button"
          className="ews-status-item ews-status-btn"
          title="Фоновые задачи · панель состояния"
          onClick={() => toggleDock("bottom")}
        >
          <span className="ews-status-label">Задачи</span>
          <span className="ews-status-detail">{ent.jobs}</span>
        </button>
        {statusItems
          .filter((i) => i.id === "api" || i.id === "mcp")
          .map((item) => (
            <div key={item.id} className="ews-status-item" title={`${item.label}: ${item.detail}`}>
              <span className={`ews-dot ews-dot--${item.tone}`} aria-hidden />
              <span className="ews-status-label">{item.label}</span>
              <span className="ews-status-detail">{item.detail}</span>
            </div>
          ))}
        <div className="ews-status-item ews-status-meta" title={webConfig.application}>
          <span className="ews-status-detail">{webConfig.version}</span>
        </div>
      </div>
    </footer>
  );
}
