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
  const isLightTheme = level.theme.mode === "light";
  const isDataVaultTheme = level.levelId === 2;
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
    <main
      className={`min-h-screen overflow-hidden px-6 ${isLightTheme ? "text-slate-900" : "text-white"}`}
      style={{
        background:
          `radial-gradient(circle at 50% -10%, ${level.theme.accentSoft}, transparent 34rem), ${level.theme.backdrop}`,
      }}
    >
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col items-center py-8 sm:py-10">
        <div className="flex h-[clamp(17rem,52vh,31rem)] w-full shrink-0 items-end justify-center">
          <div className={`intro-rise ${isLightTheme ? "intro-cool-glow border-[#8ca8b5]/55 bg-[#e7f0f2]/82" : isDataVaultTheme ? "intro-white-glow border-[#75d8d0]/60 bg-[#031315]" : "intro-white-glow border-slate-100 bg-[#050510]"} w-full max-w-[min(50vh,28rem)] border p-1`}>
            {level.sceneImage ? (
              <img
                src={level.sceneImage}
                alt={`${level.title} scene`}
                className="aspect-square w-full object-cover [image-rendering:pixelated]"
              />
            ) : (
              <div
                role="img"
                aria-label={`${level.title} scene placeholder`}
                className={`level-art-placeholder aspect-square w-full ${isLightTheme ? "level-art-placeholder-light" : isDataVaultTheme ? "level-art-placeholder-vault" : ""}`}
                data-placeholder={`${level.title} intro scene`}
              />
            )}
          </div>
        </div>

        <div className={`mt-8 flex min-h-[16rem] w-full max-w-3xl flex-col items-center text-center font-mono text-sm font-semibold leading-7 sm:mt-9 sm:min-h-[17rem] sm:text-base sm:leading-8 ${isLightTheme ? "text-slate-800 drop-shadow-[0_1px_1px_rgba(229,240,243,0.75)]" : "text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"}`}>
          <p className="min-h-[10.5rem] whitespace-pre-wrap break-words sm:min-h-36">
            {visibleText}
            <span className={`intro-cursor ml-1 inline-block h-4 w-3 translate-y-0.5 sm:h-5 ${isLightTheme ? "bg-[#466979] shadow-[0_0_10px_rgba(82,120,131,0.36)]" : isDataVaultTheme ? "bg-[#8ee0d8] shadow-[0_0_10px_rgba(86,196,189,0.72)]" : "bg-white shadow-[0_0_10px_rgba(255,255,255,0.95)]"}`} />
          </p>

          <div className="mt-8 flex h-14 items-center justify-center">
            {isComplete ? (
              <button
                key={pageIndex}
                type="button"
                onClick={handleContinue}
                disabled={continueDisabled}
                className={`intro-rise ${isLightTheme ? "intro-cool-glow border-[#527883] bg-[#e7f0f2]/70 text-slate-800 hover:bg-[#527883] hover:text-[#f4f8f9]" : isDataVaultTheme ? "intro-white-glow border-[#75d8d0]/80 text-[#d8fffb] hover:bg-[#75d8d0] hover:text-[#031315]" : "intro-white-glow border-white text-white hover:bg-white hover:text-[#090013]"} border px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] transition disabled:cursor-not-allowed disabled:opacity-45`}
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
