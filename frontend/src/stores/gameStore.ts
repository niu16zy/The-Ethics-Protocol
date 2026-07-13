import { create } from "zustand";
import type { DebateTurnResponse, SessionRead, UserRead } from "../types/api";

export type LevelStage = "intro" | "debate" | "resolution";

interface GameState {
  stage: LevelStage;
  user: UserRead | null;
  session: SessionRead | null;
  lastTurn: DebateTurnResponse | null;
  setStage: (stage: LevelStage) => void;
  setUser: (user: UserRead | null) => void;
  setSession: (session: SessionRead | null) => void;
  setLastTurn: (turn: DebateTurnResponse | null) => void;
}

export const useGameStore = create<GameState>((set) => ({
  stage: "intro",
  user: null,
  session: null,
  lastTurn: null,
  setStage: (stage) => set({ stage }),
  setUser: (user) => set({ user }),
  setSession: (session) => set({ session }),
  setLastTurn: (turn) => set({ lastTurn: turn }),
}));
