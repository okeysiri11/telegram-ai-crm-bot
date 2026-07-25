import { useMemo, useState } from "react";
import { Input, Card } from "@/ui";
import { Link } from "react-router-dom";
import { searchCenter } from "../managers";

export function SearchPanel() {
  const [q, setQ] = useState("");
  const hits = useMemo(() => searchCenter.search(q), [q]);
  return (
    <Card title="Search Center">
      <Input
        className="eds-focus-ring mb-3"
        placeholder="Search modules, users, docs… or >commands"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        aria-label="Global search"
      />
      <ul className="max-h-56 space-y-1 overflow-auto">
        {hits.map((h) => (
          <li key={h.id} className="eds-type-small">
            <Link className="text-[var(--eds-primary)]" to={h.path}>
              {h.category}: {h.label}
            </Link>
          </li>
        ))}
      </ul>
    </Card>
  );
}
