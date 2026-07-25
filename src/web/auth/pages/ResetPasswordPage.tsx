import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { Button, Input } from "@/ui";
import { AuthLink, AuthShell } from "../components/AuthShell";
import { resetPasswordSchema, type ResetPasswordForm } from "../schemas";

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, formState } = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema) as never,
    defaultValues: { token: "", password: "", confirmPassword: "" },
  });
  return (
    <AuthShell title="Reset password" subtitle="Choose a new password." footer={<AuthLink to="/login">Back to login</AuthLink>}>
      <form className="space-y-3" onSubmit={handleSubmit(() => navigate("/login"))}>
        <div>
          <label className="eds-type-label mb-1 block">Reset token</label>
          <Input className="eds-focus-ring" {...register("token")} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">New password</label>
          <Input type="password" className="eds-focus-ring" {...register("password")} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Confirm password</label>
          <Input type="password" className="eds-focus-ring" {...register("confirmPassword")} />
          {formState.errors.confirmPassword ? <p className="eds-type-caption text-[var(--eds-danger)]">{formState.errors.confirmPassword.message}</p> : null}
        </div>
        <Button className="w-full" type="submit">Update password</Button>
      </form>
    </AuthShell>
  );
}
