/**
 * Sprint 49.0/49.1 — shared business cabinet shell (RU ops UI).
 * Search / status filter / sort / pagination; honest empty states.
 */

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Badge, Button, Card, Input, Table, Skeleton } from "@/ui";
import { Pagination } from "@/ui/Pagination";
import { EmptyState } from "@/ui/EmptyState";
import { WorkspaceLayout } from "@/layouts/WorkspaceLayout";
import { cn } from "@/utils/cn";
import { useOpsCabinetNavStore } from "@/shell/mobile";
import { useIsMobile } from "@/shell/mobile/useIsMobile";
import { useVerticalWorkspaceStore } from "@/vertical-workspace/verticalWorkspaceStore";

export type OpsNavItem = { id: string; label: string; hidden?: boolean; href?: string };

export type OpsColumn = { key: string; label: string };

export type OpsRow = Record<string, string | number | null | undefined>;

export type OpsSection = {
  id: string;
  title: string;
  description: string;
  columns: OpsColumn[];
  rows: OpsRow[];
  quickActions?: { label: string; onClick?: () => void; to?: string }[];
  integrationNote?: string;
  cards?: { label: string; value: string }[];
  emptyTitle?: string;
  emptyDescription?: string;
  emptyCtaLabel?: string;
  emptyCtaOnClick?: () => void;
  statusFilterKey?: string;
  responsibleFilterKey?: string;
  dateFilterKey?: string;
  panel?: React.ReactNode;
  rowActions?: (row: OpsRow) => React.ReactNode;
  onRowOpen?: (row: OpsRow) => void;
  thumbKey?: string;
};

export type BusinessCabinetProps = {
  verticalId: string;
  title: string;
  subtitle: string;
  nav: OpsNavItem[];
  sections: Record<string, OpsSection>;
  defaultSection?: string;
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onBootstrap?: () => void;
  bootstrapLabel?: string;
  testId?: string;
  roleHint?: string;
  banner?: ReactNode;
  headerExtra?: ReactNode;
};

const PAGE_SIZE_DESKTOP = 8;
const PAGE_SIZE_MOBILE = 12;

