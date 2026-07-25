import type { IdentityUser, UserStatus } from "../types";
import { identityManager } from "./identityManager";

let localUsers = identityManager.list();

export const userManager = {
  list(): IdentityUser[] {
    return [...localUsers];
  },
  create(input: Omit<IdentityUser, "userId" | "lastLogin" | "status"> & { status?: UserStatus }): IdentityUser {
    const user: IdentityUser = {
      ...input,
      userId: `usr_${Math.random().toString(36).slice(2, 10)}`,
      status: input.status ?? "invited",
      lastLogin: "",
      avatar: input.avatar || "",
    };
    localUsers = [user, ...localUsers];
    return user;
  },
  edit(userId: string, patch: Partial<IdentityUser>): IdentityUser | undefined {
    localUsers = localUsers.map((u) => (u.userId === userId ? { ...u, ...patch } : u));
    return localUsers.find((u) => u.userId === userId);
  },
  disable(userId: string) {
    return this.edit(userId, { status: "disabled" });
  },
  delete(userId: string) {
    localUsers = localUsers.filter((u) => u.userId !== userId);
  },
  invite(email: string, name: string, company: string): IdentityUser {
    return this.create({
      name,
      email,
      username: email.split("@")[0] || "user",
      company,
      department: "Unassigned",
      position: "Member",
      language: "en",
      timeZone: "UTC",
      avatar: "",
      status: "invited",
    });
  },
  importUsers(rows: IdentityUser[]) {
    localUsers = [...rows, ...localUsers];
    return localUsers.length;
  },
  exportUsers(): IdentityUser[] {
    return this.list();
  },
};
