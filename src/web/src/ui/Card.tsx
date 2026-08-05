import type { ReactNode } from "react";
import { cn } from "@/utils/cn";

type Props = {
  title?: string;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
  status?: ReactNode;
  loading?: boolean;
  empty?: boolean;
  success?: boolean;
  interactive?: boolean;
  raised?: boolean;
  role?: string;
};

export function Card({
  title,
  children,
  className,
  actions,
  status,
  loading,
  empty,
  success,
  interactive,
  raised,
  role,
}: Props) {
  return (
    <section
      role={role}
      className={cn(
        "eds-card",
        loading && "is-loading",
        empty && "is-empty",
        success && "is-success",
        interactive && "eds-card--interactive",
        raised && "eds-card--raised",
        className,
      )}
      aria-busy={loading || undefined}
    >
      {title || status ? (
        <div className="eds-card__header">
          {title ? <h3 className="eds-card__title">{title}</h3> : <span />}
          {status ? <div className="eds-type-status">{status}</div> : null}
        </div>
      ) : null}
      <div className="eds-card__body">{children}</div>
      {actions ? <div className="eds-card__actions">{actions}</div> : null}
    </section>
  );
}
