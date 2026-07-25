import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/ui";
import { commandPalette } from "../managers/commandPalette";
import { navigationHistory } from "../managers/navigationHistory";
import { searchProvider } from "../managers/searchProvider";
import { navigationPerformance } from "../performance";
import { cn } from "@/utils/cn";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function CommandPalette({ open, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const navigate = useNavigate();

  const commands = useMemo(() => commandPalette.search(query), [query]);
  const searchHits = useMemo(() => {
    const key = `q:${query}`;
    const cached = navigationPerformance.getCached(key) as ReturnType<typeof searchProvider.search> | null;
    if (cached) return cached;
    const hits = searchProvider.search(query).slice(0, 8);
    navigationPerformance.setCached(key, hits);
    return hits;
  }, [query]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setActive(0);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive((i) => Math.min(i + 1, commands.length + searchHits.length - 1));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive((i) => Math.max(i - 1, 0));
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const cmd = commands[active];
        if (cmd?.route) {
          navigationHistory.push({ kind: "command", label: cmd.label, path: cmd.route });
          navigate(cmd.route);
          onClose();
          return;
        }
        const hit = searchHits[active - commands.length];
        if (hit) {
          navigationHistory.push({ kind: "search", label: query || hit.title, path: hit.path });
          navigate(hit.path);
          onClose();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, commands, searchHits, active, navigate, onClose, query]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[var(--eds-z-modal,50)] flex items-start justify-center bg-black/40 p-4 pt-[12vh]" role="dialog" aria-modal="true" aria-label="Command palette">
      <div className="w-full max-w-xl overflow-hidden rounded-[var(--eds-radius-lg)] bg-[var(--eds-surface)] shadow-[var(--eds-shadow-lg)] eds-anim-scale">
        <div className="border-b border-[var(--eds-border)] p-3">
          <Input
            autoFocus
            className="eds-focus-ring"
            placeholder="Type a command or search… (⌘/Ctrl+K)"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
          />
        </div>
        <div className="max-h-80 overflow-auto p-2">
          <p className="px-2 py-1 eds-type-caption">Commands</p>
          {commands.map((c, i) => (
            <button
              key={c.id}
              type="button"
              className={cn(
                "flex w-full items-center justify-between rounded-md px-3 py-2 text-left eds-type-small",
                i === active ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "hover:bg-[var(--eds-primary-soft)]/50",
              )}
              onMouseEnter={() => setActive(i)}
              onClick={() => {
                if (c.route) {
                  navigationHistory.push({ kind: "command", label: c.label, path: c.route });
                  navigate(c.route);
                  onClose();
                }
              }}
            >
              <span>{c.label}</span>
              <span className="eds-type-caption">{c.kind}</span>
            </button>
          ))}
          <p className="mt-2 px-2 py-1 eds-type-caption">Search</p>
          {searchHits.map((h, i) => {
            const idx = commands.length + i;
            return (
              <button
                key={h.id}
                type="button"
                className={cn(
                  "flex w-full items-center justify-between rounded-md px-3 py-2 text-left eds-type-small",
                  idx === active ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "hover:bg-[var(--eds-primary-soft)]/50",
                )}
                onMouseEnter={() => setActive(idx)}
                onClick={() => {
                  navigationHistory.push({ kind: "search", label: query || h.title, path: h.path });
                  navigate(h.path);
                  onClose();
                }}
              >
                <span>
                  {h.category}: {h.title}
                </span>
                <span className="eds-type-caption">{h.match} · {h.score}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
