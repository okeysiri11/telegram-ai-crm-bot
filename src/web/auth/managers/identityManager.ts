import type { IdentityUser } from "../types";

const users: IdentityUser[] = [
  {
    userId: "usr_owner",
    name: "Alex Owner",
    avatar: "",
    email: "owner@demo.corp",
    username: "owner",
    company: "demo-corp",
    department: "Executive",
    position: "Owner",
    language: "en",
    timeZone: "UTC",
    status: "active",
    lastLogin: new Date().toISOString(),
  },
  {
    userId: "usr_ops",
    name: "Sam Ops",
    avatar: "",
    email: "ops@demo.corp",
    username: "sam.ops",
    company: "demo-corp",
    department: "Operations",
    position: "Manager",
    language: "ru",
    timeZone: "Europe/Kyiv",
    status: "active",
    lastLogin: new Date(Date.now() - 86400000).toISOString(),
  },
];

export const identityManager = {
  list(): IdentityUser[] {
    return [...users];
  },
  get(userId: string): IdentityUser | undefined {
    return users.find((u) => u.userId === userId);
  },
  byEmail(email: string): IdentityUser | undefined {
    return users.find((u) => u.email.toLowerCase() === email.toLowerCase());
  },
};
