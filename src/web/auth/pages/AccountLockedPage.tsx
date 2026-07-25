import { AuthLink, AuthShell } from "../components/AuthShell";

export function AccountLockedPage() {
  return (
    <AuthShell title="Account locked" subtitle="Too many failed attempts. Contact an administrator or wait for unlock." footer={<AuthLink to="/login">Back to login</AuthLink>}>
      <p className="eds-type-body text-[var(--eds-warning)]">Security lockout is active for this identity.</p>
    </AuthShell>
  );
}
