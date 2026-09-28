export function LevelTrack({
  current,
  target,
}: {
  current: string;
  target: string;
}) {
  const steps = ["L1", "L2", "L3", "L4", "L5"];
  const currentIndex = steps.indexOf(current);
  const targetIndex = steps.indexOf(target);

  return (
    <div className="flex items-center gap-1" aria-label={`Now ${current}, goal ${target}`}>
      {steps.map((step, index) => {
        const reached = currentIndex >= index && currentIndex >= 0;
        const goal = !reached && targetIndex >= index && targetIndex >= 0;
        return (
          <div key={step} className="flex min-w-0 flex-1 flex-col items-center gap-1">
            <div
              className={`h-2 w-full rounded-full ${
                reached ? "bg-secondary" : goal ? "bg-primary/25" : "bg-muted"
              }`}
            />
            <span className={`text-[10px] ${reached ? "font-semibold text-foreground" : "text-muted-foreground"}`}>
              {step}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function ReadinessChart({
  items,
}: {
  items: { label: string; percent: number }[];
}) {
  const max = 100;
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex justify-between text-sm">
            <span className="font-medium">{item.label}</span>
            <span className="tabular-nums text-muted-foreground">{item.percent}%</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary"
              style={{ width: `${Math.max(0, Math.min(max, item.percent))}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
