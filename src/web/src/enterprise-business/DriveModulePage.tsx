/**
 * Sprint 30.8 — Enterprise Drive (documents hub): browser, upload meta, preview, categories, search, recent.
 */

import { useMemo, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Badge, Button, Card, Input } from "@/ui";
import { BusinessModuleShell } from "./BusinessModuleShell";
import { loadJson, saveJson, newId } from "./persist";

export type DriveFile = {
  id: string;
  name: string;
  category: string;
  mime: string;
  size: number;
  preview: string;
  updatedAt: string;
};

type DriveState = { files: DriveFile[] };

function read(): DriveState {
  return loadJson("drive", { files: [] });
}
function write(s: DriveState) {
  saveJson("drive", s);
}

const TABS = [
  { id: "browser", label: "Файлы" },
  { id: "upload", label: "Загрузка" },
  { id: "preview", label: "Превью" },
  { id: "categories", label: "Категории" },
  { id: "search", label: "Поиск" },
  { id: "recent", label: "Недавние" },
] as const;

export function DriveModulePage() {
  const [params, setParams] = useSearchParams();
  const view = params.get("view") || "browser";
  const [state, setState] = useState(read);
  const [selected, setSelected] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("general");
  const active = TABS.some((t) => t.id === view) ? view : "browser";

  function setTab(id: string) {
    setParams((p) => {
      const n = new URLSearchParams(p);
      n.set("view", id);
      return n;
    });
  }

  const files = useMemo(() => {
    let list = [...state.files];
    if (active === "recent") {
      list = list.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)).slice(0, 20);
    }
    if (active === "search" || q.trim()) {
      const needle = q.trim().toLowerCase();
      if (needle) list = list.filter((f) => f.name.toLowerCase().includes(needle) || f.category.toLowerCase().includes(needle));
    }
    return list;
  }, [state.files, active, q]);

  const categories = useMemo(() => [...new Set(state.files.map((f) => f.category))], [state.files]);
  const current = state.files.find((f) => f.id === selected) || state.files[0];

  function registerFile(fileName: string, cat: string, preview: string) {
    const f: DriveFile = {
      id: newId("file"),
      name: fileName,
      category: cat,
      mime: fileName.endsWith(".pdf") ? "application/pdf" : "text/plain",
      size: preview.length,
      preview,
      updatedAt: new Date().toISOString(),
    };
    const next = { files: [f, ...state.files] };
    write(next);
    setState(next);
    setSelected(f.id);
  }

  return (
    <BusinessModuleShell
      title="Документы · Drive"
      subtitle="Файлы · загрузка · превью · категории · поиск"
      tabs={[...TABS]}
      activeTab={active}
      onTab={setTab}
      source="Workspace · EKP documents"
      testId="drive-module"
      actions={
        <Link to="/knowledge?view=docs">
          <Button size="sm" variant="ghost">
            Знания
          </Button>
        </Link>
      }
    >
      {active === "upload" ? (
        <Card title="Регистрация файла">
          <div className="flex flex-wrap gap-2">
            <Input placeholder="Имя файла" value={name} onChange={(e) => setName(e.target.value)} />
            <Input placeholder="Категория" value={category} onChange={(e) => setCategory(e.target.value)} />
            <Button
              size="sm"
              onClick={() => {
                if (!name.trim()) return;
                registerFile(name.trim(), category.trim() || "general", `Превью: ${name.trim()}`);
                setName("");
              }}
            >
              Загрузить метаданные
            </Button>
            <input
              type="file"
              className="eds-type-small"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = () => {
                  const text = typeof reader.result === "string" ? reader.result.slice(0, 2000) : file.name;
                  registerFile(file.name, category || "uploads", text);
                };
                reader.readAsText(file);
              }}
            />
          </div>
        </Card>
      ) : null}

      {active === "preview" && current ? (
        <Card title={current.name} status={<Badge>{current.mime}</Badge>}>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap eds-type-small">{current.preview}</pre>
        </Card>
      ) : null}

      {active === "categories" ? (
        <div className="flex flex-wrap gap-2">
          {categories.map((c) => (
            <Badge key={c}>{c}</Badge>
          ))}
        </div>
      ) : null}

      {active === "search" ? (
        <Input placeholder="Поиск файлов…" value={q} onChange={(e) => setQ(e.target.value)} />
      ) : null}

      {(active === "browser" || active === "recent" || active === "search" || active === "upload") && (
        <ul className="mt-3 space-y-2">
          {files.map((f) => (
            <li key={f.id}>
              <button
                type="button"
                className="w-full rounded-md border border-[var(--eds-border)] px-3 py-2 text-left eds-type-small hover:border-[var(--eds-primary)]"
                onClick={() => {
                  setSelected(f.id);
                  setTab("preview");
                }}
              >
                <strong>{f.name}</strong>
                <span className="eds-type-helper"> · {f.category} · {f.size} B</span>
              </button>
            </li>
          ))}
          {!files.length ? <li className="eds-type-helper">Нет файлов</li> : null}
        </ul>
      )}
    </BusinessModuleShell>
  );
}

export function countDriveFiles(): number {
  return read().files.length;
}
