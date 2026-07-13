interface FortressMeterProps {
  current: number;
  before?: number;
  after?: number;
  delta?: number;
}

export function FortressMeter({ current, before, after, delta }: FortressMeterProps) {
  const bounded = Math.max(0, Math.min(100, current));
  const deltaText = delta === undefined ? "Awaiting first argument" : `${delta >= 0 ? "+" : ""}${delta}`;

  return (
    <section className="border border-fortress-line bg-fortress-panel p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm uppercase tracking-[0.24em] text-fortress-muted">Logic Fortress Meter</h2>
        <span className="font-display text-2xl text-fortress-text">{bounded}</span>
      </div>
      <div className="mt-4 h-4 border border-fortress-line bg-fortress-black">
        <div
          className="h-full bg-gradient-to-r from-fortress-red via-fortress-amber to-fortress-blue transition-[width] duration-500"
          style={{ width: `${bounded}%` }}
        />
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-fortress-muted">
        <span>Before: {before ?? current}</span>
        <span>After: {after ?? current}</span>
        <span>Delta: {deltaText}</span>
      </div>
    </section>
  );
}
