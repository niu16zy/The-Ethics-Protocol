interface FortressMeterProps {
  current: number;
  before?: number;
  after?: number;
  delta?: number;
}

function meterStateLabel(value: number): string {
  const bounded = Math.max(0, Math.min(100, value));
  if (bounded <= 0) {
    return "Breached";
  }
  if (bounded <= 25) {
    return "Critical";
  }
  if (bounded <= 55) {
    return "Unstable";
  }
  if (bounded <= 80) {
    return "Pressured";
  }
  return "Fortified";
}

export function FortressMeter({ current }: FortressMeterProps) {
  const bounded = Math.max(0, Math.min(100, current));
  const status = meterStateLabel(bounded);

  return (
    <section className="border border-fortress-line bg-fortress-panel p-4">
      <div className="mt-4 h-4 border border-fortress-line bg-fortress-black">
        <div
          className="h-full bg-gradient-to-r from-fortress-red via-fortress-amber to-fortress-blue transition-[width] duration-500"
          style={{ width: `${bounded}%` }}
        />
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-fortress-muted">
        <span>Holding</span>
        <span>Cracking</span>
        <span>Collapse</span>
      </div>
    </section>
  );
}
