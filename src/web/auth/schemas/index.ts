import { z } from "zod";

export const loginSchema = z.object({
  identifier: z.string().min(2, "Email or username required"),
  password: z.string().min(4, "Password too short"),
  rememberMe: z.boolean().default(false),
  tenantId: z.string().min(2),
  language: z.enum(["en", "ru", "uk"]).default("en"),
});

export const forgotPasswordSchema = z.object({
  email: z.string().email(),
});

export const resetPasswordSchema = z.object({
  token: z.string().min(6),
  password: z.string().min(8),
  confirmPassword: z.string().min(8),
}).refine((d) => d.password === d.confirmPassword, { message: "Passwords must match", path: ["confirmPassword"] });

export const changePasswordSchema = z.object({
  currentPassword: z.string().min(4),
  newPassword: z.string().min(8),
  confirmPassword: z.string().min(8),
}).refine((d) => d.newPassword === d.confirmPassword, { message: "Passwords must match", path: ["confirmPassword"] });

export const mfaTotpSchema = z.object({
  code: z.string().regex(/^\d{6}$/, "Enter 6-digit TOTP"),
});

export const mfaEmailSchema = z.object({
  code: z.string().min(4).max(8),
});

export const mfaBackupSchema = z.object({
  backupCode: z.string().min(8),
});

export const inviteUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
  roleId: z.string().min(2),
  organizationId: z.string().min(2),
});

export type LoginForm = z.infer<typeof loginSchema>;
export type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;
export type ChangePasswordForm = z.infer<typeof changePasswordSchema>;
