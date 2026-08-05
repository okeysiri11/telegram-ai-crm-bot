/**
 * Sprint 32.0 — Brand Kit panel.
 */

import { useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { useProductionStore } from "./productionStore";

export function BrandKitPanel() {
  const brandKit = useProductionStore((s) => s.brandKit);
  const updateBrandKit = useProductionStore((s) => s.updateBrandKit);
  const [kit, setKit] = useState(() => brandKit());

  function save() {
    setKit(updateBrandKit(kit));
  }

  return (
    <Card title="Enterprise Brand Kit" status={<Badge tone="success">live</Badge>} data-testid="brand-kit-panel">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="eds-type-small">
          Название
          <Input value={kit.name} onChange={(e) => setKit({ ...kit, name: e.target.value })} />
        </label>
        <label className="eds-type-small">
          Типографика
          <Input value={kit.typography} onChange={(e) => setKit({ ...kit, typography: e.target.value })} />
        </label>
        <label className="eds-type-small">
          Primary
          <Input value={kit.primaryColor} onChange={(e) => setKit({ ...kit, primaryColor: e.target.value })} />
        </label>
        <label className="eds-type-small">
          Accent
          <Input value={kit.accentColor} onChange={(e) => setKit({ ...kit, accentColor: e.target.value })} />
        </label>
        <label className="eds-type-small sm:col-span-2">
          Voice
          <Input value={kit.voice} onChange={(e) => setKit({ ...kit, voice: e.target.value })} />
        </label>
        <label className="eds-type-small sm:col-span-2">
          Writing style
          <Input value={kit.writingStyle} onChange={(e) => setKit({ ...kit, writingStyle: e.target.value })} />
        </label>
        <label className="eds-type-small sm:col-span-2">
          Visual style
          <Input value={kit.visualStyle} onChange={(e) => setKit({ ...kit, visualStyle: e.target.value })} />
        </label>
        <label className="eds-type-small sm:col-span-2">
          Allowed models (comma)
          <Input
            value={kit.allowedModels.join(", ")}
            onChange={(e) =>
              setKit({
                ...kit,
                allowedModels: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
              })
            }
          />
        </label>
        <label className="eds-type-small sm:col-span-2">
          Default AI providers (comma)
          <Input
            value={kit.defaultProviders.join(", ")}
            onChange={(e) =>
              setKit({
                ...kit,
                defaultProviders: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
              })
            }
          />
        </label>
      </div>
      <div className="mt-3 flex gap-2">
        <Button size="sm" onClick={save}>
          Сохранить Brand Kit
        </Button>
        <span className="eds-type-helper self-center">обновлено {new Date(kit.updatedAt).toLocaleString()}</span>
      </div>
    </Card>
  );
}
