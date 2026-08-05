export function Avatar({ name }: { name: string }) {
  const initials = name.slice(0, 2).toUpperCase();
  return (
    <div
      className="flex h-9 w-9 items-center justify-center rounded-[var(--eds-radius-full)] bg-[var(--eds-primary-soft)] text-xs font-semibold text-[var(--eds-primary)]"
      aria-hidden={false}
      title={name}
    >
      {initials}
    </div>
  );
}
