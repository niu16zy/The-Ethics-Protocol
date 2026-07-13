import type { EvidenceRef } from "../types/api";

interface EvidencePanelProps {
  retrievedRefs: EvidenceRef[];
  evaluatorRefs: EvidenceRef[];
}

function formatScore(score?: number | null): string {
  if (score === null || score === undefined) {
    return "score unavailable";
  }

  return `score ${score.toFixed(3)}`;
}

export function EvidencePanel({ retrievedRefs, evaluatorRefs }: EvidencePanelProps) {
  const hasEvidence = retrievedRefs.length > 0;

  return (
    <section className="border border-fortress-line bg-fortress-ink p-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <h2 className="text-sm uppercase tracking-[0.24em] text-fortress-muted">Traceable Evidence</h2>
        <span className="text-xs text-fortress-muted">
          Evaluator refs: {evaluatorRefs.length}
        </span>
      </div>

      {!hasEvidence ? (
        <p className="mt-4 text-sm leading-6 text-fortress-muted">
          No retrieved course evidence yet. Submit a grounded argument to test it against the knowledge base.
        </p>
      ) : (
        <div className="mt-4 grid gap-3">
          {retrievedRefs.map((ref) => (
            <article key={`${ref.document_id}-${ref.seq_order ?? "x"}`} className="border border-fortress-line bg-fortress-black p-3">
              <div className="flex flex-col gap-1 text-xs text-fortress-muted sm:flex-row sm:flex-wrap sm:items-center sm:gap-3">
                <span>doc #{ref.document_id}</span>
                <span>{ref.lesson ?? "lesson unknown"}</span>
                <span>{ref.topic ?? "topic unknown"}</span>
                <span>{formatScore(ref.score)}</span>
              </div>
              <p className="mt-2 break-words text-sm leading-6 text-fortress-text">{ref.excerpt}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
