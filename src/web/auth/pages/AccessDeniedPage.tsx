import { AuthLink, AuthShell } from "../components/AuthShell";

export function AccessDeniedPage() {
  return (
    <AuthShell title="Access denied" subtitle="You do not have permission for this resource." footer={<AuthLink to="/">Go home</AuthLink>}>
      <p className="eds-type-body text-[var(--eds-danger)]">RBAC denied this action.</p>
    </AuthShell>
  );
}
