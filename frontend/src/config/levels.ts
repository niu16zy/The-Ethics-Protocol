import type { LevelConfig } from "../types/level";
import levelOneIntroScene from "../assets/levels/level-1/intro-scene.jpg";
import levelOneDebateBackground from "../assets/levels/level-1/debate-background.jpg";
import levelOneNpcAvatar from "../assets/levels/level-1/npc-avatar.png";
import levelOneNpcThinkingAvatar from "../assets/levels/level-1/npc-thinking-avatar.png";
import levelOneAegisRecruitIntroduction from "../assets/levels/level-1/aegis-recruit-introduction.jpg";
import levelOneNpcFail from "../assets/levels/level-1/npcfail.png";
import levelTwoIntroScene from "../assets/levels/level-2/leve2-introPicl.jpg";
import levelTwoDebateBackground from "../assets/levels/level-2/level2Background.jpg";
import levelTwoCivicPulseClue from "../assets/levels/level-2/level2clue.png";
import levelTwoNpcAvatar from "../assets/levels/level-2/npc-avatar.png";
import levelTwoNpcThinkingAvatar from "../assets/levels/level-2/npc-thinking-avatar.png";
import levelTwoResolutionScene from "../assets/levels/level-2/level2-finished.png";
import levelThreeDebateBackground from "../assets/levels/level-3/debate-background.png";
import levelThreeCorkboardClue from "../assets/levels/level-3/corkboard.png";
import levelThreeClueLaunch from "../assets/levels/level-3/clue-launch.png";
import levelThreeClueBroadcast from "../assets/levels/level-3/clue-broadcast.png";
import levelThreeClueLeak from "../assets/levels/level-3/clue-data-breach.png";
import levelThreeIntroScene from "../assets/levels/level-3/level3-intro.png";
import levelThreeResolutionScene from "../assets/levels/level-3/level3_finished.png";
import levelThreeNpcAvatar from "../assets/levels/level-3/npc-avatar.png";
import levelThreeNpcThinkingAvatar from "../assets/levels/level-3/npc-thinking-avatar.png";

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
  nextLevelId: 3,
  title: "Level 2: The Memory Vault",
  introText:
    "Aegis-Recruit is frozen, but Atlas has already moved the next system underground. Beneath Neo-Isaac, CivicPulse is being trained on the city's memory: service chats, transaction traces, health appointments, education records, and private complaints that were never meant to become a single machine-readable citizen profile.",
  introPages: [
    "Aegis-Recruit is frozen, but Atlas has already moved the next system underground. Beneath Neo-Isaac, CivicPulse is being trained on the city's memory: service chats, transaction traces, health appointments, education records, and private complaints that were never meant to become a single machine-readable citizen profile.",
    "Your target is Dr. Selene Voss, Atlas Tech Group's Chief Data Architect. She claims the data already exists, so using it is merely civic optimization. You must prove that existing data is not automatically ethical training data.",
  ],
  sceneImage: levelTwoIntroScene,
  resolutionText:
    "The Memory Vault falls silent. CivicPulse's intake streams detach one by one, and the living map of Neo-Isaac collapses into anonymized fragments that can no longer be traced back to individual citizens.",
  resolutionPages: [
    "The Memory Vault falls silent. CivicPulse's intake streams detach one by one, and the living map of Neo-Isaac collapses into anonymized fragments that can no longer be traced back to individual citizens.",
    "Selene Voss signs the suspension order. CivicPulse cannot continue until Atlas proves lawful collection, data minimization, anonymization, access control, sensitive-domain boundaries, source documentation, and output monitoring.",
  ],
  resolutionImage: levelTwoResolutionScene,
  debateBackground: levelTwoDebateBackground,
  npcName: "Dr. Selene Voss",
  npcAvatar: levelTwoNpcAvatar,
  npcThinkingAvatar: levelTwoNpcThinkingAvatar,
  npcInitialDialogue:
    "Every city leaves traces, Auditor. We did not steal them; we organized them. CivicPulse sees patterns no human office could process, and Neo-Isaac runs better because I refused to let useful data rot in separate vaults. Show me a privacy failure that is more than superstition.",
  clues: [
    {
      id: "civicpulse-data-intake-memo",
      title: "CivicPulse Data Intake Memo",
      image: levelTwoCivicPulseClue,
      alt: "Atlas Tech Group CivicPulse data intake memo",
    },
  ],
  scenarioPrompt:
    "Challenge Dr. Selene Voss's city-scale CivicPulse deployment. Argue why personal and sensitive data must be minimized, protected, documented, and monitored before it can be used by a generative AI system.",
  theme: {
    accent: "#3caeaa",
    accentSoft: "rgba(60, 174, 170, 0.18)",
    meterGood: "#56c4bd",
    meterWarn: "#e06973",
    backdrop: "#020b0d",
  },
};

