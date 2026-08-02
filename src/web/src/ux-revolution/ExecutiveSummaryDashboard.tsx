/**
 * Sprint 33.1 — Executive Summary Dashboard (Simple Mode default home).
 * Presentation-only: uses existing stores + local demo data — no API changes.
 */

import { Link, useNavigate } from "react-router-dom";
import { Badge, Button, Card } from "@/ui";
import { useAuthStore } from "@/auth/authStore";
import { useNotificationStore } from "@/notifications/notificationStore";
import { useNavigationUi } from "../../navigation/components/NavigationProvider";
import { useLiveEnterprise } from "@/live-ops";
import { deriveMorningBrief } from "@/dashboard/deriveMorningBrief";
import "./executiveSummary.css";

type Priority = { id: string; title: string; due: string; href: string; severity: "high" | "med" | "low" };
type Risk = { id: string; title: string; detail: string; href: string };
type Rec = { id: string; title: string; why: string; href: string };
type Meeting = { id: string; title: string; when: string; href: string };
type Kpi = { id: string; label: string; value: string; delta: string; href: string };

const PRIORITIES: Priority[] = [
  { id: "p1", title: "Закрыть 3 просроченных сделки", due: "Сегодня", href: "/crm?view=deals", severity: "high" },
  { id: "p2", title: "Утвердить счёт Q3", due: "Сегодня", href: "/analytics?view=invoices", severity: "high" },
  { id: "p3", title: "Ревью проекта Alpha", due: "Завтра", href: "/projects", severity: "med" },
];

const TASKS = [
  { id: "t1", title: "Подготовить бриф для клиента", href: "/tasks" },
  { id: "t2", title: "Обновить воронку Sales", href: "/crm?view=leads" },
  { id: "t3", title: "Согласовать договор", href: "/documents" },
];

const RISKS: Risk[] = [
  { id: "r1", title: "Кассовый разрыв · 14 дней", detail: "Ожидаемые платежи ниже плана", href: "/analytics" },
  { id: "r2", title: "2 SLA под угрозой", detail: "Производство и поддержка", href: "/projects?view=overdue" },
];

const RECS: Rec[] = [
  { id: "a1", title: "Запустить AI-квалификацию лидов", why: "Снизит нагрузку Sales на 20%", href: "/ai-agents" },
  { id: "a2", title: "Открыть просроченные проекты", why: "3 задачи блокируют релиз", href: "/projects?view=overdue" },
];

const MEETINGS: Meeting[] = [
  { id: "m1", title: "Stand-up · Product", when: "10:00", href: "/calendar" },
  { id: "m2", title: "Клиент · Demo Corp", when: "14:30", href: "/calendar?view=meetings" },
  { id: "m3", title: "Финансовый обзор", when: "16:00", href: "/calendar" },
];

const KPIS: Kpi[] = [
  { id: "k1", label: "Выручка MTD", value: "₽ 4.2M", delta: "+8%", href: "/analytics" },
  { id: "k2", label: "Активные сделки", value: "47", delta: "+3", href: "/crm?view=deals" },
  { id: "k3", label: "NPS", value: "62", delta: "+2", href: "/analytics?view=kpi" },
  { id: "k4", label: "AI coverage", value: "34%", delta: "+5%", href: "/ai-agents" },
];

const ACTIVITY = [
  { id: "x1", text: "Новый лид · Acme Ltd", time: "2 мин" },
  { id: "x2", text: "Документ подписан · Договор #881", time: "18 мин" },
  { id: "x3", text: "AI: рекомендация по воронке", time: "1 ч" },
];

