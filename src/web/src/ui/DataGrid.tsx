import { Table } from "./Table";

type Row = Record<string, string | number>;

export function DataGrid({ columns, rows }: { columns: string[]; rows: Row[] }) {
  return (
    <Table headers={columns}>
      {rows.map((row, idx) => (
        <tr key={idx} className="border-t border-[var(--ew-border)]">
          {columns.map((col) => (
            <td key={col} className="px-3 py-2">{row[col]}</td>
          ))}
        </tr>
      ))}
    </Table>
  );
}
