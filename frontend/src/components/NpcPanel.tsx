import type { LevelConfig } from "../types/level";

interface NpcPanelProps {
  level: LevelConfig;
  status: string;
}

export function NpcPanel({ level, status }: NpcPanelProps) {
  return (
    <aside className="flex min-h-80 flex-col border border-fortress-line bg-fortress-ink">
      <div className="relative h-80 overflow-hidden border-b border-fortress-line bg-[#08090b]">
        {level.npcAvatar ? (
          <img
            src={level.npcAvatar}
            alt={level.npcName}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="relative h-full w-full">
            <div className="absolute left-1/2 top-12 h-32 w-24 -translate-x-1/2 border border-fortress-line bg-[#141820]" />
            <div className="absolute left-1/2 top-24 h-40 w-48 -translate-x-1/2 border border-fortress-line bg-[#101319]" />
            <div className="absolute left-[calc(50%-3rem)] top-24 h-2 w-2 bg-fortress-amber" />
            <div className="absolute left-[calc(50%+2.5rem)] top-24 h-2 w-2 bg-fortress-amber" />
            <div className="absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-fortress-black to-transparent" />
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[length:100%_5px]" />
          </div>
        )}
      </div>
      <div className="p-4">
        <p className="font-display text-2xl text-fortress-text">{level.npcName}</p>
        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-fortress-muted">{status}</p>
      </div>
    </aside>
  );
}
