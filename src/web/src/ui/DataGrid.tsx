import { Table } from "./Table";

type Row = Record<string, string | number>;

export function DataGrid({ columns, rows }: { columns: string[]; rows: Row[] }) {
  return (
    <Table
      headers={columns}
      empty={rows.length === 0 ? "No rows yet." : undefined}
    >
      {rows.map((row, idx) => (
        <tr key={idx}>
          {columns.map((col) => (
            <td key={col}>{row[col]}</td>
          ))}
        </tr>
      ))}
    </Table>
  );
}
