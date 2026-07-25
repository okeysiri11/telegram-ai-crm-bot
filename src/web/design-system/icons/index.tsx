import type { ComponentType, ReactNode } from "react";

type IconProps = { size?: number; className?: string };

function Base({ size = 20, className = "", children }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function IconNavigation(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 6h16M4 12h16M4 18h10" />
    </Base>
  );
}
export function IconAI(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 3l2 6h6l-5 4 2 6-5-4-5 4 2-6-5-4h6z" />
    </Base>
  );
}
export function IconCRM(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M16 11a4 4 0 10-8 0 4 4 0 008 0zM4 20a8 8 0 0116 0" />
    </Base>
  );
}
export function IconERP(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 19V5h6v14H4zm10-8h6v8h-6v-8z" />
    </Base>
  );
}
export function IconFinance(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 3v18M7 8h8a3 3 0 010 6H9a3 3 0 000 6h9" />
    </Base>
  );
}
export function IconHR(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M8 14a4 4 0 118 0M5 20a7 7 0 0114 0M12 7a2 2 0 100-4 2 2 0 000 4z" />
    </Base>
  );
}
export function IconAnalytics(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 19V9m6 10V5m6 14v-7m4 7H2" />
    </Base>
  );
}
export function IconNotifications(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M6 16v-5a6 6 0 1112 0v5l2 2H4l2-2zm4 4h4" />
    </Base>
  );
}
export function IconSecurity(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 3l8 4v5c0 5-3.5 8-8 9-4.5-1-8-4-8-9V7l8-4z" />
    </Base>
  );
}
export function IconSettings(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v2m0 16v2m10-10h-2M4 12H2m15.07-7.07l-1.41 1.41M8.34 15.66l-1.41 1.41m0-12.72l1.41 1.41m7.32 7.32l1.41 1.41" />
    </Base>
  );
}
export function IconWorkflow(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M6 6h4v4H6V6zm8 0h4v4h-4V6zM6 14h4v4H6v-4zm8 2h4m-8-6h4" />
    </Base>
  );
}

export const iconLibrary = {
  navigation: IconNavigation,
  ai: IconAI,
  crm: IconCRM,
  erp: IconERP,
  finance: IconFinance,
  hr: IconHR,
  analytics: IconAnalytics,
  notifications: IconNotifications,
  security: IconSecurity,
  settings: IconSettings,
  workflow: IconWorkflow,
} as const;

export type IconName = keyof typeof iconLibrary;

export function Icon({ name, size = 20, className }: { name: IconName; size?: number; className?: string }) {
  const Cmp = iconLibrary[name] as ComponentType<IconProps>;
  return <Cmp size={size} className={className} />;
}
