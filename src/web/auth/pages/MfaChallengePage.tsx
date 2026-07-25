import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { z } from "zod";
import { Button, Input } from "@/ui";
import { AuthShell } from "../components/AuthShell";
import { mfaBackupSchema, mfaEmailSchema, mfaTotpSchema } from "../schemas";
import { mfaCenter } from "../managers";

export function MfaChallengePage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<"totp" | "email" | "backup">("totp");
  const totp = useForm<z.infer<typeof mfaTotpSchema>>({ resolver: zodResolver(mfaTotpSchema) });
  const email = useForm<z.infer<typeof mfaEmailSchema>>({ resolver: zodResolver(mfaEmailSchema) });
  const backup = useForm<z.infer<typeof mfaBackupSchema>>({ resolver: zodResolver(mfaBackupSchema) });

  return (
    <AuthShell
      title="Multi-factor authentication"
      subtitle={`Methods: ${mfaCenter.methods.join(", ")} · Extensions ready: ${mfaCenter.extensionsReady.join(", ")}`}
    >
      <div className="mb-4 flex gap-2">
        {(["totp", "email", "backup"] as const).map((k) => (
          <Button key={k} size="sm" variant={tab === k ? "primary" : "secondary"} type="button" onClick={() => setTab(k)}>
            {k}
          </Button>
        ))}
      </div>
      {tab === "totp" ? (
        <form
          className="space-y-3"
          onSubmit={totp.handleSubmit((v) => {
            if (mfaCenter.verifyTotp(v.code)) navigate("/identity");
          })}
        >
          <Input placeholder="6-digit TOTP" className="eds-focus-ring" {...totp.register("code")} />
          <Button className="w-full" type="submit">
            Verify TOTP
          </Button>
        </form>
      ) : null}
      {tab === "email" ? (
        <form
          className="space-y-3"
          onSubmit={email.handleSubmit((v) => {
            if (mfaCenter.verifyEmailCode(v.code)) navigate("/identity");
          })}
        >
          <Input placeholder="Email code" className="eds-focus-ring" {...email.register("code")} />
          <Button className="w-full" type="submit">
            Verify email code
          </Button>
        </form>
      ) : null}
      {tab === "backup" ? (
        <form
          className="space-y-3"
          onSubmit={backup.handleSubmit((v) => {
            if (mfaCenter.verifyBackup(v.backupCode)) navigate("/identity");
          })}
        >
          <Input placeholder="Backup code" className="eds-focus-ring" {...backup.register("backupCode")} />
          <Button className="w-full" type="submit">
            Use backup code
          </Button>
        </form>
      ) : null}
      <p className="mt-4 eds-type-caption">
        Recovery flow ready · FIDO2 / WebAuthn / Hardware keys prepared for extension
      </p>
    </AuthShell>
  );
}
