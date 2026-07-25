import { Button } from "./Button";

type Props = { page: number; pages: number; onChange: (p: number) => void };

export function Pagination({ page, pages, onChange }: Props) {
  return (
    <div className="flex items-center gap-2">
      <Button size="sm" variant="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>Prev</Button>
      <span className="text-sm text-[var(--ew-muted)]">{page} / {pages}</span>
      <Button size="sm" variant="secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</Button>
    </div>
  );
}
