import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button, Input } from "@/ui";
import { AuthLink, AuthShell } from "../components/AuthShell";
import { forgotPasswordSchema, type ForgotPasswordForm } from "../schemas";
import { useState } from "react";

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const { register, handleSubmit, formState } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
  });
  return (
    <AuthShell title="Forgot password" subtitle="We will email a reset link." footer={<AuthLink to="/login">Back to login</AuthLink>}>
      {sent ? (
        <p className="eds-type-body text-[var(--eds-success)]">Reset instructions sent.</p>
      ) : (
        <form className="space-y-3" onSubmit={handleSubmit(() => setSent(true))}>
          <div>
            <label className="eds-type-label mb-1 block">Email</label>
            <Input type="email" className="eds-focus-ring" {...register("email")} />
            {formState.errors.email ? <p className="eds-type-caption text-[var(--eds-danger)]">{formState.errors.email.message}</p> : null}
          </div>
          <Button className="w-full" type="submit">Send reset link</Button>
        </form>
      )}
    </AuthShell>
  );
}
