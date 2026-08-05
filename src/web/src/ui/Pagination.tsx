import { Button } from "./Button";

type Props = { page: number; pages: number; onChange: (p: number) => void };

export function Pagination({ page, pages, onChange }: Props) {
  return (
    <div className="eds-toolbar">
      <Button size="sm" variant="secondary" toolbar disabled={page <= 1} onClick={() => onChange(page - 1)}>
        Prev
      </Button>
      <span className="eds-type-helper">
        {page} / {pages}
      </span>
      <Button size="sm" variant="secondary" toolbar disabled={page >= pages} onClick={() => onChange(page + 1)}>
        Next
      </Button>
    </div>
  );
}