export function ExecutiveSummaryDashboard() {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const { openPalette } = useNavigationUi();
  const notifs = useNotificationStore((s) => s.items.filter((i) => !i.read));
  const { snapshot, busy } = useLiveEnterprise(true);
  const brief = deriveMorningBrief(snapshot, {
    company: user?.tenantId || "ADOS",
    unread: notifs.length,
  });

  const name = user?.displayName || user?.email || "Leader";

  return (
    <div className="ux-exec" data-sprint="33.1">
      <header className="ux-exec__hero">
        <div>
          <p className="ux-exec__eyebrow">Executive Summary · Simple Mode</p>
          <h1 className="ux-exec__title">Доброе утро, {name}</h1>
          <p className="ux-exec__sub">
            {brief.summaryLine || "Приоритеты, риски и рекомендации AI — за 5 минут."}
          </p>
        </div>
        <div className="ux-exec__hero-actions">
          <Button size="sm" variant="secondary" onClick={() => openPalette()}>
            ⌘K Команды
          </Button>
          <Button size="sm" onClick={() => navigate("/ai-agents")}>
            AI-Ассистент
          </Button>
        </div>
      </header>

      <section className="ux-exec__kpis" aria-label="KPI">
        {KPIS.map((k) => (
          <Link key={k.id} to={k.href} className="ux-exec__kpi">
            <span className="ux-exec__kpi-label">{k.label}</span>
            <span className="ux-exec__kpi-value">{k.value}</span>
            <span className="ux-exec__kpi-delta">{k.delta}</span>
          </Link>
        ))}
      </section>

      <div className="ux-exec__grid">
        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Приоритеты на сегодня</h2>
          <ul className="ux-exec__list">
            {PRIORITIES.map((p) => (
              <li key={p.id}>
                <Link to={p.href} className="ux-exec__row">
                  <Badge tone={p.severity === "high" ? "danger" : "default"}>{p.due}</Badge>
                  <span>{p.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Задачи</h2>
          <ul className="ux-exec__list">
            {TASKS.map((t) => (
              <li key={t.id}>
                <Link to={t.href} className="ux-exec__row">
                  {t.title}
                </Link>
              </li>
            ))}
          </ul>
          <Link to="/tasks" className="ux-exec__muted">
            Все задачи →
          </Link>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Риски</h2>
          <ul className="ux-exec__list">
            {RISKS.map((r) => (
              <li key={r.id}>
                <Link to={r.href} className="ux-exec__row ux-exec__row--stack">
                  <strong>{r.title}</strong>
                  <span className="ux-exec__muted">{r.detail}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Рекомендации AI</h2>
          <ul className="ux-exec__list">
            {RECS.map((a) => (
              <li key={a.id}>
                <Link to={a.href} className="ux-exec__row ux-exec__row--stack">
                  <strong>{a.title}</strong>
                  <span className="ux-exec__muted">{a.why}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Уведомления</h2>
          {notifs.length === 0 ? (
            <p className="ux-exec__muted">Нет непрочитанных</p>
          ) : (
            <ul className="ux-exec__list">
              {notifs.slice(0, 5).map((n) => (
                <li key={n.id} className="ux-exec__row">
                  {n.title}
                </li>
              ))}
            </ul>
          )}
          <Link to="/notifications" className="ux-exec__muted">
            Центр уведомлений →
          </Link>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Активность</h2>
          <ul className="ux-exec__list">
            {ACTIVITY.map((a) => (
              <li key={a.id} className="ux-exec__row">
                <span>{a.text}</span>
                <span className="ux-exec__muted">{a.time}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Встречи</h2>
          <ul className="ux-exec__list">
            {MEETINGS.map((m) => (
              <li key={m.id}>
                <Link to={m.href} className="ux-exec__row">
                  <Badge>{m.when}</Badge>
                  <span>{m.title}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>

        <Card className="ux-exec__card">
          <h2 className="ux-exec__h2">Здоровье платформы</h2>
          <p className="ux-exec__muted">
            {busy
              ? "Обновление…"
              : `Здоровье ${brief.healthOk}/${brief.healthTotal} · ${brief.tone === "alert" ? "требует внимания" : "в норме"}`}
          </p>
          <div className="ux-exec__health-actions">
            <Button size="sm" variant="secondary" onClick={() => navigate("/health")}>
              Health
            </Button>
            <Button size="sm" variant="secondary" onClick={() => navigate("/owner")}>
              Owner
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
