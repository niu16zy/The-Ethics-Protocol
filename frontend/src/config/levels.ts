import type { LevelConfig } from "../types/level";
import levelOneIntroScene from "../assets/levels/level-1/intro-scene.jpg";
import levelOneDebateBackground from "../assets/levels/level-1/debate-background.jpg";
import levelOneNpcAvatar from "../assets/levels/level-1/npc-avatar.png";
import levelOneNpcThinkingAvatar from "../assets/levels/level-1/npc-thinking-avatar.png";
import levelOneAegisRecruitIntroduction from "../assets/levels/level-1/aegis-recruit-introduction.jpg";

export const levelOne: LevelConfig = {
  levelId: 1,
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
  resolutionImage: null,
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

export const levels = [levelOne];
