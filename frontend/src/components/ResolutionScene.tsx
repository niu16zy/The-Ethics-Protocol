import { useEffect, useMemo, useState } from "react";
import type { LevelConfig } from "../types/level";

interface ResolutionSceneProps {
  level: LevelConfig;
}

export function ResolutionScene({ level }: ResolutionSceneProps) {
  const isLightTheme = level.theme.mode === "light";
  const isDataVaultTheme = level.levelId === 2;
  const resolutionPages = level.resolutionPages?.length
    ? level.resolutionPages
    : [level.resolutionText];
  const [pageIndex, setPageIndex] = useState(0);
  const [visibleCount, setVisibleCount] = useState(0);
  const currentText = resolutionPages[pageIndex] ?? level.resolutionText;
  const isLastPage = pageIndex === resolutionPages.length - 1;
  const isComplete = visibleCount >= currentText.length;
  const hasNextLevel = typeof level.nextLevelId === "number";
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

  const handleLevelCleared = () => {
    if (!isComplete || !hasNextLevel || level.nextLevelId === undefined) {
      return;
    }

    const targetUrl = new URL(window.location.href);
    targetUrl.searchParams.set("level", String(level.nextLevelId));
    targetUrl.hash = "";
    window.location.assign(targetUrl.toString());
  };

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
                className={`level-art-placeholder aspect-square w-full ${isLightTheme ? "level-art-placeholder-light" : isDataVaultTheme ? "level-art-placeholder-vault" : ""}`}
                data-placeholder={`${level.title} resolution`}
              />
            )}
          </div>
        </div>

        <div className={`mt-8 flex min-h-[16rem] w-full max-w-3xl flex-col items-center text-center font-mono text-sm font-semibold leading-7 sm:mt-9 sm:min-h-[17rem] sm:text-base sm:leading-8 ${isLightTheme ? "text-slate-800 drop-shadow-[0_1px_1px_rgba(229,240,243,0.75)]" : "text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]"}`}>
          <p className="min-h-[10.5rem] whitespace-pre-wrap break-words sm:min-h-36">
            {visibleText}
            {!isComplete ? (
              <span className={`intro-cursor ml-1 inline-block h-4 w-3 translate-y-0.5 sm:h-5 ${isLightTheme ? "bg-[#466979] shadow-[0_0_10px_rgba(82,120,131,0.36)]" : isDataVaultTheme ? "bg-[#8ee0d8] shadow-[0_0_10px_rgba(86,196,189,0.72)]" : "bg-white shadow-[0_0_10px_rgba(255,255,255,0.95)]"}`} />
            ) : null}
          </p>

          <div className="mt-8 flex h-14 items-center justify-center">
            {!isLastPage ? (
              <button
                type="button"
                onClick={handleContinue}
                disabled={!isComplete}
                className={`intro-rise ${isLightTheme ? "intro-cool-glow border-[#527883] bg-[#e7f0f2]/70 text-slate-800 hover:bg-[#527883] hover:text-[#f4f8f9]" : isDataVaultTheme ? "intro-white-glow border-[#75d8d0]/80 text-[#d8fffb] hover:bg-[#75d8d0] hover:text-[#031315]" : "intro-white-glow border-white text-white hover:bg-white hover:text-[#090013]"} border px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] transition disabled:cursor-not-allowed disabled:opacity-45 ${
                  isComplete ? "opacity-100" : "pointer-events-none opacity-0"
                }`}
              >
                Continue
              </button>
            ) : hasNextLevel ? (
              <button
                type="button"
                onClick={handleLevelCleared}
                disabled={!isComplete}
                className={`intro-rise border px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] transition disabled:cursor-not-allowed disabled:opacity-45 ${isLightTheme ? "border-[#527883] bg-[#e7f0f2]/70 text-slate-800 shadow-[0_0_12px_rgba(82,120,131,0.18)] hover:bg-[#527883] hover:text-[#f4f8f9]" : isDataVaultTheme ? "border-[#75d8d0]/80 text-[#d8fffb] shadow-[0_0_12px_rgba(86,196,189,0.28)] hover:bg-[#75d8d0] hover:text-[#031315]" : "border-white/80 text-white shadow-[0_0_12px_rgba(255,255,255,0.28)] hover:bg-white hover:text-[#090013]"} ${
                  isComplete ? "opacity-100" : "pointer-events-none opacity-0"
                }`}
                aria-label={`Enter level ${level.nextLevelId}`}
              >
                Level Cleared
              </button>
            ) : (
              <div
                className={`intro-rise border px-7 py-3 font-mono text-sm font-semibold uppercase tracking-[0.16em] transition-opacity duration-500 ${isLightTheme ? "border-[#527883] bg-[#e7f0f2]/70 text-slate-800 shadow-[0_0_12px_rgba(82,120,131,0.18)]" : isDataVaultTheme ? "border-[#75d8d0]/80 text-[#d8fffb] shadow-[0_0_12px_rgba(86,196,189,0.28)]" : "border-white/80 text-white shadow-[0_0_12px_rgba(255,255,255,0.28)]"} ${
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
