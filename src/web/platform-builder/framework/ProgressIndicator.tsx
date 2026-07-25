export function ProgressIndicator({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
  const pct = Math.round(((current + 1) / Math.max(total, 1)) * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between eds-type-caption text-[var(--eds-text-muted)]">
        <span>
          Step {current + 1} of {total}
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-[var(--eds-border)]">
        <div
          className="h-full rounded-full bg-[var(--eds-primary)] transition-all duration-300 eds-anim-fade"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
