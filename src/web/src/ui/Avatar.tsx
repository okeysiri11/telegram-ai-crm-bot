export function Avatar({ name }: { name: string }) {
  const initials = name.slice(0, 2).toUpperCase();
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--ew-brand-soft)] text-xs font-semibold text-[var(--ew-brand)]">
      {initials}
    </div>
  );
}
