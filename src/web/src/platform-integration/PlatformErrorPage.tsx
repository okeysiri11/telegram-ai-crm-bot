/**
 * Sprint 30.6 — Unified platform error pages (404 / 403 / 500 / Offline / Unauthorized).
 */

import { Link } from "react-router-dom";
import { EmptyLayout } from "@/layouts/EmptyLayout";
import { Button } from "@/ui";

export type PlatformErrorKind = "404" | "403" | "500" | "offline" | "unauthorized";

const COPY: Record<
  PlatformErrorKind,
  { title: string; titleRu: string; body: string; code: string }
> = {
  "404": {
    title: "Not Found",
    titleRu: "Страница не найдена",
    body: "Маршрут недоступен или устарел.",
    code: "404",
  },
  "403": {
    title: "Forbidden",
    titleRu: "Доступ запрещён",
    body: "Недостаточно прав для этого ресурса (RBAC).",
    code: "403",
  },
  "500": {
    title: "Server Error",
    titleRu: "Ошибка сервера",
    body: "Внутренняя ошибка. Повторите попытку или вернитесь на дашборд.",
    code: "500",
  },
  offline: {
    title: "Offline",
    titleRu: "Нет сети",
    body: "Соединение потеряно. Проверьте сеть — OfflineBanner восстановит синхронизацию.",
    code: "OFFLINE",
  },
  unauthorized: {
    title: "Unauthorized",
    titleRu: "Требуется вход",
    body: "Сессия отсутствует или истекла. Войдите снова.",
    code: "401",
  },
};

export function PlatformErrorPage({ kind = "404" }: { kind?: PlatformErrorKind }) {
  const c = COPY[kind];
  const primary =
    kind === "unauthorized" || kind === "403"
      ? { to: "/login", label: "Войти" }
      : { to: "/dashboard", label: "Дашборд" };

  return (
    <EmptyLayout>
      <div className="mx-auto max-w-lg p-8" role="alert" data-testid={`platform-error-${kind}`}>
        <p className="eds-type-caption uppercase tracking-[0.14em] text-[var(--eds-text-muted)]">
          Platform Error · {c.code}
        </p>
        <h1 className="eds-type-h1 mt-2">{c.titleRu}</h1>
        <p className="eds-type-helper mt-1">{c.title}</p>
        <p className="eds-type-body mt-3">{c.body}</p>
        <div className="mt-6 flex flex-wrap gap-2">
          <Link to={primary.to}>
            <Button>{primary.label}</Button>
          </Link>
          <Link to="/">
            <Button variant="secondary">Главная</Button>
          </Link>
          <Link to="/health">
            <Button variant="ghost">Здоровье платформы</Button>
          </Link>
          {kind === "offline" ? (
            <Button variant="ghost" onClick={() => window.location.reload()}>
              Обновить
            </Button>
          ) : null}
        </div>
      </div>
    </EmptyLayout>
  );
}
