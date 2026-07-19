export interface LevelTheme {
  accent: string;
  accentSoft: string;
  meterGood: string;
  meterWarn: string;
  backdrop: string;
}

export interface LevelClue {
  id: string;
  title: string;
  image: string | null;
  alt: string;
}

export interface LevelConfig {
  levelId: number;
  nextLevelId?: number;
  title: string;
  introText: string;
  introPages?: string[];
  sceneImage: string | null;
  resolutionText: string;
  resolutionPages?: string[];
  resolutionImage?: string | null;
  debateBackground?: string | null;
  npcName: string;
  npcAvatar: string | null;
  npcThinkingAvatar?: string | null;
  npcInitialDialogue: string;
  clues?: LevelClue[];
  theme: LevelTheme;
  scenarioPrompt?: string;
}
