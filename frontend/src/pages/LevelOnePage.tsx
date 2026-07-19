import { useEffect, useState, type KeyboardEvent as ReactKeyboardEvent } from "react";
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
import type { LevelClue, LevelConfig } from "../types/level";

interface InitialGameState {
  user: UserRead;
  session: SessionRead;
}

interface LevelOnePageProps {
  level?: LevelConfig;
}

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
  const [playerInput, setPlayerInput] = useState("");
  const [turnError, setTurnError] = useState<string | null>(null);
  const [streamPhase, setStreamPhase] = useState<string | null>(null);
  const [streamTargetDialogue, setStreamTargetDialogue] = useState("");
  const [visibleStreamDialogue, setVisibleStreamDialogue] = useState("");
  const [isSubmittingTurn, setIsSubmittingTurn] = useState(false);
  const [pendingMeter, setPendingMeter] = useState<number | null>(null);
  const [activeClue, setActiveClue] = useState<LevelClue | null>(null);
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
    if (stage !== "debate" || isSubmittingTurn) {
      return undefined;
    }

    const resolvedMeter = lastTurn?.meter_after ?? session?.fortress_meter;
    if (resolvedMeter === undefined || resolvedMeter > 0) {
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setStage("resolution");
    }, 900);

    return () => window.clearTimeout(timer);
  }, [
    isSubmittingTurn,
    lastTurn?.meter_after,
    session?.fortress_meter,
    setStage,
    stage,
  ]);

  useEffect(() => {
    if (!activeClue) {
      return undefined;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setActiveClue(null);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeClue]);

  const npcDialogue =
    streamTargetDialogue.length > 0
      ? visibleStreamDialogue
      : lastTurn?.npc_response ?? level.npcInitialDialogue;
  const currentMeter = pendingMeter ?? lastTurn?.meter_after ?? session?.fortress_meter ?? 50;
  const canSubmitArgument =
    Boolean(session) && playerInput.trim().length > 0 && !isSubmittingTurn;
  const isAwaitingPersonaStream = isSubmittingTurn && streamTargetDialogue.length === 0;
  const npcPortrait =
    isAwaitingPersonaStream && level.npcThinkingAvatar
      ? level.npcThinkingAvatar
      : level.npcAvatar;
  const pendingDialogueText =
    streamPhase === "persona"
      ? `${level.npcName} is choosing a response...`
      : "The audit lens is reviewing the case record...";
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
      setPendingMeter(null);
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
      className="min-h-screen p-3 text-white sm:p-5"
      style={{
        background:
          `radial-gradient(circle at 50% -10%, ${level.theme.accentSoft}, transparent 34rem), ${level.theme.backdrop}`,
      }}
    >
      <section className="mx-auto flex min-h-[calc(100vh-1.5rem)] w-full max-w-7xl flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/[0.035] shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl sm:min-h-[calc(100vh-2.5rem)]">
        <div className="relative min-h-[60vh] flex-1 overflow-hidden bg-[#111122] sm:min-h-[64vh]">
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
              className="level-art-placeholder absolute inset-0"
              data-placeholder={`${level.title} background`}
            />
          )}
          <div className="absolute inset-0 bg-black/15" />
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[length:100%_6px]" />

          <div className="npc-pop-out absolute left-4 right-4 top-5 z-10 sm:left-8 sm:right-8 sm:top-10 lg:left-10 lg:right-10 lg:top-12">
            <div className="w-[clamp(9rem,28vw,20rem)] rounded-xl border border-white/15 bg-white/[0.105] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_18px_60px_rgba(0,0,0,0.35)] backdrop-blur-xl backdrop-saturate-150 sm:p-4">
              <div className="flex aspect-[3/4] items-center justify-center overflow-hidden rounded-lg border border-white/10 bg-[#101024]/70">
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
                    className="level-portrait-placeholder h-full w-full"
                    data-placeholder={`${level.npcName} portrait`}
                  />
                )}
              </div>
            </div>

            <div className="mt-3 w-full rounded-xl border border-white/15 bg-white/[0.115] px-4 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_18px_60px_rgba(0,0,0,0.35)] backdrop-blur-xl backdrop-saturate-150 sm:mt-4 sm:px-5 sm:py-4">
              <p className="font-mono text-lg font-semibold uppercase tracking-[0.12em] text-white/90 sm:text-2xl">
                {level.npcName}
              </p>
              <p className="mt-2 max-h-[24vh] min-h-20 overflow-y-auto whitespace-pre-wrap break-words font-mono text-base font-semibold leading-7 text-white/90 sm:text-lg sm:leading-8">
                {streamPhase && streamTargetDialogue.length === 0
                  ? pendingDialogueText
                  : npcDialogue}
              </p>
            </div>
          </div>

          <div className="absolute right-4 top-4 z-20 w-[calc(100vw-12rem)] min-w-32 max-w-[14rem] rounded-xl border border-white/10 bg-white/[0.055] p-3 text-xs text-slate-300 shadow-[0_14px_40px_rgba(0,0,0,0.25)] backdrop-blur-md sm:right-6 sm:top-6 sm:w-72 sm:max-w-72 lg:right-8 lg:top-8">
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
              <div
                className="h-full rounded-full shadow-[0_0_8px_rgba(255,255,255,0.32)] transition-[width] duration-500"
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
                  onClick={() => setActiveClue(clue)}
                  className="group w-24 rounded-lg border border-white/15 bg-white/[0.105] p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.12),0_14px_34px_rgba(0,0,0,0.35)] backdrop-blur-xl backdrop-saturate-150 transition hover:-translate-y-0.5 hover:bg-white/[0.16] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white/80 sm:w-28"
                  aria-label={`Open clue: ${clue.title}`}
                >
                  {clue.image ? (
                    <img
                      src={clue.image}
                      alt=""
                      className="aspect-[3/4] w-full rounded border border-white/10 object-cover object-top [image-rendering:auto]"
                    />
                  ) : (
                    <div
                      aria-hidden="true"
                      className="level-clue-placeholder aspect-[3/4] w-full rounded border border-white/10"
                      data-placeholder={clue.title}
                    />
                  )}
                </button>
              ))}
            </div>
          ) : null}

        </div>

        <section className="border-t border-white/10 bg-[#090013]/75 p-3 backdrop-blur-xl sm:p-4">
          {turnError ? (
            <div className="mb-3 rounded-xl border border-white/10 bg-white/[0.055] p-3 text-sm text-white/90 backdrop-blur-md">
              {turnError}
            </div>
          ) : null}

          <div className="mt-2">
            <label className="block">
              <span className="text-xs uppercase tracking-[0.22em] text-slate-300">
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
                  className="w-full resize-none rounded-xl border border-white/10 bg-white/[0.06] py-3 pl-4 pr-28 pb-10 font-mono text-base leading-7 text-white placeholder:text-slate-500 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] backdrop-blur-md transition-colors duration-200 focus:border-white/10 focus:outline-none focus:ring-0 focus-visible:border-white/10 focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-60 sm:pr-32"
                />
                <button
                  type="button"
                  onClick={submitArgument}
                  disabled={!canSubmitArgument}
                  className="absolute bottom-3 right-4 bg-transparent p-0 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-white/85 transition hover:text-white disabled:cursor-not-allowed disabled:opacity-45 sm:right-5 sm:text-sm"
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
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/72 p-4 shadow-[inset_0_0_180px_rgba(0,0,0,0.82)] backdrop-blur-sm sm:p-6"
          role="dialog"
          aria-modal="true"
          aria-label={activeClue.title}
          onClick={() => setActiveClue(null)}
        >
          <figure
            className="relative z-10 flex max-h-[92vh] w-full max-w-5xl items-center justify-center"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setActiveClue(null)}
              className="absolute right-0 top-0 z-20 bg-black/55 px-3 py-2 font-mono text-xs font-semibold uppercase tracking-[0.12em] text-white/90 backdrop-blur-md transition hover:bg-black/75 hover:text-white sm:-top-12 sm:bg-white/[0.12]"
            >
              Close
            </button>
            {activeClue.image ? (
              <img
                src={activeClue.image}
                alt={activeClue.alt}
                className="max-h-[86vh] max-w-full rounded-lg border border-white/20 bg-white shadow-[0_28px_90px_rgba(0,0,0,0.72)]"
              />
            ) : (
              <div
                role="img"
                aria-label={activeClue.alt}
                className="level-clue-placeholder h-[min(86vh,48rem)] w-[min(80vw,36rem)] rounded-lg border border-white/20 shadow-[0_28px_90px_rgba(0,0,0,0.72)]"
                data-placeholder={activeClue.title}
              />
            )}
          </figure>
        </div>
      ) : null}
    </main>
  );
}
