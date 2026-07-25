import { AuthLink, AuthShell } from "../components/AuthShell";
import { Button } from "@/ui";
import { useNavigate } from "react-router-dom";

export function SessionExpiredPage() {
  const navigate = useNavigate();
  return (
    <AuthShell title="Session expired" subtitle="Please sign in again to continue." footer={<AuthLink to="/login">Login</AuthLink>}>
      <Button className="w-full" onClick={() => navigate("/login")}>Re-authenticate</Button>
    </AuthShell>
  );
}
