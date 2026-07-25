import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Button, Input, Select } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useI18n } from "@/i18n";
import { useWorkspaceStore } from "@/workspace/workspaceStore";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(4),
  tenantId: z.string().min(2),
});

type Form = z.infer<typeof schema>;

export function LoginPage() {
  const t = useI18n((s) => s.t);
  const login = useAuthStore((s) => s.login);
  const setWorkspace = useWorkspaceStore((s) => s.setWorkspace);
  const navigate = useNavigate();
  const { register, handleSubmit, formState } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { email: "owner@demo.corp", password: "demo", tenantId: "demo-corp" },
  });

  return (
    <AuthLayout>
      <h1 className="mb-1 text-2xl font-semibold">{t("app.title")}</h1>
      <p className="mb-6 text-sm text-[var(--ew-muted)]">Multi-tenant sign-in · MFA ready</p>
      <form
        className="space-y-3"
        onSubmit={handleSubmit(async (values) => {
          await login(values.email, values.password, values.tenantId);
          setWorkspace({ company: values.tenantId });
          navigate("/");
        })}
      >
        <div>
          <label className="mb-1 block text-sm">{t("auth.email")}</label>
          <Input type="email" {...register("email")} />
        </div>
        <div>
          <label className="mb-1 block text-sm">{t("auth.password")}</label>
          <Input type="password" {...register("password")} />
        </div>
        <div>
          <label className="mb-1 block text-sm">{t("auth.tenant")}</label>
          <Select {...register("tenantId")}>
            <option value="demo-corp">demo-corp</option>
            <option value="acme-ltd">acme-ltd</option>
          </Select>
        </div>
        <Button className="w-full" type="submit" disabled={formState.isSubmitting}>
          {t("auth.login")}
        </Button>
      </form>
    </AuthLayout>
  );
}
