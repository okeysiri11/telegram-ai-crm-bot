import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { Button, Input } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { AuthLink, AuthShell } from "../components/AuthShell";
import { saveFirstEntry } from "@/onboarding/firstEntryStore";
import { useOrgSelector } from "@/navigation/orgSelectorStore";

const schema = z
  .object({
    name: z.string().min(1),
    email: z.string().email(),
    password: z.string().min(8),
    confirm: z.string().min(8),
    tenantId: z.string().min(1),
  })
  .refine((v) => v.password === v.confirm, { message: "Пароли не совпадают", path: ["confirm"] });

type Form = z.infer<typeof schema>;

export function RegisterPage() {
  const registerUser = useAuthStore((s) => s.register);
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const { register, handleSubmit, formState } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { tenantId: "demo-corp", name: "", email: "", password: "", confirm: "" },
  });

  return (
    <AuthShell
      title="Создать аккаунт"
      subtitle="Регистрация по Email · Google доступен на экране входа"
      footer={<AuthLink to="/login">Уже есть аккаунт? Войти</AuthLink>}
    >
      <form
        className="space-y-3"
        onSubmit={handleSubmit(async (values) => {
          setError(null);
          try {
            await registerUser(values.email, values.password, values.tenantId, values.name);
            useOrgSelector.getState().setOrganization(
              ["demo-corp", "acme-ltd", "bidex"].includes(values.tenantId)
                ? values.tenantId
                : "demo-corp",
            );
            saveFirstEntry({
              completed: false,
              step: "welcome",
              companyName: values.tenantId,
              language: "ru",
            });
            navigate("/onboarding/first-entry", { replace: true });
          } catch (err) {
            setError(err instanceof Error ? err.message : "Ошибка регистрации");
          }
        })}
      >
        <div>
          <label className="eds-type-label mb-1 block">Имя</label>
          <Input {...register("name")} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Email</label>
          <Input type="email" {...register("email")} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Пароль</label>
          <Input type="password" {...register("password")} />
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Повтор пароля</label>
          <Input type="password" {...register("confirm")} />
          {formState.errors.confirm ? (
            <p className="eds-type-caption text-[var(--eds-danger)]">
              {formState.errors.confirm.message}
            </p>
          ) : null}
        </div>
        <div>
          <label className="eds-type-label mb-1 block">Компания</label>
          <Input {...register("tenantId")} />
        </div>
        {error ? (
          <p className="eds-type-caption text-[var(--eds-danger)]" role="alert">
            {error}
          </p>
        ) : null}
        <Button className="w-full" type="submit" disabled={formState.isSubmitting}>
          Создать аккаунт
        </Button>
      </form>
    </AuthShell>
  );
}
