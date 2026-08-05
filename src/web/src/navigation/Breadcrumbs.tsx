import { Link, useLocation } from "react-router-dom";
import { breadcrumbEngine } from "../../navigation/managers/breadcrumbEngine";
import { navigationHistory } from "../../navigation/managers/navigationHistory";
import { useEffect } from "react";

export function Breadcrumbs() {
  const loc = useLocation();
  const crumbs = breadcrumbEngine.fromPath(loc.pathname);

  useEffect(() => {
    const parts = breadcrumbEngine.fromPath(loc.pathname);
    const last = parts[parts.length - 1];
    if (last) {
      navigationHistory.push({ kind: "page", label: last.label, path: last.path });
    }
  }, [loc.pathname]);

  return (
    <nav className="uws-breadcrumbs flex flex-wrap items-center gap-2 text-xs text-[var(--ew-muted)]" aria-label="Навигационная цепочка">
      {crumbs.map((c, i) => (
        <span key={`${c.path}-${c.level}`} className="inline-flex items-center gap-2">
          {i > 0 ? <span className="uws-crumb-sep" aria-hidden>›</span> : null}
          <Link to={c.path} className="hover:text-[var(--ew-brand)]" title={c.level}>
            {c.label}
          </Link>
        </span>
      ))}
    </nav>
  );
}
