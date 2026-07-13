import { useEffect, useMemo, useState } from "react";
import type { LevelConfig } from "../types/level";

interface ResolutionSceneProps {
  level: LevelConfig;
}

export function ResolutionScene({ level }: ResolutionSceneProps) {
  const resolutionPages = level.resolutionPages?.length
    ? level.resolutionPages
    : [level.resolutionText];
  const [pageIndex, setPageIndex] = useState(0);
  const [visibleCount, setVisibleCount] = useState(0);
  const currentText = resolutionPages[pageIndex] ?? level.resolutionText;
  const isLastPage = pageIndex === resolutionPages.length - 1;
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
    if (!isComplete || isLastPage) {
      return;
    }

    setPageIndex((index) => index + 1);
    setVisibleCount(0);
  };

  return (
    <main className="min-h-screen overflow-hidden bg-[#090013] px-6 text-white">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center py-8 sm:py-10">
        <div className="flex h-[clamp(17rem,52vh,31rem)] w-full shrink-0 items-end justify-center">
          <div className="intro-rise intro-white-glow w-full max-w-[min(50vh,28rem)] border border-slate-100 bg-[#050510] p-1">
            {level.resolutionImage ? (
              <img
                src={level.resolutionImage}
                alt={`${level.title} resolution`}
                className="aspect-square w-full object-cover [image-rendering:pixelated]"
              />
            ) : (
              <div
                role="img"
                aria-label={`${level.title} resolution placeholder`}
                className="resolution-placeholder aspect-square w-full"
              />
            )}
          </div>
        </div>

        <div className="mt-8 flex min-h-[16rem] w-full max-w-3xl flex-col items-center text-center font-mono text-sm font-semibold leading-7 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)] sm:mt-9 sm:min-h-[17rem] sm:text-base sm:leading-8">
          <p className="min-h-[10.5rem] whitespace-pre-wrap break-words sm:min-h-36">
            {visibleText}
            {!isComplete ? (
              <span className="intro-cursor ml-1 inline-block h-4 w-3 translate-y-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.95)] sm:h-5" />
            ) : null}
          </p>

          <div className="mt-8 flex h-14 items-center justify-center">
            {!isLastPage ? (
              <button
                type="button"
                onClick={handleContinue}
                disabled={!isComplete}
                className={`intro-rise intro-white-glow border border-white px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] text-white transition hover:bg-white hover:text-[#090013] disabled:cursor-not-allowed disabled:opacity-45 ${
                  isComplete ? "opacity-100" : "pointer-events-none opacity-0"
                }`}
              >
                Continue
              </button>
            ) : (
              <div
                className={`intro-rise border border-white/80 px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] text-white shadow-[0_0_12px_rgba(255,255,255,0.28)] transition-opacity duration-500 ${
                  isComplete ? "opacity-100" : "opacity-0"
                }`}
              >
                Level Cleared
              </div>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
