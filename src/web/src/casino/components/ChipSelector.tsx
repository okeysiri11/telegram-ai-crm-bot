export function ChipSelector({
  value,
  options,
  onChange,
  disabled,
}: {
  value: number;
  options: number[];
  onChange: (n: number) => void;
  disabled?: boolean;
}) {
  return (
    <div className="op-rail" role="group" aria-label="Фишки PLAY">
      {options.map((n) => (
        <button
          key={n}
          type="button"
          className={`op-chip${value === n ? " is-on" : ""}`}
          disabled={disabled}
          aria-pressed={value === n}
          onClick={() => onChange(n)}
        >
          {n >= 1000 ? `${n / 1000}k` : n}
        </button>
      ))}
    </div>
  );
}
