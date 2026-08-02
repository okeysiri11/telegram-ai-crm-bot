import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Input } from "@/ui";
import { cn } from "@/utils/cn";
import { commandPaletteEngine } from "../managers/commandPalette";
import { omniboxEngine, navigationIndex } from "../managers/omnibox";
import { smartSuggestions } from "../managers/suggestions";
import { contextEngine } from "../managers/contextEngine";
import {
  buildPaletteSections,
  searchPaletteCommands,
} from "@/command-center-runtime/paletteSections";
import { commandFavorites, commandRecent } from "@/command-center-runtime/commandFavorites";
import { commandRuntime } from "@/runtime/commandRuntime";
import type { CommandItem } from "../types";
import { matchAiNavigationIntent, useExperienceModeStore } from "@/ux-revolution";

type Mode = "palette" | "omnibox" | "ai" | "commands";

type Props = {
  open: boolean;
  onClose: () => void;
  initialMode?: Mode;
};

type Row = { key: string; label: string; meta: string; section?: string; run: () => void };

async function runCommand(c: CommandItem, navigate: (path: string) => void, onClose: () => void) {
  commandRuntime.setSurface("palette");
  commandRuntime.bindNavigator(navigate);
  commandRecent.push(c.id);
  const res = await commandRuntime.execute(c.action ?? c.id);
  if (res.route) navigate(res.route);
  else if (c.route) navigate(c.route);
  onClose();
}

/**
 * Sprint 27.5 — VS Code–style Command Palette.
 * Sections: Recent · Favorites · Open module · Create · AI · Developer.
 */
