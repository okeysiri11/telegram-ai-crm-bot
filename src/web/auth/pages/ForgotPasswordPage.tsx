import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button, Input } from "@/ui";
import { AuthLink, AuthShell } from "../components/AuthShell";
import { forgotPasswordSchema, type ForgotPasswordForm } from "../schemas";
import { useState } from "react";
import { productionPasswordReset } from "@/auth/identityApi";

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
  });
  return (
    <AuthShell
      title="Восстановить пароль"
      subtitle="Мы отправим инструкции на email"
      footer={<AuthLink to="/login">Назад ко входу</AuthLink>}
    >
      {sent ? (
        <p className="eds-type-body text-[var(--eds-success)]">
          Инструкции по восстановлению отправлены.
        </p>
      ) : (
        <form
          className="space-y-3"
          onSubmit={handleSubmit(async (values) => {
            setError(null);
            try {
              await productionPasswordReset(values.email);
              setSent(true);
            } catch (err) {
              setError(err instanceof Error ? err.message : "Ошибка запроса");
            }
          })}
        >
          <div>
            <label className="eds-type-label mb-1 block">Email</label>
            <Input type="email" className="eds-focus-ring" {...register("email")} />
            {formState.errors.email ? (
              <p className="eds-type-caption text-[var(--eds-danger)]">
                {formState.errors.email.message}
              </p>
            ) : null}
          </div>
          {error ? (
            <p className="eds-type-caption text-[var(--eds-danger)]" role="alert">
              {error}
            </p>
          ) : null}
          <Button className="w-full" type="submit">
            Восстановить пароль
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
