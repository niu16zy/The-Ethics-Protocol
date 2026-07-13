import { useEffect, useMemo, useState } from "react";
import type { LevelConfig } from "../types/level";

interface IntroSceneProps {
  level: LevelConfig;
  isInitializing: boolean;
  initializationError?: string;
  canEnter: boolean;
  onEnter: () => void;
  onRetryInitialization: () => void;
}

export function IntroScene({
  level,
  isInitializing,
  canEnter,
  onEnter,
}: IntroSceneProps) {
  const introPages = level.introPages?.length ? level.introPages : [level.introText];
  const [pageIndex, setPageIndex] = useState(0);
  const [visibleCount, setVisibleCount] = useState(0);
  const currentText = introPages[pageIndex] ?? level.introText;
  const isLastPage = pageIndex === introPages.length - 1;
  const isComplete = visibleCount >= currentText.length;
  const visibleText = useMemo(
    () => currentText.slice(0, visibleCount),
    [currentText, visibleCount],
  );

  useEffect(() => {
    if (isComplete) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setVisibleCount((count) => Math.min(count + 2, currentText.length));
    }, 34);

    return () => window.clearTimeout(timer);
  }, [currentText.length, isComplete, visibleCount]);

  const handleContinue = () => {
    if (!isComplete) {
      return;
    }

    if (!isLastPage) {
      setPageIndex((index) => index + 1);
      setVisibleCount(0);
      return;
    }

    onEnter();
  };

  const continueDisabled = !isComplete || (isLastPage && (!canEnter || isInitializing));
  const buttonLabel = isLastPage ? "Enter" : "Continue";

  return (
    <main className="min-h-screen overflow-hidden bg-[#090013] px-6 text-white">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center py-8 sm:py-10">
        <div className="flex h-[clamp(17rem,52vh,31rem)] w-full shrink-0 items-end justify-center">
          <div className="intro-rise intro-white-glow w-full max-w-[min(50vh,28rem)] border border-slate-100 bg-[#050510] p-1">
            <img
              src={level.sceneImage ?? ""}
              alt={`${level.title} scene`}
              className="aspect-square w-full object-cover [image-rendering:pixelated]"
            />
          </div>
        </div>

        <div className="mt-8 flex min-h-[16rem] w-full max-w-3xl flex-col items-center text-center font-mono text-sm font-semibold leading-7 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)] sm:mt-9 sm:min-h-[17rem] sm:text-base sm:leading-8">
          <p className="min-h-[10.5rem] whitespace-pre-wrap break-words sm:min-h-36">
            {visibleText}
            <span className="intro-cursor ml-1 inline-block h-4 w-3 translate-y-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.95)] sm:h-5" />
          </p>

          <div className="mt-8 flex h-14 items-center justify-center">
            {isComplete ? (
              <button
                key={pageIndex}
                type="button"
                onClick={handleContinue}
                disabled={continueDisabled}
                className="intro-rise intro-white-glow border border-white px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] text-white transition hover:bg-white hover:text-[#090013] disabled:cursor-not-allowed disabled:opacity-45"
              >
                {buttonLabel}
              </button>
            ) : null}
          </div>
        </div>
      </section>
    </main>
  );
}
