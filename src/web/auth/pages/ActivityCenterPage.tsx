import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Card } from "@/ui";
import { activityCenter } from "../managers";

export function ActivityCenterPage() {
  const entries = activityCenter.list();
  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">Activity Center</h1>
        <Card title="History">
          <ul className="space-y-2">
            {entries.map((e) => (
              <li key={e.id} className="border-b border-[var(--eds-border)] py-2 eds-type-small">
                <strong>{e.kind}</strong> — {e.summary}
                <div className="eds-type-caption">{e.at}</div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </DashboardLayout>
  );
}
