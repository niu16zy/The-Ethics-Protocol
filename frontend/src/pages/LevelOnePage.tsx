import {
  useEffect,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";
import { useMutation } from "@tanstack/react-query";
import {
  createSession,
  createUser,
  getSession,
  getUser,
  submitDebateTurnStream,
} from "../api/logicFortressApi";
import { ApiError } from "../api/client";
import { IntroScene } from "../components/IntroScene";
import { ResolutionScene } from "../components/ResolutionScene";
import { levelOne } from "../config/levels";
import { useGameStore } from "../stores/gameStore";
import type { DebateTurnStreamEvent, SessionRead, UserRead } from "../types/api";
import type { LevelClue, LevelClueHotspot, LevelConfig } from "../types/level";

interface InitialGameState {
  user: UserRead;
  session: SessionRead;
}

interface LevelOnePageProps {
  level?: LevelConfig;
}

interface ClueTilt {
  rotateX: number;
  rotateY: number;
  translateX: number;
  translateY: number;
}

const NEUTRAL_CLUE_TILT: ClueTilt = {
  rotateX: 0,
  rotateY: 0,
  translateX: 0,
  translateY: 0,
};

function messageFromError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.detail ?? error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unknown error";
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

async function initializeGame(level: LevelConfig): Promise<InitialGameState> {
  const suffix = crypto.randomUUID().slice(0, 8);
  const createdUser = await createUser({
    username: `lf_player_${suffix}`,
    display_name: "Field Analyst",
  });
  const user = await getUser(createdUser.id);
  const createdSession = await createSession({
    user_id: user.id,
    current_level: level.levelId,
  });
  const session = await getSession(createdSession.id);

  return { user, session };
}

export function LevelOnePage({ level = levelOne }: LevelOnePageProps) {
  const isLightTheme = level.theme.mode === "light";
  const isDataVaultTheme = level.levelId === 2;
  const [playerInput, setPlayerInput] = useState("");
  const [turnError, setTurnError] = useState<string | null>(null);
  const [streamPhase, setStreamPhase] = useState<string | null>(null);
  const [streamTargetDialogue, setStreamTargetDialogue] = useState("");
  const [visibleStreamDialogue, setVisibleStreamDialogue] = useState("");
  const [isSubmittingTurn, setIsSubmittingTurn] = useState(false);
  const [pendingMeter, setPendingMeter] = useState<number | null>(null);
  const [displayedMeter, setDisplayedMeter] = useState<number | null>(null);
  const [activeClue, setActiveClue] = useState<LevelClue | null>(null);
  const [activeClueHotspot, setActiveClueHotspot] = useState<LevelClueHotspot | null>(null);
  const [clueTilt, setClueTilt] = useState<ClueTilt>(NEUTRAL_CLUE_TILT);
  const {
    stage,
    user,
    session,
    lastTurn,
    setStage,
    setUser,
    setSession,
    setLastTurn,
  } = useGameStore();

  const initializeMutation = useMutation({
    mutationFn: () => initializeGame(level),
    onSuccess: ({ user: createdUser, session: createdSession }) => {
      setUser(createdUser);
      setSession(createdSession);
      setDisplayedMeter(createdSession.fortress_meter);
    },
  });

  useEffect(() => {
    if (user || session || initializeMutation.isPending) {
      return;
    }

    initializeMutation.mutate();
  }, []);

  const initializationError = initializeMutation.error
    ? messageFromError(initializeMutation.error)
    : undefined;

  useEffect(() => {
    if (!streamTargetDialogue || visibleStreamDialogue.length >= streamTargetDialogue.length) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setVisibleStreamDialogue((current) => streamTargetDialogue.slice(0, current.length + 1));
    }, 18);

    return () => window.clearTimeout(timer);
  }, [streamTargetDialogue, visibleStreamDialogue.length]);

  useEffect(() => {
    if (displayedMeter !== null || !session) {
      return undefined;
    }

    setDisplayedMeter(session.fortress_meter);
    return undefined;
  }, [displayedMeter, session]);

  const isNpcTextOutputComplete =
    !isSubmittingTurn &&
    (streamTargetDialogue.length === 0 ||
      visibleStreamDialogue.length >= streamTargetDialogue.length);

  useEffect(() => {
    if (!isNpcTextOutputComplete || pendingMeter === null) {
      return undefined;
    }

    setDisplayedMeter(pendingMeter);
    setPendingMeter(null);
    return undefined;
  }, [isNpcTextOutputComplete, pendingMeter]);

  useEffect(() => {
    if (stage !== "debate" || pendingMeter !== null || displayedMeter === null || displayedMeter > 0) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setStage("resolution");
    }, 2400);

    return () => window.clearTimeout(timer);
  }, [displayedMeter, pendingMeter, setStage, stage]);

  useEffect(() => {
    if (!activeClue) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (activeClueHotspot) {
          setActiveClueHotspot(null);
        } else {
          setActiveClue(null);
          setClueTilt(NEUTRAL_CLUE_TILT);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeClue, activeClueHotspot]);

  const npcDialogue =
    streamTargetDialogue.length > 0
      ? visibleStreamDialogue
      : lastTurn?.npc_response ?? level.npcInitialDialogue;
  const currentMeter = displayedMeter ?? session?.fortress_meter ?? 50;
  const canSubmitArgument =
    Boolean(session) &&
    playerInput.trim().length > 0 &&
    !isSubmittingTurn &&
    pendingMeter === null &&
    isNpcTextOutputComplete;
  const isAwaitingPersonaStream = isSubmittingTurn && streamTargetDialogue.length === 0;
  const npcPortrait =
    isAwaitingPersonaStream && level.npcThinkingAvatar
      ? level.npcThinkingAvatar
      : level.npcAvatar;
  const pendingDialogueText = `${level.npcName} is considering...`;
  const currentMeterLabel = meterStateLabel(currentMeter);

  const handleStreamEvent = (event: DebateTurnStreamEvent) => {
    if (event.event === "phase") {
      setStreamPhase(event.phase);
      return;
    }

    if (event.event === "evaluator_complete") {
      setPendingMeter(event.meter_after);
      return;
    }

    if (event.event === "persona_delta") {
      setStreamPhase("persona");
      setStreamTargetDialogue((current) => current + event.text);
      return;
    }

    if (event.event === "complete") {
      setLastTurn(event.turn);
      setPendingMeter(event.turn.meter_after);
      setStreamTargetDialogue(event.turn.npc_response);
      setSession(
        session
          ? {
              ...session,
              fortress_meter: event.turn.meter_after,
            }
          : session,
      );
    }
  };

  const submitArgument = async () => {
    const trimmed = playerInput.trim();
    if (!trimmed || !session || isSubmittingTurn) {
      return;
    }

    setPlayerInput("");
    setTurnError(null);
    setStreamPhase("retrieving");
    setStreamTargetDialogue("");
    setVisibleStreamDialogue("");
    setIsSubmittingTurn(true);
    setPendingMeter(null);

    try {
      await submitDebateTurnStream(
        session.id,
        { player_input: trimmed },
        {
          onEvent: handleStreamEvent,
        },
      );
    } catch (error) {
      setTurnError(messageFromError(error));
    } finally {
      setIsSubmittingTurn(false);
      setStreamPhase(null);
    }
  };

  const handleArgumentKeyDown = (event: ReactKeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key !== "Enter" || event.shiftKey || event.nativeEvent.isComposing) {
      return;
    }

    event.preventDefault();
    void submitArgument();
  };

  const handleCluePointerMove = (event: ReactPointerEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
    const y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;

    setClueTilt({
      rotateX: -y * 5,
      rotateY: x * 5,
      translateX: x * 6,
      translateY: y * 6,
    });
  };

  const closeActiveClue = () => {
    setActiveClue(null);
    setActiveClueHotspot(null);
    setClueTilt(NEUTRAL_CLUE_TILT);
  };

  const clueImageTransform = `translate3d(${clueTilt.translateX}px, ${clueTilt.translateY}px, 0) rotateX(${clueTilt.rotateX}deg) rotateY(${clueTilt.rotateY}deg)`;
  const activeClueHasHotspots = Boolean(activeClue?.hotspots?.length);

  if (stage === "intro") {
    return (
      <IntroScene
        level={level}
        isInitializing={initializeMutation.isPending}
        initializationError={initializationError}
        canEnter={Boolean(user && session)}
        onEnter={() => setStage("debate")}
        onRetryInitialization={() => initializeMutation.mutate()}
      />
    );
  }

  if (stage === "resolution") {
    return <ResolutionScene level={level} />;
  }

  return (
    <main
      className={`min-h-screen p-3 sm:p-5 ${isLightTheme ? "text-slate-900" : "text-white"}`}
      style={{
        background:
          `radial-gradient(circle at 50% -10%, ${level.theme.accentSoft}, transparent 34rem), ${level.theme.backdrop}`,
      }}
    >
      <section className={`mx-auto flex min-h-[calc(100vh-1.5rem)] w-full max-w-7xl flex-col overflow-hidden rounded-2xl border backdrop-blur-xl sm:min-h-[calc(100vh-2.5rem)] ${isLightTheme ? "border-[#8ca8b5]/35 bg-[#e6eff2]/78 shadow-[0_24px_80px_rgba(58,82,96,0.22)]" : isDataVaultTheme ? "border-[#1e5b59]/30 bg-[#041416]/70 shadow-[0_24px_80px_rgba(0,20,22,0.5)]" : "border-white/10 bg-white/[0.035] shadow-[0_24px_80px_rgba(0,0,0,0.45)]"}`}>
        <div className={`relative min-h-[60vh] flex-1 overflow-hidden sm:min-h-[64vh] ${isLightTheme ? "bg-[#d8e5ea]" : isDataVaultTheme ? "bg-[#061719]" : "bg-[#111122]"}`}>
          {level.debateBackground ? (
            <img
              src={level.debateBackground}
              alt=""
              className="absolute inset-0 h-full w-full object-cover"
            />
          ) : (
            <div
              role="img"
              aria-label={`${level.title} debate background placeholder`}
              className={`level-art-placeholder absolute inset-0 ${isLightTheme ? "level-art-placeholder-light" : isDataVaultTheme ? "level-art-placeholder-vault" : ""}`}
              data-placeholder={`${level.title} background`}
            />
          )}
          <div className={`absolute inset-0 ${isLightTheme ? "bg-[#dfe9ed]/25" : "bg-black/15"}`} />
          <div className={isLightTheme ? "absolute inset-0 bg-[linear-gradient(rgba(82,120,131,0.035)_1px,transparent_1px)] bg-[length:100%_6px]" : isDataVaultTheme ? "absolute inset-0 bg-[linear-gradient(rgba(126,218,209,0.04)_1px,transparent_1px)] bg-[length:100%_6px]" : "absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[length:100%_6px]"} />

          <div className="npc-pop-out absolute left-4 top-5 z-10 w-[clamp(9rem,28vw,20rem)] sm:left-8 sm:top-10 lg:left-10 lg:top-12">
            <div className={`w-full rounded-xl border p-3 backdrop-blur-xl backdrop-saturate-150 sm:p-4 ${isLightTheme ? "border-[#7f9faf]/28 bg-[#eaf2f4]/76 shadow-[inset_0_1px_0_rgba(246,251,252,0.72),0_18px_60px_rgba(58,82,96,0.18)]" : isDataVaultTheme ? "border-[#2a7772]/28 bg-[#082226]/78 shadow-[inset_0_1px_0_rgba(126,218,209,0.12),0_18px_60px_rgba(0,20,22,0.42)]" : "border-white/15 bg-white/[0.105] shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_18px_60px_rgba(0,0,0,0.35)]"}`}>
              <div className={`flex aspect-[3/4] items-center justify-center overflow-hidden rounded-lg border ${isLightTheme ? "border-[#7f9faf]/22 bg-[#d8e5ea]/80" : isDataVaultTheme ? "border-[#2a7772]/22 bg-[#061719]/80" : "border-white/10 bg-[#101024]/70"}`}>
                {npcPortrait ? (
                  <img
                    src={npcPortrait}
                    alt={level.npcName}
                    className="h-full w-full object-cover object-top"
                  />
                ) : (
                  <div
                    role="img"
                    aria-label={`${level.npcName} portrait placeholder`}
                    className={`level-portrait-placeholder h-full w-full ${isLightTheme ? "level-art-placeholder-light" : isDataVaultTheme ? "level-art-placeholder-vault" : ""}`}
                    data-placeholder={`${level.npcName} portrait`}
                  />
                )}
              </div>
            </div>
          </div>

          <div className={`absolute bottom-4 left-4 right-4 z-10 flex h-48 flex-col overflow-hidden rounded-xl border px-4 py-3 backdrop-blur-xl backdrop-saturate-150 sm:bottom-5 sm:left-8 sm:right-8 sm:h-52 sm:px-5 sm:py-4 lg:left-10 lg:right-10 ${isLightTheme ? "border-[#7f9faf]/28 bg-[#eaf2f4]/82 shadow-[inset_0_1px_0_rgba(246,251,252,0.68),0_18px_60px_rgba(58,82,96,0.16)]" : isDataVaultTheme ? "border-[#2a7772]/30 bg-[#071d21]/84 shadow-[inset_0_1px_0_rgba(126,218,209,0.13),0_18px_60px_rgba(0,20,22,0.42)]" : "border-white/15 bg-white/[0.115] shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_18px_60px_rgba(0,0,0,0.35)]"}`}>
            <p className={`shrink-0 font-mono text-lg font-semibold uppercase tracking-[0.12em] sm:text-2xl ${isLightTheme ? "text-slate-800" : "text-white/90"}`}>
              {level.npcName}
            </p>
            <p className={`mt-2 min-h-0 flex-1 overflow-hidden whitespace-pre-wrap break-words font-mono text-base font-semibold leading-7 sm:text-lg sm:leading-8 ${isLightTheme ? "text-slate-700" : "text-white/90"}`}>
              {streamPhase && streamTargetDialogue.length === 0
                ? pendingDialogueText
                : npcDialogue}
            </p>
          </div>

          <div className={`absolute right-4 top-4 z-20 w-[calc(100vw-12rem)] min-w-32 max-w-[14rem] rounded-xl border p-3 text-xs backdrop-blur-md sm:right-6 sm:top-6 sm:w-72 sm:max-w-72 lg:right-8 lg:top-8 ${isLightTheme ? "border-[#7f9faf]/24 bg-[#eaf2f4]/74 text-slate-700 shadow-[0_14px_40px_rgba(58,82,96,0.14)]" : isDataVaultTheme ? "border-[#2a7772]/24 bg-[#071d21]/72 text-[#b7deda] shadow-[0_14px_40px_rgba(0,20,22,0.34)]" : "border-white/10 bg-white/[0.055] text-slate-300 shadow-[0_14px_40px_rgba(0,0,0,0.25)]"}`}>
            <div className={`mt-2 h-2 overflow-hidden rounded-full ${isLightTheme ? "bg-[#b8cbd4]/75" : isDataVaultTheme ? "bg-[#143b3d]/80" : "bg-white/10"}`}>
              <div
                className={`h-full rounded-full transition-[width] duration-500 ${isLightTheme ? "shadow-[0_0_8px_rgba(82,120,131,0.24)]" : "shadow-[0_0_8px_rgba(255,255,255,0.32)]"}`}
                style={{
                  width: `${Math.max(0, Math.min(100, currentMeter))}%`,
                  backgroundColor: currentMeter <= 25 ? level.theme.meterWarn : level.theme.meterGood,
                }}
              />
            </div>
          </div>

          {level.clues?.length ? (
            <div className="absolute right-4 top-28 z-30 flex flex-col gap-3 sm:right-6 sm:top-32 lg:right-8">
              {level.clues.map((clue) => (
                <button
                  key={clue.id}
                  type="button"
                  onClick={() => {
                    setActiveClue(clue);
                    setActiveClueHotspot(null);
                  }}
                  className={`group inline-flex overflow-hidden rounded-lg border p-[3px] backdrop-blur-xl backdrop-saturate-150 transition hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${isLightTheme ? "border-[#7f9faf]/28 bg-[#eaf2f4]/76 shadow-[inset_0_1px_0_rgba(246,251,252,0.68),0_14px_34px_rgba(58,82,96,0.16)] hover:bg-[#f1f6f7]/88 focus-visible:outline-[#527883]" : isDataVaultTheme ? "border-[#2a7772]/28 bg-[#082226]/78 shadow-[inset_0_1px_0_rgba(126,218,209,0.12),0_14px_34px_rgba(0,20,22,0.38)] hover:bg-[#0d3033]/88 focus-visible:outline-[#56c4bd]" : "border-white/15 bg-white/[0.105] shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_14px_34px_rgba(0,0,0,0.35)] hover:bg-white/[0.16] focus-visible:outline-white/80"}`}
                  aria-label={`Open clue: ${clue.title}`}
                >
                  {clue.image ? (
                    <img
                      src={clue.image}
                      alt=""
                      className="block h-32 w-auto object-contain [image-rendering:auto] sm:h-36"
                    />
                  ) : (
                    <div
                      aria-hidden="true"
                      className={`level-clue-placeholder h-32 w-24 sm:h-36 sm:w-28 ${isLightTheme ? "level-art-placeholder-light" : isDataVaultTheme ? "level-art-placeholder-vault" : ""}`}
                      data-placeholder={clue.title}
                    />
                  )}
                </button>
              ))}
            </div>
          ) : null}

        </div>

        <section className={`border-t p-3 backdrop-blur-xl sm:p-4 ${isLightTheme ? "border-[#8ca8b5]/35 bg-[#dfe9ed]/92" : isDataVaultTheme ? "border-[#1e5b59]/30 bg-[#031315]/86" : "border-white/10 bg-[#090013]/75"}`}>
          {turnError ? (
            <div className={`mb-3 rounded-xl border p-3 text-sm backdrop-blur-md ${isLightTheme ? "border-[#7f9faf]/24 bg-[#eaf2f4]/78 text-slate-700" : isDataVaultTheme ? "border-[#2a7772]/24 bg-[#071d21]/72 text-[#d8fffb]" : "border-white/10 bg-white/[0.055] text-white/90"}`}>
              {turnError}
            </div>
          ) : null}

          <div className="mt-2">
            <label className="block">
              <span className={`text-xs uppercase tracking-[0.22em] ${isLightTheme ? "text-[#466979]" : isDataVaultTheme ? "text-[#8ec9c3]" : "text-slate-300"}`}>
                Your response
              </span>
              <div className="relative mt-2">
                <textarea
                  value={playerInput}
                  onChange={(event) => setPlayerInput(event.target.value)}
                  onKeyDown={handleArgumentKeyDown}
                  disabled={!session || isSubmittingTurn}
                  rows={2}
                  maxLength={4000}
                  placeholder="Ask, challenge, or make an ethical argument..."
                  className={`logic-response-textarea ${isDataVaultTheme ? "logic-response-textarea-vault" : ""} w-full resize-none rounded-xl border py-3 pl-4 pr-28 pb-10 font-mono text-base leading-7 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-md transition-colors duration-200 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-60 sm:pr-32 ${isLightTheme ? "border-[#849faf]/45 bg-[#eaf2f4]/86 text-slate-800 placeholder:text-slate-500 focus:border-[#527883] focus-visible:border-[#527883]" : isDataVaultTheme ? "border-[#2a7772]/30 bg-[#061d20]/82 text-[#f0fffd] placeholder:text-[#658e8b] focus:border-[#56c4bd] focus-visible:border-[#56c4bd]" : "border-white/10 bg-white/[0.06] text-white placeholder:text-slate-500 focus:border-white/10 focus-visible:border-white/10"}`}
                />
                <button
                  type="button"
                  onClick={submitArgument}
                  disabled={!canSubmitArgument}
                  className={`absolute bottom-3 right-4 bg-transparent p-0 font-mono text-xs font-semibold uppercase tracking-[0.12em] transition disabled:cursor-not-allowed disabled:opacity-45 sm:right-5 sm:text-sm ${isLightTheme ? "text-[#466979] hover:text-[#233843]" : isDataVaultTheme ? "text-[#8ee0d8] hover:text-[#d8fffb]" : "text-white/85 hover:text-white"}`}
                >
                  Submit
                </button>
              </div>
            </label>
          </div>

        </section>
      </section>

      {activeClue ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/72 p-4 shadow-[inset_0_0_180px_rgba(0,0,0,0.82)] sm:p-6"
          style={{ backdropFilter: "blur(4px) brightness(0.85)" }}
          role="dialog"
          aria-modal="true"
          aria-label={activeClue.title}
          onPointerMove={handleCluePointerMove}
          onPointerLeave={() => setClueTilt(NEUTRAL_CLUE_TILT)}
          onClick={closeActiveClue}
        >
          <figure
            className={`relative z-10 flex max-h-[92vh] w-full items-center justify-center ${activeClueHasHotspots ? "max-w-[min(96vw,96rem)]" : "max-w-5xl"}`}
            style={{ perspective: "1200px" }}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              onClick={closeActiveClue}
              className="absolute right-0 top-0 z-20 bg-black/55 px-3 py-2 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-white/90 backdrop-blur-md transition hover:bg-black/75 hover:text-white sm:-top-12 sm:bg-white/[0.12]"
            >
              Close
            </button>
            {activeClueHotspot ? (
              <>
                <button
                  type="button"
                  onClick={() => setActiveClueHotspot(null)}
                  className="absolute left-0 top-0 z-20 bg-black/55 px-3 py-2 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-white/90 backdrop-blur-md transition hover:bg-black/75 hover:text-white sm:-top-12 sm:bg-white/[0.12]"
                >
                  Back
                </button>
                <img
                  src={activeClueHotspot.image}
                  alt={activeClueHotspot.alt}
                  className="max-h-[86vh] max-w-full rounded-md object-contain drop-shadow-[0_26px_34px_rgba(0,0,0,0.62)] transition-transform duration-100 ease-out will-change-transform"
                  style={{
                    transform: clueImageTransform,
                    transformStyle: "preserve-3d",
                  }}
                />
              </>
            ) : activeClue.image ? (
              <div
                className={`relative inline-block max-h-[86vh] max-w-full ${activeClueHasHotspots ? "" : "transition-transform duration-100 ease-out will-change-transform"}`}
                style={
                  activeClueHasHotspots
                    ? undefined
                    : {
                        transform: clueImageTransform,
                        transformStyle: "preserve-3d",
                      }
                }
              >
                <img
                  src={activeClue.image}
                  alt={activeClue.alt}
                  className="block max-h-[86vh] max-w-full rounded-md object-contain drop-shadow-[0_26px_34px_rgba(0,0,0,0.62)]"
                />
                {activeClue.hotspots?.map((hotspot) => (
                  <button
                    key={hotspot.id}
                    type="button"
                    title={hotspot.title}
                    aria-label={`Open enlarged clipping: ${hotspot.title}`}
                    onClick={(event) => {
                      event.stopPropagation();
                      setActiveClueHotspot(hotspot);
                      setClueTilt(NEUTRAL_CLUE_TILT);
                    }}
                    className="absolute cursor-zoom-in bg-transparent focus-visible:outline-none"
                    style={{
                      left: `${hotspot.x}%`,
                      top: `${hotspot.y}%`,
                      width: `${hotspot.width}%`,
                      height: `${hotspot.height}%`,
                    }}
                  />
                ))}
              </div>
            ) : (
              <div
                role="img"
                aria-label={activeClue.alt}
                className={`level-clue-placeholder h-[min(86vh,48rem)] w-[min(80vw,36rem)] rounded-lg border shadow-[0_28px_90px_rgba(0,0,0,0.72)] ${isLightTheme ? "level-art-placeholder-light border-[#8ca8b5]/38" : isDataVaultTheme ? "level-art-placeholder-vault border-[#2a7772]/38" : "border-white/20"}`}
                data-placeholder={activeClue.title}
              />
            )}
          </figure>
        </div>
      ) : null}
    </main>
  );
}
