import { Button } from "@/ui";
import { useNavigate } from "react-router-dom";
import { quickActions } from "../managers";
import { useEffect } from "react";

export function QuickActionsBar() {
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.metaKey || e.ctrlKey) || e.shiftKey || e.altKey) return;
      const action = quickActions.byShortcut(e.key);
      if (action) {
        e.preventDefault();
        navigate(action.path);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navigate]);

  return (
    <div className="flex flex-wrap gap-2">
      {quickActions.actions.map((a) => (
        <Button key={a.id} size="sm" variant="secondary" onClick={() => navigate(a.path)} title={`⌘/Ctrl+${a.shortcut.toUpperCase()}`}>
          {a.label}
        </Button>
      ))}
    </div>
  );
}
