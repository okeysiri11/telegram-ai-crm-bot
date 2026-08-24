import { Link } from "react-router-dom";
import { Card } from "@/ui";
import { visibleMobileSettings } from "./mobileSettings";

export function MobileSettingsPage() {
  const items = visibleMobileSettings();
  return (
    <div className="ados-mobile-home" data-testid="mobile-settings">
      <Card>
        <h1 className="text-2xl font-semibold">Настройки</h1>
        <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">Только разделы, доступные вашей роли.</p>
      </Card>
      <nav className="flex flex-col gap-2" aria-label="Настройки">
        {items.map((item) => (
          <Link key={item.id} to={item.href} className="ados-mobile-card block" data-testid={`mobile-settings-${item.id}`}>
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