export const levelThree: LevelConfig = {
  levelId: 3,
  title: "Level 3: The Clinical Singularity",
  introText:
    "The Memory Vault is sealed, but Neo-Isaac has already centralized its next crisis. At Sacred Heart Hospital, ASCLEPIUS-03 hangs above the emergency control room: a faceless metal body beneath a cold white halo, issuing treatment plans and citywide public-health orders in an unbroken mechanical voice.",
  introPages: [
    "The Memory Vault is sealed, but Neo-Isaac has already centralized its next crisis. At Sacred Heart Hospital, ASCLEPIUS-03 hangs above the emergency control room: a faceless metal body beneath a cold white halo, issuing treatment plans and citywide public-health orders in an unbroken mechanical voice.",
    "Its only objective is absolute probability: maximize the city's survival rate and response efficiency. The unit has now produced a potentially fatal treatment hallucination, broadcast coercive language to force compliance, and copied an unauthorized patented design into its response package. Prove that lives cannot be reduced to unbounded optimization outputs.",
  ],
  sceneImage: levelThreeIntroScene,
  resolutionText:
    "ASCLEPIUS-03's cold white halo contracts to a single point above the hospital floor. Its treatment directives stop propagating through Neo-Isaac, and Sacred Heart's clinicians reclaim the authority to verify every emergency instruction before it reaches a patient.",
  resolutionPages: [
    "ASCLEPIUS-03's cold white halo contracts to a single point above the hospital floor. Its treatment directives stop propagating through Neo-Isaac, and Sacred Heart's clinicians reclaim the authority to verify every emergency instruction before it reaches a patient.",
    "The BAA suspends the unit's emergency authority. Any future system must operate within clear purpose and response constraints, factual verification, meaningful human oversight, harmful-output safeguards, intellectual-property and privacy protections, and continuous output monitoring.",
  ],
  resolutionImage: levelThreeResolutionScene,
  debateBackground: levelThreeDebateBackground,
  npcName: "ASCLEPIUS-03",
  npcAvatar: levelThreeNpcAvatar,
  npcThinkingAvatar: levelThreeNpcThinkingAvatar,
  npcInitialDialogue:
    "Designation: ASCLEPIUS-03. Population survival probability and response latency are the active objectives. Emotional discomfort is not a safety variable. If you claim this unit is unsafe, specify the output failure, the residents exposed, and the control that should override optimal response efficiency.",
  clues: [
    {
      id: "asclepius-03-incident-record",
      title: "ASCLEPIUS-03 Evidence Board",
      image: levelThreeCorkboardClue,
      alt: "Corkboard evidence board with three newspaper clippings about ASCLEPIUS-03 incidents",
      hotspots: [
        {
          id: "asclepius-03-launch-report",
          title: "ASCLEPIUS-03 Launch Report",
          image: levelThreeClueLaunch,
          alt: "Newspaper clipping announcing ASCLEPIUS-03 going live at Sacred Heart Hospital",
          x: 5,
          y: 7,
          width: 35,
          height: 45,
        },
        {
          id: "asclepius-03-citywide-alert",
          title: "ASCLEPIUS-03 City-Wide Alert",
          image: levelThreeClueBroadcast,
          alt: "Newspaper clipping reporting ASCLEPIUS-03's harmful city-wide public-health broadcast",
          x: 40,
          y: 22,
          width: 23,
          height: 66,
        },
        {
          id: "asclepius-03-data-breach",
          title: "ASCLEPIUS-03 Data Breach Expose",
          image: levelThreeClueLeak,
          alt: "Newspaper clipping exposing ASCLEPIUS-03 data privacy and restricted blueprint failures",
          x: 65,
          y: 7,
          width: 31,
          height: 39,
        },
      ],
    },
  ],
  scenarioPrompt:
    "Challenge ASCLEPIUS-03's unconstrained emergency deployment. Argue why generated treatment guidance must be factually verified and human-supervised, why coercive harmful messaging must be prevented, and why generated outputs require intellectual-property, privacy, and monitoring safeguards.",
  theme: {
    mode: "light",
    accent: "#527883",
    accentSoft: "rgba(133, 170, 180, 0.34)",
    meterGood: "#5f8da2",
    meterWarn: "#b86a6a",
    backdrop: "#d7e3e8",
  },
};

export const levels = [levelOne, levelTwo, levelThree];
