import type { ReactNode } from "react";
import type { LevelConfig } from "../types/level";
import type { SessionRead, UserRead } from "../types/api";
import { LlmStatusBadge } from "./LlmStatusBadge";

interface LevelShellProps {
  level: LevelConfig;
  user: UserRead | null;
  session: SessionRead | null;
  children: ReactNode;
}

export function LevelShell({ level, user, session, children }: LevelShellProps) {
  return (
    <main className="min-h-screen bg-fortress-black px-4 py-5 text-fortress-text sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header className="flex flex-col gap-3 border-b border-fortress-line pb-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-fortress-amber">
              Logic Fortress
            </p>
            <h1 className="mt-2 font-display text-3xl text-fortress-text sm:text-4xl">
              {level.title}
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-fortress-muted">
              {level.scenarioPrompt}
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-fortress-muted">
            <span className="border border-fortress-line px-3 py-2">
              Player: {user?.display_name ?? "initializing"}
            </span>
            <span className="border border-fortress-line px-3 py-2">
              Session: {session?.id ?? "..."}
            </span>
            <LlmStatusBadge />
          </div>
        </header>

        {children}
      </div>
    </main>
  );
}