export function BusinessCabinetShell({
  verticalId,
  title,
  subtitle,
  nav,
  sections,
  defaultSection = "home",
  loading,
  error,
  onRefresh,
  onBootstrap,
  bootstrapLabel,
  testId,
  roleHint,
  banner,
  headerExtra,
}: BusinessCabinetProps) {
  const { sub } = useParams<{ sub?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [params, setParams] = useSearchParams();
  const sectionId = params.get("view") || sub || defaultSection;
  const section = sections[sectionId] || sections[defaultSection] || Object.values(sections)[0];

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [responsible, setResponsible] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [sortKey, setSortKey] = useState("");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [online, setOnline] = useState(() => (typeof navigator === "undefined" ? true : navigator.onLine));
  const isMobile = useIsMobile();
  const pageSize = isMobile ? PAGE_SIZE_MOBILE : PAGE_SIZE_DESKTOP;

  useEffect(() => {
    const items = nav
      .filter((item) => !item.hidden)
      .map((item) => ({
        id: item.id,
        label: item.label,
        href: item.href || (item.id === defaultSection ? `/workspace/${verticalId}` : `/workspace/${verticalId}?view=${item.id}`),
      }));
    useOpsCabinetNavStore.getState().register({
      verticalId,
      title,
      roleHint,
      items,
    });
    useVerticalWorkspaceStore.getState().setVerticalId(verticalId);
    return () => useOpsCabinetNavStore.getState().clear();
  }, [nav, verticalId, title, roleHint, defaultSection]);

  useEffect(() => {
    if (sub && !params.get("view") && Object.prototype.hasOwnProperty.call(sections, sub)) {
      const next = new URLSearchParams(params);
      next.set("view", sub);
      setParams(next, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sub]);

  useEffect(() => {
    setQ("");
    setStatus("");
    setResponsible("");
    setDateFrom("");
    setPage(1);
    setSortKey("");
  }, [sectionId]);

  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  function go(id: string) {
    const item = nav.find((entry) => entry.id === id);
    if (item?.href) {
      navigate(item.href);
      return;
    }
    const next = new URLSearchParams(params);
    if (id === defaultSection) next.delete("view");
    else next.set("view", id);
    next.delete("id");
    setParams(next);
  }

  function isNavActive(item: OpsNavItem) {
    if (item.href) {
      const [path, query] = item.href.split("?");
      if (item.id === "projects") {
        return location.pathname.startsWith(`/workspace/${verticalId}/projects`);
      }
      if (query) {
        const view = new URLSearchParams(query).get("view");
        return location.pathname === path && (params.get("view") || sub) === view;
      }
      return location.pathname === path && !params.get("view") && !sub;
    }
    return sectionId === item.id;
  }

  const statusOptions = useMemo(() => {
    if (!section?.statusFilterKey) return [];
    const key = section.statusFilterKey;
    return [...new Set(section.rows.map((r) => String(r[key] ?? "")).filter(Boolean))];
  }, [section]);

  const responsibleOptions = useMemo(() => {
    if (!section?.responsibleFilterKey) return [];
    const key = section.responsibleFilterKey;
    return [...new Set(section.rows.map((r) => String(r[key] ?? "")).filter(Boolean))];
  }, [section]);

  const filtered = useMemo(() => {
    if (!section) return [];
    let rows = [...section.rows];
    const needle = q.trim().toLowerCase();
    if (needle) {
      rows = rows.filter((r) =>
        Object.values(r).some((v) => String(v ?? "").toLowerCase().includes(needle)),
      );
    }
    if (status && section.statusFilterKey) {
      rows = rows.filter((r) => String(r[section.statusFilterKey!] ?? "") === status);
    }
    if (responsible && section.responsibleFilterKey) {
      rows = rows.filter((r) => String(r[section.responsibleFilterKey!] ?? "") === responsible);
    }
    if (dateFrom && section.dateFilterKey) {
      rows = rows.filter((r) => String(r[section.dateFilterKey!] ?? "").startsWith(dateFrom));
    }
    if (sortKey) {
      rows.sort((a, b) => {
        const av = String(a[sortKey] ?? "");
        const bv = String(b[sortKey] ?? "");
        const cmp = av.localeCompare(bv, "ru", { numeric: true });
        return sortDir === "asc" ? cmp : -cmp;
      });
    }
    return rows;
  }, [section, q, status, responsible, dateFrom, sortKey, sortDir]);

  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageRows = isMobile
    ? filtered.slice(0, page * pageSize)
    : filtered.slice((page - 1) * pageSize, page * pageSize);
  const hasMore = isMobile && pageRows.length < filtered.length;

  return (
    <WorkspaceLayout>
      <div
        className="biz-cabinet grid gap-4 lg:grid-cols-[14rem_minmax(0,1fr)]"
        data-testid={testId || `biz-cabinet-${verticalId}`}
        data-vertical={verticalId}
      >
        <div className="hidden md:block lg:hidden">
          <Button
            size="sm"
            variant="secondary"
            aria-label="Открыть разделы"
            data-testid="ops-mobile-nav-toggle"
            onClick={() => setMobileNavOpen(true)}
          >
            Разделы
          </Button>
        </div>
        {mobileNavOpen ? (
          <button
            type="button"
            aria-label="Закрыть разделы"
            className="fixed inset-0 z-30 bg-black/40 lg:hidden"
            onClick={() => setMobileNavOpen(false)}
          />
        ) : null}
        <aside
          className={cn(
            "rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-3",
            mobileNavOpen
              ? "fixed inset-y-0 left-0 z-40 w-[min(18rem,calc(100vw-2rem))] overflow-y-auto shadow-lg lg:static lg:z-auto lg:w-auto lg:shadow-none"
              : "hidden lg:block",
          )}
          data-testid="ops-side-nav"
        >
          <p className="eds-type-caption text-[var(--eds-text-muted)]">Рабочее пространство</p>
          <h1 className="eds-type-section mt-1">{title}</h1>
          <p className="eds-type-helper mt-1 text-[var(--eds-text-muted)]">{subtitle}</p>
          {roleHint ? (
            <p className="mt-1 eds-type-caption text-[var(--eds-text-muted)]">Роль: {roleHint}</p>
          ) : null}
          <nav className="mt-3 flex flex-col gap-1" aria-label="Разделы">
            {nav
              .filter((item) => !item.hidden)
              .map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={cn(
                    "rounded-md px-2 py-1.5 text-left eds-type-small",
                    sectionId === item.id || isNavActive(item)
                      ? "bg-[var(--eds-primary-soft)] text-[var(--eds-primary)]"
                      : "hover:bg-[var(--eds-primary-soft)]/40",
                  )}
                  onClick={() => {
                    go(item.id);
                    setMobileNavOpen(false);
                  }}
                >
                  {item.label}
                </button>
              ))}
          </nav>
          <div className="mt-4 flex flex-col gap-2">
            {onRefresh ? (
              <Button size="sm" variant="secondary" onClick={onRefresh} disabled={loading}>
                Обновить
              </Button>
            ) : null}
            {onBootstrap ? (
              <Button size="sm" variant="secondary" onClick={onBootstrap} disabled={loading}>
                {bootstrapLabel || "Загрузить демо-данные"}
              </Button>
            ) : null}
            <Link to={`/vertical/${verticalId}`} className="eds-type-caption text-[var(--eds-primary)]">
              ← Обзор вертикали
            </Link>
          </div>
        </aside>

        <main className="min-w-0 space-y-4">
          {banner ? (
            <div
              className="rounded-lg border border-[var(--ew-danger,#b91c1c)] bg-[var(--eds-danger-soft,#fef2f2)] p-3"
              data-testid="agro-demo-banner"
            >
              {banner}
            </div>
          ) : null}
          <header className="rounded-lg border border-[var(--ew-border)] bg-[var(--eds-surface)] p-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <h2 className="eds-type-title text-xl">{section?.title}</h2>
                <p className="mt-1 eds-type-body text-[var(--eds-text-muted)]">{section?.description}</p>
              </div>
              <div className="flex items-center gap-2">
                {headerExtra}
                {loading ? <Badge>Загрузка…</Badge> : null}
              </div>
            </div>
            {section?.quickActions?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {section.quickActions.map((a) =>
                  a.to ? (
                    <Link key={a.label} to={a.to}>
                      <Button size="sm" className="ews-primary-cta">
                        {a.label}
                      </Button>
                    </Link>
                  ) : (
                    <Button key={a.label} size="sm" variant="secondary" onClick={a.onClick}>
                      {a.label}
                    </Button>
                  ),
                )}
              </div>
            ) : null}
            {section?.integrationNote ? (
              <p className="mt-3 eds-type-caption text-[var(--eds-text-muted)]">
                {section.integrationNote}
              </p>
            ) : null}
          </header>

          {error ? (
            <Card title="Ошибка" data-testid="ops-error-state">
              <p className="eds-type-body text-[var(--eds-danger,#b91c1c)]">{error}</p>
              {!online ? <p className="mt-1 eds-type-helper">Нет сети. Проверьте соединение.</p> : null}
              {onRefresh ? (
                <Button className="mt-3" variant="secondary" onClick={onRefresh} data-testid="ops-retry">
                  Повторить
                </Button>
              ) : null}
            </Card>
          ) : null}

          {loading && !error ? (
            <div className="ados-mobile-card" data-testid="ops-skeleton">
              <Skeleton rows={5} height="2.5rem" />
            </div>
          ) : null}

          {section?.cards?.length ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {section.cards.map((c) => (
                <Card key={c.label} title={c.label}>
                  <p className="eds-type-title text-2xl">{c.value}</p>
                </Card>
              ))}
            </div>
          ) : null}

          {section?.panel ? <div data-testid={`ops-panel-${section.id}`}>{section.panel}</div> : null}

          {section && section.columns.length > 0 ? (
            <Card title={section.title}>
              <div className="mb-3 flex flex-wrap gap-2" data-testid="ops-table-controls">
                <Input
                  placeholder="Поиск…"
                  aria-label="Поиск"
                  className="max-w-sm"
                  value={q}
                  onChange={(e) => {
                    setQ(e.target.value);
                    setPage(1);
                  }}
                />
                {section.statusFilterKey ? (
                  <select
                    aria-label="Фильтр статуса"
                    className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small"
                    value={status}
                    onChange={(e) => {
                      setStatus(e.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="">Все статусы</option>
                    {statusOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                ) : null}
                {section.responsibleFilterKey ? (
                  <select
                    aria-label="Фильтр ответственного"
                    className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small"
                    value={responsible}
                    onChange={(e) => {
                      setResponsible(e.target.value);
                      setPage(1);
                    }}
                  >
                    <option value="">Все ответственные</option>
                    {responsibleOptions.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                ) : null}
                {section.dateFilterKey ? (
                  <Input
                    type="date"
                    aria-label="Фильтр даты"
                    className="max-w-[10rem]"
                    value={dateFrom}
                    onChange={(e) => {
                      setDateFrom(e.target.value);
                      setPage(1);
                    }}
                  />
                ) : null}
                <select
                  aria-label="Сортировка"
                  className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small"
                  value={sortKey}
                  onChange={(e) => setSortKey(e.target.value)}
                >
                  <option value="">Без сортировки</option>
                  {section.columns.map((c) => (
                    <option key={c.key} value={c.key}>
                      {c.label}
                    </option>
                  ))}
                </select>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setSortDir((d) => (d === "asc" ? "desc" : "asc"))}
                >
                  {sortDir === "asc" ? "↑" : "↓"}
                </Button>
              </div>

              {filtered.length === 0 ? (
                <div className="space-y-3">
                  <EmptyState
                    title={section.emptyTitle || "Пока нет записей"}
                    description={
                      section.emptyDescription ||
                      "Нет операционных данных. Создайте первую запись или загрузите демо-данные."
                    }
                  />
                  {section.emptyCtaOnClick ? (
                    <Button size="sm" className="ews-primary-cta" onClick={section.emptyCtaOnClick}>
                      {section.emptyCtaLabel || "Создать первую запись"}
                    </Button>
                  ) : null}
                </div>
              ) : (
                <>
                  <div className="ados-ops-cards" data-testid="ops-mobile-cards">
                    {pageRows.map((row, i) => (
                      <article
                        key={String(row.id ?? i)}
                        className="ados-mobile-card"
                        role={section.onRowOpen ? "button" : undefined}
                        tabIndex={section.onRowOpen ? 0 : undefined}
                        onClick={() => section.onRowOpen?.(row)}
                        onKeyDown={(e) => {
                          if (section.onRowOpen && (e.key === "Enter" || e.key === " ")) {
                            e.preventDefault();
                            section.onRowOpen(row);
                          }
                        }}
                      >
                        {section.thumbKey && row[section.thumbKey] ? (
                          <img
                            src={String(row[section.thumbKey])}
                            alt=""
                            className="ados-mobile-thumb"
                            loading="lazy"
                            width={72}
                            height={48}
                          />
                        ) : null}
                        <h3 className="font-semibold">
                          {String(
                            row.title ??
                              row[section.columns.find((c) => c.key !== "photo" && c.key !== "thumb")?.key || "id"] ??
                              "Запись",
                          )}
                        </h3>
                        <dl className="mt-2">
                          {section.columns
                            .filter((col) => col.key !== "photo" && col.key !== "thumb" && col.key !== "title")
                            .slice(0, 3)
                            .map((col) => (
                            <div key={col.key}>
                              <dt>{col.label}</dt>
                              <dd>{row[col.key] ?? "—"}</dd>
                            </div>
                          ))}
                        </dl>
                        {section.rowActions ? (
                          <div className="mt-2" onClick={(e) => e.stopPropagation()}>
                            {section.rowActions(row)}
                          </div>
                        ) : null}
                      </article>
                    ))}
                  </div>
                  <Table
                    className="eds-table-wrap--wide hidden md:block"
                    headers={[...section.columns.map((c) => c.label), ...(section.rowActions ? ["Действия"] : [])]}
                  >
                    {pageRows.map((row, i) => (
                      <tr key={String(row.id ?? i)}>
                        {section.columns.map((col) => (
                          <td key={col.key}>{row[col.key] ?? "—"}</td>
                        ))}
                        {section.rowActions ? <td>{section.rowActions(row)}</td> : null}
                      </tr>
                    ))}
                  </Table>
                  <div className="mt-3">
                  {isMobile ? (
                    hasMore ? (
                      <Button
                        className="w-full"
                        variant="secondary"
                        data-testid="ops-load-more"
                        onClick={() => setPage((p) => p + 1)}
                      >
                        Показать ещё
                      </Button>
                    ) : null
                  ) : (
                    <Pagination page={page} pages={pages} onChange={setPage} />
                  )}
                  </div>
                </>
              )}
            </Card>
          ) : null}
        </main>
      </div>
    </WorkspaceLayout>
  );
}
