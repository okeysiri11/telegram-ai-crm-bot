import { useNavigate } from "react-router-dom";
import { Card } from "@/ui";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";
import { getVertical } from "@/vertical-workspace/catalog";
import { MOBILE_VERTICAL_HUB } from "./mobileWorkspace";

export function MobileWorkspaceCards({ heading = "Рабочие пространства" }: { heading?: string }) {
  const navigate = useNavigate();
  const setVerticalId = useVerticalWorkspaceStore((s) => s.setVerticalId);
  const unread = useNotificationStore((s) => s.items.filter((i) => !i.read).length);

  function open(id: string, href: string) {
    setVerticalId(id);
    navigate(href);
  }

  return (
    <section>
      <h2 className="mb-2 font-semibold">{heading}</h2>
      <div className="ados-mobile-hub">
        {MOBILE_VERTICAL_HUB.map((item) => {
          const purpose = getVertical(item.id)?.purpose;
          return (
            <button
              key={item.id}
              type="button"
              className="ados-mobile-hub__card"
              data-testid={`mobile-hub-${item.id}`}
              onClick={() => open(item.id, item.href)}
            >
              <span className="ados-mobile-hub__icon" aria-hidden>
                {item.icon}
              </span>
              <span className="ados-mobile-hub__name">{item.label}</span>
              {purpose ? <span className="ados-mobile-hub__status">{purpose}</span> : null}
              {unread > 0 && item.id === "crm" ? <span className="ados-mobile-hub__badge">{unread}</span> : null}
            </button>
          );
        })}
      </div>
    </section>
  );
}

export function MobileWorkspaceHub() {
  const orgLabel = useOrgSelector((s) => s.label());

  return (
    <div className="ados-mobile-home" data-testid="mobile-workspace-hub">
      <Card>
        <p className="eds-type-caption text-[var(--eds-text-muted)]">Организация</p>
        <h1 className="text-2xl font-semibold">{orgLabel}</h1>
        <p className="mt-1 eds-type-body">Выберите рабочее пространство</p>
      </Card>
      <MobileWorkspaceCards />
    </div>
  );
}
