import { Button } from "@/ui";

export function BuilderStepNav({
  steps,
  current,
  onChange,
}: {
  steps: readonly string[];
  current: number;
  onChange: (index: number) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {steps.map((step, i) => (
        <Button
          key={step}
          variant={i === current ? "primary" : "ghost"}
          onClick={() => onChange(i)}
        >
          {i + 1}. {step}
        </Button>
      ))}
    </div>
  );
}
