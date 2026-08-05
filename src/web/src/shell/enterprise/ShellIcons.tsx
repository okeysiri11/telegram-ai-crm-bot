import type { ShellIconId } from "./enterpriseNav";

/** Lightweight inline icons — no new icon package dependency. */
export function ShellIcon({ id, className = "ews-nav-icon" }: { id: ShellIconId; className?: string }) {
  const common = {
    className,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true as const,
  };

  switch (id) {
    case "dashboard":
      return (
        <svg {...common}>
          <rect x="3" y="3" width="7" height="9" rx="1.5" />
          <rect x="14" y="3" width="7" height="5" rx="1.5" />
          <rect x="14" y="12" width="7" height="9" rx="1.5" />
          <rect x="3" y="16" width="7" height="5" rx="1.5" />
        </svg>
      );
    case "desktop":
      return (
        <svg {...common}>
          <rect x="3" y="4" width="18" height="12" rx="1.5" />
          <path d="M8 20h8M12 16v4" />
        </svg>
      );
    case "crm":
      return (
        <svg {...common}>
          <circle cx="9" cy="8" r="3.5" />
          <path d="M3.5 19c1.2-3.2 3.2-4.5 5.5-4.5S13.3 15.8 14.5 19" />
          <circle cx="17" cy="9" r="2.5" />
          <path d="M15 19c.6-2 1.8-3 3.5-3 .8 0 1.5.2 2.1.6" />
        </svg>
      );
    case "erp":
      return (
        <svg {...common}>
          <path d="M4 20V8l8-4 8 4v12" />
          <path d="M9 20v-6h6v6" />
          <path d="M4 12h16" />
        </svg>
      );
    case "projects":
      return (
        <svg {...common}>
          <path d="M4 7h16v12H4z" />
          <path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          <path d="M4 12h16" />
        </svg>
      );
    case "ai_studio":
      return (
        <svg {...common}>
          <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" />
          <path d="M18 15l.9 2.1L21 18l-2.1.9L18 21l-.9-2.1L15 18l2.1-.9z" />
        </svg>
      );
    case "ai_agents":
      return (
        <svg {...common}>
          <rect x="5" y="8" width="14" height="10" rx="2" />
          <circle cx="9.5" cy="13" r="1.2" fill="currentColor" stroke="none" />
          <circle cx="14.5" cy="13" r="1.2" fill="currentColor" stroke="none" />
          <path d="M12 4v4M9 4h6" />
        </svg>
      );
    case "knowledge":
      return (
        <svg {...common}>
          <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H12v16H6.5A2.5 2.5 0 0 0 4 21.5z" />
          <path d="M20 5.5A2.5 2.5 0 0 0 17.5 3H12v16h5.5a2.5 2.5 0 0 1 2.5 2.5z" />
        </svg>
      );
    case "documents":
      return (
        <svg {...common}>
          <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" />
          <path d="M14 3v5h5M9 13h6M9 17h4" />
        </svg>
      );
    case "analytics":
      return (
        <svg {...common}>
          <path d="M4 19h16" />
          <path d="M7 16V10M12 16V6M17 16v-4" />
        </svg>
      );
    case "marketplace":
      return (
        <svg {...common}>
          <path d="M4 8h16l-1.5 11H5.5z" />
          <path d="M8 8V6a4 4 0 0 1 8 0v2" />
        </svg>
      );
    case "automation":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
        </svg>
      );
    case "integrations":
      return (
        <svg {...common}>
          <path d="M8 12h8" />
          <rect x="2" y="9" width="6" height="6" rx="1.5" />
          <rect x="16" y="9" width="6" height="6" rx="1.5" />
          <path d="M12 8V5a2 2 0 0 1 2-2h2M12 16v3a2 2 0 0 0 2 2h2" />
        </svg>
      );
    case "security":
      return (
        <svg {...common}>
          <path d="M12 3l8 3v6c0 5-3.5 8.5-8 9.5C7.5 20.5 4 17 4 12V6z" />
          <path d="M9.5 12.5l1.8 1.8 3.7-3.8" />
        </svg>
      );
    case "city":
      return (
        <svg {...common}>
          <path d="M3 20h18" />
          <path d="M5 20V10l4-2v12M13 20V6l6-2v16" />
          <path d="M7 13h1M7 16h1M15 10h1M15 13h1M15 16h1" />
        </svg>
      );
    case "settings":
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.1 5.1l1.6 1.6M17.3 17.3l1.6 1.6M18.9 5.1l-1.6 1.6M6.7 17.3l-1.6 1.6" />
        </svg>
      );
    case "builder":
      return (
        <svg {...common}>
          <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9l-3.8 3.8z" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
        </svg>
      );
  }
}
