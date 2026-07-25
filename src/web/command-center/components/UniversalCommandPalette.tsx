import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/ui";
import { cn } from "@/utils/cn";
import { commandPaletteEngine } from "../managers/commandPalette";
import { omniboxEngine, navigationIndex } from "../managers/omnibox";
import { smartSuggestions } from "../managers/suggestions";
import { actionExecutor } from "../managers/security";
import { aiCommandCenter } from "../managers/aiCommands";
import { commandAnalytics } from "../managers/analytics";
import { contextEngine } from "../managers/contextEngine";

type Mode = "palette" | "omnibox" | "ai" | "commands";

type Props = {
  open: boolean;
  onClose: () => void;
  initialMode?: Mode;
};

export function UniversalCommandPalette({ open, onClose, initialMode = "palette" }: Props) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [mode, setMode] = useState<Mode>(initialMode);
  const navigate = useNavigate();

  const suggestions = useMemo(() => smartSuggestions.list(6), [open]);
  const commands = useMemo(() => commandPaletteEngine.search(query), [query]);
  const hits = useMemo(() => omniboxEngine.search(query, 10), [query]);

  const rows = useMemo(() => {
    type Row = { key: string; label: string; meta: string; run: () => void };
    if (mode === "ai") return [] as Row[];
    if (mode === "omnibox") {
      return hits.map((h) => ({
        key: h.id,
        label: `${h.type}: ${h.title}`,
        meta: `${h.score}`,
        run: () => {
          navigationIndex.recordUse(h.id);
          if (h.route) {
            contextEngine.pushPage(h.route);
            navigate(h.route);
          }
          onClose();
        },
      }));
    }
    type RowSource = { id: string; label: string; kind?: string; route?: string; action?: string };
    let list: RowSource[] = [];
    if (mode === "commands") {
      list = commands.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action }));
    } else if (query) {
      list = [
        ...commands.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
        ...hits.map((h) => ({ id: h.id, label: h.title, kind: h.type, route: h.route, action: h.action ?? h.id })),
      ];
    } else {
      list = [
        ...suggestions.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
        ...commands.slice(0, 8).map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
      ];
    }
    return list.map((c) => ({
      key: c.id,
      label: c.label,
      meta: c.kind ?? "command",
      run: () => {
        const t0 = performance.now();
        const res = actionExecutor.execute(c.action ?? c.id);
        commandAnalytics.track(c.id, res.ok, performance.now() - t0);
        if (res.route) navigate(res.route);
        else if (c.route) navigate(c.route);
        onClose();
      },
    }));
  }, [mode, query, commands, hits, suggestions, navigate, onClose]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setActive(0);
      setMode(initialMode);
    }
  }, [open, initialMode]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActive((i) => Math.min(i + 1, Math.max(rows.length - 1, 0)));
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActive((i) => Math.max(i - 1, 0));
      }
      if (e.key === "Tab") {
        e.preventDefault();
        const modes: Mode[] = ["palette", "omnibox", "commands", "ai"];
        const idx = modes.indexOf(mode);
        setMode(modes[e.shiftKey ? (idx + modes.length - 1) % modes.length : (idx + 1) % modes.length]!);
        setActive(0);
      }
      if (e.key === "Enter") {
        e.preventDefault();
        if (mode === "ai") {
          const result = aiCommandCenter.interpret(query);
          commandAnalytics.track(result.intent ?? "ai", result.ok, 1, true);
          if (result.route) {
            contextEngine.pushPage(result.route);
            navigate(result.route);
            onClose();
          }
          return;
        }
        rows[active]?.run();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, rows, active, mode, query, navigate, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[var(--eds-z-modal,50)] flex items-start justify-center bg-black/40 p-4 pt-[10vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Universal command palette"
    >
      <div className="w-full max-w-2xl overflow-hidden rounded-[var(--eds-radius-lg)] bg-[var(--eds-surface)] shadow-[var(--eds-shadow-lg)] eds-anim-scale">
        <div className="flex items-center gap-2 border-b border-[var(--eds-border)] px-3 pt-3">
          {(["palette", "omnibox", "commands", "ai"] as Mode[]).map((m) => (
            <button
              key={m}
              type="button"
              className={cn(
                "rounded-md px-2 py-1 eds-type-caption capitalize",
                mode === m ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "text-[var(--eds-text-muted)]",
              )}
              onClick={() => {
                setMode(m);
                setActive(0);
              }}
            >
              {m}
            </button>
          ))}
        </div>
        <div className="border-b border-[var(--eds-border)] p-3">
          <Input
            autoFocus
            className="eds-focus-ring"
            placeholder={
              mode === "ai"
                ? "Ask AI to open CRM, create invoice, summarize workspace…"
                : mode === "omnibox"
                  ? "Search CRM, ERP, Knowledge, Agents, Workflows…"
                  : "Type a command or search… (⌘/Ctrl+K)"
            }
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
            aria-label="Command input"
          />
        </div>
        <div className="max-h-96 overflow-auto p-2" role="listbox">
          {mode === "ai" ? (
            <p className="px-3 py-2 eds-type-small text-[var(--eds-text-muted)]">
              Press Enter to execute AI command. Context: {contextEngine.get().workspace} / {contextEngine.get().role}
            </p>
          ) : (
            rows.map((row, i) => (
              <button
                key={row.key}
                type="button"
                role="option"
                aria-selected={i === active}
                className={cn(
                  "flex w-full items-center justify-between rounded-md px-3 py-2 text-left eds-type-small eds-anim-fade",
                  i === active ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]" : "hover:bg-[var(--eds-primary-soft)]/50",
                )}
                onMouseEnter={() => setActive(i)}
                onClick={() => row.run()}
              >
                <span>{row.label}</span>
                <span className="eds-type-caption">{row.meta}</span>
              </button>
            ))
          )}
          {!rows.length && mode !== "ai" ? (
            <p className="px-3 py-4 eds-type-small text-[var(--eds-text-muted)]">No matches</p>
          ) : null}
        </div>
        <div className="flex justify-between border-t border-[var(--eds-border)] px-3 py-2 eds-type-caption text-[var(--eds-text-muted)]">
          <span>↑↓ navigate · Tab modes · Enter run · Esc close</span>
          <span>Zero-latency · fuzzy · RBAC</span>
        </div>
      </div>
    </div>
  );
}
