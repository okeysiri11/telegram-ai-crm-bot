/**
 * Enterprise Policies catalog — Sprint 33.9.
 * Static policy definitions — no new Policy Engine / Store.
 */

export type PolicyDomain =
  | "financial"
  | "security"
  | "legal"
  | "privacy"
  | "hr"
  | "operations"
  | "ai_usage"
  | "automation";

export type PolicySeverity = "low" | "medium" | "high" | "critical";

export type EnterprisePolicy = {
  id: string;
  domain: PolicyDomain;
  label: string;
  summary: string;
  severity: PolicySeverity;
  requiresApproval: boolean;
  permissionHint: string;
  tokens: RegExp;
};

export const ENTERPRISE_POLICIES: EnterprisePolicy[] = [
  {
    id: "pol_fin",
    domain: "financial",
    label: "Financial",
    summary: "Платежи, лимиты, invoice и бюджетные пороги",
    severity: "critical",
    requiresApproval: true,
    permissionHint: "finance.write / admin",
    tokens: /finance|payment|invoice|бюджет|платеж/i,
  },
  {
    id: "pol_sec",
    domain: "security",
    label: "Security",
    summary: "Доступ, секреты, отключение интеграций, privilege changes",
    severity: "critical",
    requiresApproval: true,
    permissionHint: "security.admin / platform_owner",
    tokens: /security|secret|oauth|ключ|disable integration/i,
  },
  {
    id: "pol_legal",
    domain: "legal",
    label: "Legal",
    summary: "Контракты, юридические отправки, claims",
    severity: "high",
    requiresApproval: true,
    permissionHint: "legal.write",
    tokens: /legal|contract|юридич|claim/i,
  },
  {
    id: "pol_privacy",
    domain: "privacy",
    label: "Privacy",
    summary: "PII, retention, экспорт персональных данных",
    severity: "high",
    requiresApproval: true,
    permissionHint: "privacy.officer / admin",
    tokens: /privacy|pii|gdpr|персональ|retention/i,
  },
  {
    id: "pol_hr",
    domain: "hr",
    label: "HR",
    summary: "Кадровые изменения, доступы сотрудников",
    severity: "medium",
    requiresApproval: true,
    permissionHint: "hr.write",
    tokens: /hr|hire|сотрудник|onboard|people/i,
  },
  {
    id: "pol_ops",
    domain: "operations",
    label: "Operations",
    summary: "Операционные изменения Runtime / Workflow",
    severity: "medium",
    requiresApproval: false,
    permissionHint: "ops.write / read",
    tokens: /ops|runtime|queue|workflow|операц/i,
  },
  {
    id: "pol_ai",
    domain: "ai_usage",
    label: "AI Usage",
    summary: "Границы автономии AI, knowledge use, high-risk AI actions",
    severity: "high",
    requiresApproval: true,
    permissionHint: "ai.execute / owner",
    tokens: /ai|concierge|autonomy|specialist|агент/i,
  },
  {
    id: "pol_auto",
    domain: "automation",
    label: "Automation",
    summary: "Массовые автоматизации и unattended runs",
    severity: "medium",
    requiresApproval: true,
    permissionHint: "automation.run",
    tokens: /automat|mass|bulk|unattended|пакетн/i,
  },
];

export function matchPolicy(text: string): EnterprisePolicy {
  return (
    ENTERPRISE_POLICIES.find((p) => p.tokens.test(text)) ||
    ENTERPRISE_POLICIES.find((p) => p.domain === "operations")!
  );
}
