import { Link, useLocation } from "react-router-dom";

export function Breadcrumbs() {
  const loc = useLocation();
  const parts = loc.pathname.split("/").filter(Boolean);
  const crumbs = [{ path: "/", label: "Home" }, ...parts.map((p, i) => ({
    path: "/" + parts.slice(0, i + 1).join("/"),
    label: p,
  }))];
  return (
    <nav className="flex flex-wrap gap-2 text-xs text-[var(--ew-muted)]">
      {crumbs.map((c, i) => (
        <span key={c.path} className="inline-flex items-center gap-2">
          {i > 0 ? <span>/</span> : null}
          <Link to={c.path} className="hover:text-[var(--ew-brand)]">{c.label}</Link>
        </span>
      ))}
    </nav>
  );
}
