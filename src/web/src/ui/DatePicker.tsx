import { Input } from "./Input";

export function DatePicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return <Input type="date" value={value} onChange={(e) => onChange(e.target.value)} />;
}
