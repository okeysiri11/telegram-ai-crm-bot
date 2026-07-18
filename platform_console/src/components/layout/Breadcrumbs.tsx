import { Link, useLocation } from 'react-router-dom';

const LABELS: Record<string, string> = {
  '/': 'Dashboard',
  '/requests': 'Requests',
  '/managers': 'Managers',
  '/workflows': 'Workflows',
  '/configuration': 'Configuration',
  '/audit': 'Audit',
  '/jobs': 'Jobs',
  '/integrations': 'Integrations',
  '/observability': 'Observability',
  '/system': 'System',
  '/settings': 'Settings',
};

export function Breadcrumbs() {
  const { pathname } = useLocation();
  const label = LABELS[pathname] || pathname.slice(1);

  return (
    <nav className="mb-4 text-sm text-[var(--color-muted)]">
      <Link to="/" className="hover:text-[var(--color-accent)]">
        Home
      </Link>
      {pathname !== '/' && (
        <>
          <span className="mx-2">/</span>
          <span className="text-[var(--color-text)]">{label}</span>
        </>
      )}
    </nav>
  );
}
