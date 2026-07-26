import { PortalLayout, PortalLinksCard } from "./PortalLayout";

const SHARED = [
  { label: "Workspace home", to: "/workspace" },
  { label: "Mission Control", to: "/platform-builder/mission-control" },
  { label: "Digital Twin", to: "/platform-builder/digital-twin" },
  { label: "Business Ecosystems", to: "/platform-builder/business-ecosystem" },
];

const ECOSYSTEMS = [
  { label: "Automotive", to: "/workspace/auto" },
  { label: "Beauty", to: "/workspace/beauty" },
  { label: "Cafe", to: "/workspace/cafe" },
  { label: "Agriculture", to: "/workspace/agro" },
  { label: "Drone", to: "/workspace/drone" },
  { label: "Legal", to: "/workspace/legal" },
  { label: "Crypto (Bidex)", to: "/workspace/crypto" },
];

export function CustomerPortalPage() {
  return (
    <PortalLayout
      title="Customer Portal"
      subtitle="Shell for customer-facing journeys. Industry modules (Automotive, Beauty, Legal…) extend this surface — they do not fork it."
      audience="customer"
    >
      <PortalLinksCard
        title="Universal modules"
        links={[
          { label: "CRM workspace module", to: "/workspace/crm" },
          { label: "Documents", to: "/workspace/docs" },
          { label: "Knowledge Base", to: "/platform-builder/knowledge" },
          { label: "Automotive workspace", to: "/workspace/auto" },
          ...SHARED,
        ]}
      />
      <PortalLinksCard title="Business ecosystems" links={ECOSYSTEMS} />
    </PortalLayout>
  );
}

export function EmployeePortalPage() {
  return (
    <PortalLayout
      title="Employee Portal"
      subtitle="Shell for internal operators. Binds to RBAC roles; AI tools arrive via platform growth layers."
      audience="employee"
    >
      <PortalLinksCard
        title="Operations"
        links={[
          { label: "CRM", to: "/workspace/crm" },
          { label: "ERP", to: "/workspace/erp" },
          { label: "Workflows", to: "/workspace/workflows/invoice" },
          { label: "AI workspace", to: "/workspace/ai" },
          { label: "Command Center", to: "/command-center" },
          ...SHARED,
        ]}
      />
      <PortalLinksCard title="Business ecosystems" links={ECOSYSTEMS} />
    </PortalLayout>
  );
}

export function OwnerPortalPage() {
  return (
    <PortalLayout
      title="Owner Portal"
      subtitle="Shell for owners and executives. Reuses Strategy, Scorecard, and Mission Control — no parallel executive stack."
      audience="owner"
    >
      <PortalLinksCard
        title="Executive surfaces"
        links={[
          { label: "Mission Control", to: "/platform-builder/mission-control" },
          { label: "Strategy Engine", to: "/platform-builder/strategy" },
          { label: "Twin Intelligence", to: "/platform-builder/twin-intelligence" },
          { label: "Analytics", to: "/workspace/analytics" },
          { label: "Global Command Center", to: "/command-center" },
          ...SHARED,
        ]}
      />
      <PortalLinksCard title="Business ecosystems" links={ECOSYSTEMS} />
    </PortalLayout>
  );
}