export function UniversalCommandPalette({ open, onClose, initialMode = "palette" }: Props) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [mode, setMode] = useState<Mode>(initialMode);
  const navigate = useNavigate();

  const suggestions = useMemo(() => smartSuggestions.list(6), [open]);
  const commands = useMemo(() => commandPaletteEngine.search(query), [query]);
  const hits = useMemo(() => omniboxEngine.search(query, 10), [query]);
  const sections = useMemo(() => (open && !query ? buildPaletteSections() : []), [open, query]);
  const sectionSearch = useMemo(() => (query ? searchPaletteCommands(query) : []), [query]);

  const rows: Row[] = useMemo(() => {
    if (mode === "ai") return [];
    if (mode === "omnibox") {
      return hits.map((h) => ({
        key: h.id,
        label: `${h.type}: ${h.title}`,
        meta: `${h.score}`,
        run: () => {
          navigationIndex.recordUse(h.id);
          commandRecent.push(h.id);
          if (h.route) {
            contextEngine.pushPage(h.route);
            navigate(h.route);
          }
          onClose();
        },
      }));
    }

    if (mode === "palette" && !query) {
      const out: Row[] = [];
      for (const section of sections) {
        for (const c of section.items) {
          out.push({
            key: `${section.id}:${c.id}`,
            label: c.label,
            meta: section.label,
            section: section.label,
            run: () => {
              void runCommand(c, navigate, onClose);
            },
          });
        }
      }
      return out;
    }

    if (mode === "palette" && query) {
      return sectionSearch.map((c) => ({
        key: c.id,
        label: c.label,
        meta: c.kind,
        run: () => {
          void runCommand(c, navigate, onClose);
        },
      }));
    }

    type RowSource = { id: string; label: string; kind?: string; route?: string; action?: string };
    let list: RowSource[] = [];
    if (mode === "commands") {
      list = [
        ...commands.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
        ...sectionSearch.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
      ];
    } else if (query) {
      list = [
        ...sectionSearch.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
        ...commands.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
        ...hits.map((h) => ({ id: h.id, label: h.title, kind: h.type, route: h.route, action: h.action ?? h.id })),
      ];
    } else {
      list = [
        ...suggestions.map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
        ...commands.slice(0, 8).map((c) => ({ id: c.id, label: c.label, kind: c.kind, route: c.route, action: c.action })),
      ];
    }
    const seen = new Set<string>();
    return list
      .filter((c) => {
        if (seen.has(c.id)) return false;
        seen.add(c.id);
        return true;
      })
      .map((c) => ({
        key: c.id,
        label: c.label,
        meta: c.kind ?? "command",
        run: () => {
          void (async () => {
            const intent = matchAiNavigationIntent(c.label) || (c.id.startsWith("ai_intent_") ? matchAiNavigationIntent(query) : null);
            if (intent?.requiresPro) {
              useExperienceModeStore.getState().setMode("pro");
            }
            commandRuntime.setSurface("palette");
            commandRuntime.bindNavigator(navigate);
            commandRecent.push(c.id);
            const res = await commandRuntime.execute(c.action ?? c.id);
            const route = res.route || c.route || intent?.route;
            if (route) navigate(route);
            onClose();
          })();
        },
      }));
  }, [mode, query, commands, hits, suggestions, navigate, onClose, sections, sectionSearch]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setActive(0);
      setMode(initialMode);
      return;
    }
    commandRuntime.setSurface("palette");
    commandRuntime.bindNavigator(navigate);
    commandRuntime.startup();
  }, [open, initialMode, navigate]);

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
      if (metaFavorite(e) && rows[active]) {
        e.preventDefault();
        const id = rows[active]!.key.includes(":") ? rows[active]!.key.split(":")[1]! : rows[active]!.key;
        commandFavorites.toggle(id);
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        if (mode === "ai") {
          const intent = matchAiNavigationIntent(query);
          if (intent) {
            if (intent.requiresPro) useExperienceModeStore.getState().setMode("pro");
            if (intent.route) navigate(intent.route);
            onClose();
            return;
          }
          void commandRuntime.routeAiIntent(query).then((result) => {
            if (result.route) navigate(result.route);
            onClose();
          });
          return;
        }
        rows[active]?.run();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, rows, active, mode, query, navigate, onClose]);

  if (!open) return null;

  let lastSection = "";

  return (
    <div
      className="fixed inset-0 z-[var(--eds-z-modal,50)] flex items-start justify-center bg-black/40 p-4 pt-[10vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Universal command palette"
    >
      <div className="w-full max-w-2xl overflow-hidden rounded-[var(--eds-radius-lg)] bg-[var(--eds-surface)] shadow-[var(--eds-shadow-lg)] edm-overlay-panel">
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
                ? "Спросите AI: открыть CRM, создать счёт, сводка…"
                : mode === "omnibox"
                  ? "Поиск: CRM, ERP, Знания, Агенты, Процессы…"
                  : "Команда или поиск… (⌘/Ctrl+K)"
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
            rows.map((row, i) => {
              const showSection = Boolean(row.section && row.section !== lastSection);
              if (row.section) lastSection = row.section;
              return (
                <div key={row.key}>
                  {showSection ? (
                    <p className="px-3 pt-2 pb-1 eds-type-caption uppercase tracking-wide text-[var(--eds-text-muted)]">
                      {row.section}
                    </p>
                  ) : null}
                  <button
                    type="button"
                    role="option"
                    aria-selected={i === active}
                    className={cn(
                      "edm-palette-item flex w-full items-center justify-between rounded-md px-3 py-2 text-left eds-type-small",
                      i === active
                        ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]"
                        : "hover:bg-[var(--eds-primary-soft)]/50",
                    )}
                    onMouseEnter={() => setActive(i)}
                    onClick={() => row.run()}
                  >
                    <span>{row.label}</span>
                    <span className="eds-type-caption">{row.meta}</span>
                  </button>
                </div>
              );
            })
          )}
          {!rows.length && mode !== "ai" ? (
            <div className="px-3 py-4">
              <div className="eds-empty-art" aria-hidden>
                ◇
              </div>
              <p className="mt-2 eds-type-small text-[var(--eds-text-muted)]">Nothing found</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    navigate("/platform-builder/mission-control");
                    onClose();
                  }}
                >
                  Mission Control
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => {
                    navigate("/dashboard");
                    onClose();
                  }}
                >
                  Dashboard
                </Button>
              </div>
            </div>
          ) : null}
        </div>
        <div className="flex justify-between border-t border-[var(--eds-border)] px-3 py-2 eds-type-caption text-[var(--eds-text-muted)]">
          <span>↑↓ · Tab modes · Enter · ⌘B favorite · Esc</span>
          <span>Enterprise Command Center</span>
        </div>
      </div>
    </div>
  );
}

function metaFavorite(e: KeyboardEvent): boolean {
  return (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "b";
}
