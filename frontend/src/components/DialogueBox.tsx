interface DialogueBoxProps {
  speaker: string;
  text: string;
  isLoading?: boolean;
}

export function DialogueBox({ speaker, text, isLoading = false }: DialogueBoxProps) {
  return (
    <section className="rounded-2xl border border-white/10 bg-white/6 p-5 backdrop-blur-md">
      <p className="text-xs uppercase tracking-[0.24em] text-white/70">{speaker}</p>
      <p className="mt-3 min-h-24 whitespace-pre-wrap break-words font-display text-xl leading-8 text-white/90">
        {isLoading ? "The audit lens is testing your claim against the case record..." : text}
      </p>
    </section>
  );
}
