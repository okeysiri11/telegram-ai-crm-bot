import { Link } from "react-router-dom";
import { Card } from "@/ui";
import { PLATFORM_MANAGEMENT_NAV } from "./mobileWorkspace";

/** Compact owner platform list — never the desktop God Mode surface. */
export function MobilePlatformHome() {
  return (
    <div className="ados-mobile-home" data-testid="mobile-platform-home">
      <Card>
        <p className="eds-type-caption text-[var(--eds-text-muted)]">Режим</p>
        <h1 className="text-2xl font-semibold">Владелец системы</h1>
        <p className="mt-1 eds-type-body">Управление платформой</p>
      </Card>
      <section>
        <h2 className="mb-2 font-semibold">Разделы</h2>
        <div className="flex flex-col gap-2">
          {PLATFORM_MANAGEMENT_NAV.map((item) => (
            <Link key={item.id} to={item.href} className="ados-mobile-card block" data-testid={`mobile-platform-${item.id}`}>
              {item.label}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
