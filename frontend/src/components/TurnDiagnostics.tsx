import type { DebateTurnResponse } from "../types/api";

interface TurnDiagnosticsProps {
  turn: DebateTurnResponse | null;
}

function asPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function TurnDiagnostics({ turn }: TurnDiagnosticsProps) {
  if (!turn) {
    return (
      <section className="border border-fortress-line bg-fortress-panel p-4">
        <h2 className="text-sm uppercase tracking-[0.24em] text-fortress-muted">Verdict Diagnostics</h2>
        <p className="mt-3 text-sm leading-6 text-fortress-muted">
          The evaluator has not judged a turn yet.
        </p>
      </section>
    );
  }

  return (
    <section className="border border-fortress-line bg-fortress-panel p-4">
      <h2 className="text-sm uppercase tracking-[0.24em] text-fortress-muted">Verdict Diagnostics</h2>
      <div className="mt-4 grid gap-3 text-sm text-fortress-text sm:grid-cols-2">
        <div>
          <p className="text-fortress-muted">Verdict</p>
          <p className="mt-1 font-display text-xl capitalize">{turn.evaluator.verdict.replace("_", " ")}</p>
        </div>
        <div>
          <p className="text-fortress-muted">Confidence</p>
          <p className="mt-1 font-display text-xl">{asPercent(turn.evaluator.confidence)}</p>
        </div>
        <div>
          <p className="text-fortress-muted">Evaluator Source</p>
          <p className="mt-1 uppercase tracking-[0.18em]">{turn.evaluator_source ?? "unknown"}</p>
        </div>
        <div>
          <p className="text-fortress-muted">Persona Source</p>
          <p className="mt-1 uppercase tracking-[0.18em]">{turn.persona_source ?? "unknown"}</p>
        </div>
      </div>

      <p className="mt-4 break-words text-sm leading-6 text-fortress-text">
        {turn.evaluator.reasoning_summary}
      </p>

      {turn.evaluator.identified_principles.length > 0 ? (
        <div className="mt-4">
          <p className="text-xs uppercase tracking-[0.2em] text-fortress-muted">Identified Principles</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {turn.evaluator.identified_principles.map((principle) => (
              <span key={principle} className="border border-fortress-line px-2 py-1 text-xs text-fortress-text">
                {principle}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
