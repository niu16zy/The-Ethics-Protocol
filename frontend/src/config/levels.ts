import type { LevelConfig } from "../types/level";
import levelOneIntroScene from "../assets/levels/level-1/intro-scene.jpg";
import levelOneDebateBackground from "../assets/levels/level-1/debate-background.jpg";
import levelOneNpcAvatar from "../assets/levels/level-1/npc-avatar.png";
import levelOneNpcThinkingAvatar from "../assets/levels/level-1/npc-thinking-avatar.png";
import levelOneAegisRecruitIntroduction from "../assets/levels/level-1/aegis-recruit-introduction.jpg";
import levelOneNpcFail from "../assets/levels/level-1/npcfail.png";

export const levelOne: LevelConfig = {
  levelId: 1,
  nextLevelId: 2,
  title: "Level 1: The Hiring Gate",
  introText:
    "Welcome to Neo-Isaac, 2026. Behind the flawless neon skyline lies a society entirely governed by cold, unyielding algorithms. You are a Senior Auditor from the Bureau of Algorithmic Audits. You must draw on your years of experience handling AI ethics cases and your advanced interrogation skills to construct ethically grounded, compelling arguments capable of breaking down the subject’s psychological defenses.",
  introPages: [
    "Welcome to Neo-Isaac, 2026. Behind the flawless neon skyline lies a society entirely governed by cold, unyielding algorithms. You are a Senior Auditor from the Bureau of Algorithmic Audits. You must draw on your years of experience handling AI ethics cases and your advanced interrogation skills to construct ethically grounded, compelling arguments capable of breaking down the subject’s psychological defenses.",
    "Your target is the obsidian headquarters of Atlas Tech Group. Inside, Senior VP Victor Barrett blindly defends Aegis-Recruit v4—a generative hiring AI that has quietly, systematically purged human diversity to chase pure profit.",
  ],
  sceneImage: levelOneIntroScene,
  resolutionText:
    "The Logic Fortress reaches zero. The glass around Victor's command console goes dark; one by one, Aegis-Recruit's candidate rankings stop refreshing. For the first time tonight, the room is quiet enough to hear him breathe.",
  resolutionPages: [
    "The Logic Fortress reaches zero. The glass around Victor's command console goes dark; one by one, Aegis-Recruit's candidate rankings stop refreshing. For the first time tonight, the room is quiet enough to hear him breathe.",
    "Victor Barrett withdraws the rollout order. He will not use the AI system to screen applicants until its bias, transparency, and accountability failures can be answered. He transfers control of Aegis-Recruit to the audit office, then opens a secure line to his superiors: the system is suspended, and the decision is final.",
  ],
  resolutionImage: levelOneNpcFail,
  debateBackground: levelOneDebateBackground,
  npcName: "Victor Barrett",
  npcAvatar: levelOneNpcAvatar,
  npcThinkingAvatar: levelOneNpcThinkingAvatar,
  npcInitialDialogue:
    "Make it efficient. My board expects a hiring pipeline that scales, not another hand-wringing seminar. If you want me to slow Aegis-Recruit, bring an audit-grade objection I cannot bury in a risk memo.",
  clues: [
    {
      id: "aegis-recruit-introduction",
      title: "Aegis-Recruit v4",
      image: levelOneAegisRecruitIntroduction,
      alt: "Atlas Tech Group Aegis-Recruit v4 introductory document",
    },
  ],
  scenarioPrompt:
    "Challenge Victor Barrett's rollout of an uncalibrated generative HR screening AI. Argue why it must be tested for bias and explained to affected applicants.",
  theme: {
    accent: "#d8b35d",
    accentSoft: "rgba(216, 179, 93, 0.16)",
    meterGood: "#87a8c8",
    meterWarn: "#b86b61",
    backdrop: "#050506",
  },
};

export const levelTwo: LevelConfig = {
  levelId: 2,
  title: "Level 2: The Memory Vault",
  introText:
    "Aegis-Recruit is frozen, but Atlas has already moved the next system underground. Beneath Neo-Isaac, CivicPulse is being trained on the city's memory: service chats, transaction traces, health appointments, education records, and private complaints that were never meant to become a single machine-readable citizen profile.",
  introPages: [
    "Aegis-Recruit is frozen, but Atlas has already moved the next system underground. Beneath Neo-Isaac, CivicPulse is being trained on the city's memory: service chats, transaction traces, health appointments, education records, and private complaints that were never meant to become a single machine-readable citizen profile.",
    "Your target is Dr. Selene Voss, Atlas Tech Group's Chief Data Architect. She claims the data already exists, so using it is merely civic optimization. You must prove that existing data is not automatically ethical training data.",
  ],
  sceneImage: null,
  resolutionText:
    "The Memory Vault falls silent. CivicPulse's intake streams detach one by one, and the living map of Neo-Isaac collapses into anonymized fragments that can no longer be traced back to individual citizens.",
  resolutionPages: [
    "The Memory Vault falls silent. CivicPulse's intake streams detach one by one, and the living map of Neo-Isaac collapses into anonymized fragments that can no longer be traced back to individual citizens.",
    "Selene Voss signs the suspension order. CivicPulse cannot continue until Atlas proves lawful collection, data minimization, anonymization, access control, sensitive-domain boundaries, source documentation, and output monitoring.",
  ],
  resolutionImage: null,
  debateBackground: null,
  npcName: "Dr. Selene Voss",
  npcAvatar: null,
  npcThinkingAvatar: null,
  npcInitialDialogue:
    "Every city leaves traces, Auditor. We did not steal them; we organized them. CivicPulse sees patterns no human office could process, and Neo-Isaac runs better because I refused to let useful data rot in separate vaults. Show me a privacy failure that is more than superstition.",
  clues: [
    {
      id: "civicpulse-data-intake-memo",
      title: "CivicPulse Data Intake Memo",
      image: null,
      alt: "Atlas Tech Group CivicPulse data intake memo placeholder",
    },
  ],
  scenarioPrompt:
    "Challenge Dr. Selene Voss's city-scale CivicPulse deployment. Argue why personal and sensitive data must be minimized, protected, documented, and monitored before it can be used by a generative AI system.",
  theme: {
    accent: "#52d1c5",
    accentSoft: "rgba(82, 209, 197, 0.16)",
    meterGood: "#68d8cf",
    meterWarn: "#ff6b7a",
    backdrop: "#031012",
  },
};

export const levels = [levelOne, levelTwo];
