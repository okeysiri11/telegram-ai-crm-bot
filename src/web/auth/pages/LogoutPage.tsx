import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/auth/authStore";
import { sessionManager } from "../managers";
import { AuthShell } from "../components/AuthShell";
import { Button } from "@/ui";

export function LogoutPage() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  useEffect(() => {
    sessionManager.logoutCurrent();
    logout();
  }, [logout]);
  return (
    <AuthShell title="Signed out" subtitle="Your session has been closed safely.">
      <Button className="w-full" onClick={() => navigate("/login")}>Return to login</Button>
    </AuthShell>
  );
}
