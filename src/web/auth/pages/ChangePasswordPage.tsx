import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Button, Card, Input } from "@/ui";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { changePasswordSchema, type ChangePasswordForm } from "../schemas";

export function ChangePasswordPage() {
  const [ok, setOk] = useState(false);
  const { register, handleSubmit, formState, reset } = useForm<ChangePasswordForm>({
    resolver: zodResolver(changePasswordSchema) as never,
  });
  return (
    <DashboardLayout>
      <div className="mx-auto max-w-lg space-y-4">
        <h1 className="eds-type-h1">Change password</h1>
        <Card title="Update credentials">
          {ok ? <p className="mb-3 text-[var(--eds-success)]">Password updated.</p> : null}
          <form
            className="space-y-3"
            onSubmit={handleSubmit(() => {
              setOk(true);
              reset();
            })}
          >
            <Input type="password" placeholder="Current password" className="eds-focus-ring" {...register("currentPassword")} />
            <Input type="password" placeholder="New password" className="eds-focus-ring" {...register("newPassword")} />
            <Input type="password" placeholder="Confirm password" className="eds-focus-ring" {...register("confirmPassword")} />
            {formState.errors.confirmPassword ? (
              <p className="eds-type-caption text-[var(--eds-danger)]">{formState.errors.confirmPassword.message}</p>
            ) : null}
            <Button type="submit">Save</Button>
          </form>
        </Card>
      </div>
    </DashboardLayout>
  );
}
