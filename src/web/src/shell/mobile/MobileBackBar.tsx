import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/ui";
import { workspaceHomePath } from "./mobileWorkspace";

export function MobileBackBar({
  section,
  workspaceLabel,
  verticalId,
}: {
  section: string | null;
  workspaceLabel: string;
  verticalId: string;
}) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  if (pathname === "/dashboard" && !section) return null;

  const title = section || workspaceLabel;
  const home = workspaceHomePath(verticalId);

  function back() {
    if (section) {
      navigate(home);
      return;
    }
    if (pathname !== "/dashboard") {
      navigate("/dashboard");
      return;
    }
    navigate(-1);
  }

  return (
    <div className="ados-mobile-back" data-testid="mobile-back-bar">
      <Button size="sm" variant="ghost" aria-label="Назад" data-testid="mobile-back" onClick={back}>
        ←
      </Button>
      <div className="min-w-0">
        <p className="ados-mobile-back__title truncate">{title}</p>
        {section ? <p className="ados-mobile-back__sub truncate">{workspaceLabel}</p> : null}
      </div>
    </div>
  );
}
