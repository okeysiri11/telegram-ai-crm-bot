import { Link } from "react-router-dom";
import { Badge, Card } from "@/ui";
import { PlatformBuilderLayout } from "../layouts/PlatformBuilderLayout";
import { BUILDER_CATALOG } from "../managers/builderRegistry";
import { useIsPlatformOwner } from "../managers/platformOwner";
import { builderDisplayName, term } from "@/i18n/platformGlossary";
import { HUB_CARDS } from "@/ai-builder-studio/studioCatalog";

const STATUS_RU: Record<string, string> = {
  operational: "Работает",
  frame: "Скоро",
  preview: "Превью",
};

export function PlatformBuilderDashboard() {
  const owner = useIsPlatformOwner();
  const builders = BUILDER_CATALOG.filter(
    (b) => b.kind === "builder" || b.kind === "academy" || (b.kind === "god_mode" && owner),
  );

  return (
    <PlatformBuilderLayout
      title="Конструктор платформы"
      subtitle="Создавайте AI, сценарии и модули через понятные мастера — без инженерного шума."
    >
      <div className="pb-hub-grid mb-4" data-testid="platform-builder-hub">
        {HUB_CARDS.map((c) => (
          <Link
            key={c.id}
            to={c.externalRoute || `/platform-builder/builder-studio?section=${c.section}`}
            className="pb-hub-card"
          >
            <span className="pb-hub-icon" aria-hidden>
              {c.icon}
            </span>
            <span className="pb-hub-title">{c.title}</span>
            <span className="pb-hub-detail">{c.detail}</span>
          </Link>
        ))}
      </div>

      <div className="eds-grid eds-grid--dashboard">
        <Card title="Как устроен мастер">
          <p className="eds-type-small">Шаг → Пояснение → Пример → {term("preview")} → {term("create")}</p>
          <Badge tone="success">Готово к демо</Badge>
        </Card>
        <Card title="Академия">
          <p className="eds-type-small">Быстрый старт · Обучение · Эксперт</p>
          <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/academy">
            Открыть академию
          </Link>
        </Card>
        <Card title="Владелец платформы">
          <p className="eds-type-small">
            {owner
              ? "Режим владельца доступен — полный доступ к конструкторам."
              : "Полный доступ к конструкторам — у владельца и разработчика."}
          </p>
        </Card>
        <Card title="Центр управления">
          <Link className="eds-type-small text-[var(--eds-primary)]" to="/platform-builder/ops-center">
            Инженерные панели →
          </Link>
        </Card>
      </div>

      <Card title="Все конструкторы">
        <ul className="grid gap-2 md:grid-cols-2">
          {builders.map((b) => (
            <li key={b.id}>
              <Link
                to={b.route}
                className="flex items-center justify-between rounded-md border border-[var(--eds-border)] p-3 eds-type-small transition hover:border-[var(--eds-primary)]"
              >
                <span>{builderDisplayName(b.id, b.name)}</span>
                <Badge>{STATUS_RU[b.status] || b.status}</Badge>
              </Link>
            </li>
          ))}
        </ul>
      </Card>
    </PlatformBuilderLayout>
  );
}
