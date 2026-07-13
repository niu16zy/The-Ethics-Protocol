import { useState } from "react";

interface DebateInputProps {
  disabled: boolean;
  onSubmit: (input: string) => void;
}

export function DebateInput({ disabled, onSubmit }: DebateInputProps) {
  const [input, setInput] = useState("");
  const canSubmit = input.trim().length > 0 && !disabled;

  const submit = () => {
    const trimmed = input.trim();
    if (!trimmed || disabled) {
      return;
    }

    onSubmit(trimmed);
    setInput("");
  };

  return (
    <section className="border border-fortress-line bg-fortress-ink p-4">
      <label htmlFor="player-argument" className="text-xs uppercase tracking-[0.24em] text-fortress-muted">
        Your grounded argument
      </label>
      <textarea
        id="player-argument"
        value={input}
        onChange={(event) => setInput(event.target.value)}
        disabled={disabled}
        rows={5}
        maxLength={4000}
        placeholder="Example: A hiring AI can become unfair when biased training data harms applicants, so it needs bias testing, transparency, and accountable human review."
        className="mt-3 w-full resize-y border border-fortress-line bg-fortress-black px-4 py-3 text-base leading-7 text-fortress-text placeholder:text-fortress-muted/70 disabled:cursor-not-allowed disabled:opacity-60"
      />
      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-fortress-muted">{input.length}/4000 characters</p>
        <button
          type="button"
          onClick={submit}
          disabled={!canSubmit}
          className="border border-fortress-amber bg-fortress-amber px-5 py-2 text-sm font-semibold text-fortress-black transition hover:bg-[#efcc74] disabled:cursor-not-allowed disabled:border-fortress-line disabled:bg-fortress-line disabled:text-fortress-muted"
        >
          Submit Argument
        </button>
      </div>
    </section>
  );
}
