export function RoomSkeleton() {
  return (
    <div className="op-skeleton" data-testid="room-skeleton" role="status" aria-live="polite">
      <span className="op-skeleton-glow" aria-hidden />
      <p>Загрузка зала…</p>
    </div>
  );
}
