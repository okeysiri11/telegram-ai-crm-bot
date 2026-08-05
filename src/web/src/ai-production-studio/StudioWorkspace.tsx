import { Card } from "@/ui";
import {
  AI_STUDIO_CORE_IDS,
  PRODUCTION_STUDIOS,
  STUDIO_GROUPS,
  type ProductionStudioId,
} from "./productionCatalog";
import { useProductionStore } from "./productionStore";
import { StudioWorkbench } from "./StudioWorkbench";
import { BETA_PRODUCTION_STUDIOS } from "@/dashboard/betaHomeCatalog";

/** Lazy studio grid / detail — code-split from center shell. Sprint 30.5 RU. */
export function StudioWorkspace({ coreOnly = false }: { coreOnly?: boolean }) {
  const view = useProductionStore((s) => s.view);
  const activeStudioId = useProductionStore((s) => s.activeStudioId);
  const openStudio = useProductionStore((s) => s.openStudio);

  if (view === "studio" && activeStudioId) {
    return <StudioWorkbench studioId={activeStudioId} />;
  }

  const groups = coreOnly
    ? STUDIO_GROUPS.filter((g) => g.id === "generate" || g.id === "library" || g.id === "social")
    : STUDIO_GROUPS;

  return (
    <div className="stack-md">
      <Card title="Продакшн-студия · Beta">
        <p className="eds-type-helper mb-3">
          Видео · Изображения · Голос · Reels · Соцсети · Презентации · Библиотека промптов · Бренд-ассеты.
        </p>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 10,
          }}
        >
          {BETA_PRODUCTION_STUDIOS.map((s) => {
            const studio = PRODUCTION_STUDIOS.find((x) => x.id === s.id);
            if (!studio) return null;
            return (
              <button
                key={s.id}
                type="button"
                className="ews-glass"
                style={{
                  textAlign: "left",
                  padding: "0.85rem 1rem",
                  borderRadius: "var(--eds-radius-xl)",
                  border: "1px solid var(--eds-border)",
                  cursor: s.available ? "pointer" : "default",
                  opacity: s.available ? 1 : 0.75,
                }}
                onClick={() => {
                  if (s.available) openStudio(s.id as ProductionStudioId);
                }}
                disabled={!s.available}
              >
                <p className="font-semibold">{s.label}</p>
                <p className="eds-type-helper mt-1">{studio.description}</p>
              </button>
            );
          })}
        </div>
      </Card>

      {coreOnly ? (
        <section aria-label="Ядро AI-студии">
          <h2 className="eds-type-section mb-2">Визуальные студии</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
              gap: 10,
            }}
          >
            {AI_STUDIO_CORE_IDS.map((id) => {
              const s = PRODUCTION_STUDIOS.find((x) => x.id === id)!;
              return (
                <button
                  key={s.id}
                  type="button"
                  className="ews-glass"
                  style={{
                    textAlign: "left",
                    padding: "0.85rem 1rem",
                    borderRadius: "var(--eds-radius-xl)",
                    border: "1px solid var(--eds-border)",
                    cursor: "pointer",
                  }}
                  onClick={() => openStudio(s.id as ProductionStudioId)}
                >
                  <p className="font-semibold">{s.label}</p>
                  <p className="eds-type-helper mt-1">{s.description}</p>
                  <p className="eds-type-caption mt-2">{s.aiAgents[0]}</p>
                </button>
              );
            })}
          </div>
        </section>
      ) : (
        groups.map((g) => {
          const studios = PRODUCTION_STUDIOS.filter((s) => s.group === g.id);
          return (
            <section key={g.id} aria-label={g.label}>
              <h2 className="eds-type-section mb-2">{g.label}</h2>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                  gap: 10,
                }}
              >
                {studios.map((s) => {
                  return (
                    <button
                      key={s.id}
                      type="button"
                      className="ews-glass"
                      style={{
                        textAlign: "left",
                        padding: "0.85rem 1rem",
                        borderRadius: "var(--eds-radius-xl)",
                        border: "1px solid var(--eds-border)",
                        cursor: "pointer",
                      }}
                      onClick={() => openStudio(s.id as ProductionStudioId)}
                    >
                      <p className="font-semibold">{s.labelRu || s.label}</p>
                      <p className="eds-type-helper mt-1">{s.description}</p>
                      <p className="eds-type-caption mt-2">{s.aiAgents[0]}</p>
                    </button>
                  );
                })}
              </div>
            </section>
          );
        })
      )}
    </div>
  );
}
