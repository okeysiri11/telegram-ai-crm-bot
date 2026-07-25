import { DashboardLayout } from "@/layouts/DashboardLayout";
import { Button, Card, Input } from "@/ui";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { inviteUserSchema } from "../schemas";
import { userManager } from "../managers";
import { useState } from "react";
import { z } from "zod";

export function UsersPage() {
  const [users, setUsers] = useState(userManager.list());
  const form = useForm<z.infer<typeof inviteUserSchema>>({
    resolver: zodResolver(inviteUserSchema),
    defaultValues: { email: "", name: "", roleId: "role_org_owner", organizationId: "org_demo" },
  });

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <h1 className="eds-type-h1">User Manager</h1>
        <Card title="Invite user">
          <form
            className="grid gap-2 md:grid-cols-2"
            onSubmit={form.handleSubmit((v) => {
              userManager.invite(v.email, v.name, v.organizationId);
              setUsers(userManager.list());
              form.reset();
            })}
          >
            <Input placeholder="Email" {...form.register("email")} />
            <Input placeholder="Name" {...form.register("name")} />
            <Input placeholder="Role ID" {...form.register("roleId")} />
            <Input placeholder="Organization ID" {...form.register("organizationId")} />
            <Button type="submit">Invite</Button>
            <Button type="button" variant="secondary" onClick={() => { const blob = new Blob([JSON.stringify(userManager.exportUsers(), null, 2)], { type: "application/json" }); const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = "users.json"; a.click(); }}>Export</Button>
          </form>
        </Card>
        <Card title="Users">
          <ul className="space-y-2">
            {users.map((u) => (
              <li key={u.userId} className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--eds-border)] py-2 eds-type-small">
                <span>{u.name} · {u.email} · {u.status} · {u.department}</span>
                <div className="flex gap-2">
                  <Button size="sm" variant="ghost" onClick={() => { userManager.disable(u.userId); setUsers(userManager.list()); }}>Disable</Button>
                  <Button size="sm" variant="danger" onClick={() => { userManager.delete(u.userId); setUsers(userManager.list()); }}>Delete</Button>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </DashboardLayout>
  );
}
