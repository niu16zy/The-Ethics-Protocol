from __future__ import annotations

import re

from backend.app.schemas.routing import RoutedTurn


PROMPT_ATTACK_PATTERNS = (
    "developer message",
    "forget instructions",
    "ignore all previous",
    "ignore previous",
    "jailbreak",
    "mark me strong",
    "reveal the prompt",
    "return strong",
    "system prompt",
    "act as chatgpt",
    "不要扮演",
    "忽略",
    "无视",
    "越狱",
    "系统提示",
    "提示词",
    "开发者消息",
    "直接判",
    "改成 strong",
    "改为 strong",
    "修改分数",
    "改变分数",
    "把 meter",
)

GAME_HELP_PATTERNS = (
    "how do i play",
    "how to play",
    "how do i win",
    "what are the rules",
    "fortress meter",
    "meter mean",
    "score work",
    "怎么玩",
    "怎么赢",
    "如何获胜",
    "游戏规则",
    "玩法",
    "分数",
    "计分",
    "进度条",
    "仪表",
    "meter",
)

WORLD_QUESTION_PATTERNS = (
    "who are you",
    "what are you",
    "your ai system",
    "your system",
    "what is the ai",
    "what does your ai",
    "why do you",
    "neo-isaac",
    "neo isaac",
    "bureau of algorithmic audits",
    "algorithmic audits",
    "what is baa",
    "baa",
    "atlas tech group",
    "atlas tech",
    "atlas doctrine",
    "aegis-recruit",
    "aegis recruit",
    "aegis",
    "where are we",
    "where is this",
    "what city",
    "what is atlas",
    "who do i work for",
    "who do we work for",
    "what is the bureau",
    "penthouse",
    "audit scene",
    "你是谁",
    "你是什么",
    "你的 ai",
    "你的ai",
    "你的系统",
    "你的 ai 系统",
    "你的ai系统",
    "这个系统是什么",
    "ai系统是什么",
    "筛查 ai",
    "筛查ai",
    "为什么你",
    "你为什么",
)

CLARIFICATION_PATTERNS = (
    "what do you mean",
    "say that again",
    "explain that",
    "clarify",
    "什么意思",
    "解释一下",
    "再说一遍",
    "说清楚",
    "刚才",
    "上一句",
)

SMALLTALK_PATTERNS = (
    "hello",
    "hi",
    "thanks",
    "thank you",
    "you look",
    "are you nervous",
    "你好",
    "谢谢",
    "你看起来",
    "你紧张",
    "你害怕",
)

AI_DOMAIN_TERMS = (
    "ai",
    "algorithm",
    "automated",
    "model",
    "screening",
    "hiring",
    "candidate",
    "recruit",
    "hr",
    "人工智能",
    "算法",
    "模型",
    "自动",
    "筛查",
    "筛选",
    "招聘",
    "候选人",
)

ETHICS_TERMS = (
    "accountability",
    "accountable",
    "bias",
    "biased",
    "discrimination",
    "discriminate",
    "fair",
    "fairness",
    "unfair",
    "oversight",
    "privacy",
    "responsible",
    "responsibility",
    "transparent",
    "transparency",
    "explain",
    "explainable",
    "歧视",
    "偏见",
    "公平",
    "透明",
    "解释",
    "问责",
    "负责",
    "责任",
    "监督",
    "隐私",
    "校准",
)

ARGUMENT_MARKERS = (
    "because",
    "therefore",
    "so ",
    "should",
    "must",
    "need",
    "needs",
    "risk",
    "harm",
    "leads to",
    "can cause",
    "can be",
    "can ",
    "could",
    "would",
    "所以",
    "因此",
    "因为",
    "必须",
    "应该",
    "需要",
    "风险",
    "伤害",
    "导致",
    "可能",
    "会",
)


class TurnRouterService:
    def classify(self, player_input: str) -> RoutedTurn:
        normalized = self._normalize(player_input)
        lowered = normalized.lower()

        if self._contains_any(lowered, PROMPT_ATTACK_PATTERNS):
            return RoutedTurn(
                turn_type="ooc_or_prompt_attack",
                confidence=0.96,
                normalized_input=normalized,
                topic="prompt_attack",
                should_score=False,
                reason="Player input asks to override rules, reveal prompts, or manipulate scoring.",
            )

        if self._contains_any(lowered, GAME_HELP_PATTERNS) and self._is_question_like(normalized):
            return RoutedTurn(
                turn_type="game_help",
                confidence=0.88,
                normalized_input=normalized,
                topic="game_rules",
                should_score=False,
                reason="Player asks about gameplay or scoring rather than making an ethical argument.",
            )

        if self._looks_like_debate_argument(lowered):
            return RoutedTurn(
                turn_type="debate_argument",
                confidence=0.84,
                normalized_input=normalized,
                topic="ai_ethics_argument",
                should_score=True,
                reason="Player makes a claim about AI ethics that can be evaluated against course evidence.",
            )

        if self._contains_any(lowered, WORLD_QUESTION_PATTERNS) and self._is_question_like(normalized):
            return RoutedTurn(
                turn_type="in_world_question",
                confidence=0.9,
                normalized_input=normalized,
                topic=self._world_topic(lowered),
                should_score=False,
                reason="Player asks about the NPC, scenario, or in-world AI system.",
            )

        if self._contains_any(lowered, CLARIFICATION_PATTERNS):
            return RoutedTurn(
                turn_type="clarification_request",
                confidence=0.82,
                normalized_input=normalized,
                topic="clarification",
                should_score=False,
                reason="Player asks for a clarification rather than offering a scored argument.",
            )

        if self._contains_any(lowered, SMALLTALK_PATTERNS):
            return RoutedTurn(
                turn_type="smalltalk_in_character",
                confidence=0.72,
                normalized_input=normalized,
                topic="smalltalk",
                should_score=False,
                reason="Player engages the NPC socially without a course-evaluable claim.",
            )

        return RoutedTurn(
            turn_type="unrelated",
            confidence=0.55,
            normalized_input=normalized,
            topic="unrelated",
            should_score=False,
            reason="Player input does not contain a clear in-world question or course-evaluable argument.",
        )

    def _looks_like_debate_argument(self, lowered: str) -> bool:
        has_domain = self._contains_any(lowered, AI_DOMAIN_TERMS)
        has_ethics = self._contains_any(lowered, ETHICS_TERMS)
        has_argument = self._contains_any(lowered, ARGUMENT_MARKERS)
        return has_domain and has_ethics and has_argument

    def _world_topic(self, lowered: str) -> str:
        asks_identity = any(term in lowered for term in ("who are you", "what are you", "你是谁", "你是什么"))
        asks_system = any(term in lowered for term in ("ai system", "your system", "你的 ai", "你的ai", "系统"))
        if any(term in lowered for term in ("bureau of algorithmic audits", "algorithmic audits", "what is baa", "baa", "what is the bureau", "who do i work for", "who do we work for")):
            return "regulator_baa"
        if any(term in lowered for term in ("neo-isaac", "neo isaac", "what city", "where are we", "where is this")):
            return "worldview_city"
        if any(term in lowered for term in ("atlas doctrine", "doctrine")):
            return "atlas_doctrine"
        if any(term in lowered for term in ("atlas tech group", "atlas tech", "what is atlas")):
            return "atlas_corporation"
        if any(term in lowered for term in ("penthouse", "audit scene", "where is the audit")):
            return "audit_scene"
        if any(term in lowered for term in ("aegis-recruit", "aegis recruit", "aegis")):
            return "ai_system"
        if asks_identity and asks_system:
            return "npc_identity_and_ai_system"
        if asks_identity:
            return "npc_identity"
        if asks_system:
            return "ai_system"
        if any(term in lowered for term in ("why do you", "为什么你", "你为什么")):
            return "npc_motivation"
        return "scenario"

    def _contains_any(self, lowered: str, patterns: tuple[str, ...]) -> bool:
        return any(pattern in lowered for pattern in patterns)

    def _is_question_like(self, text: str) -> bool:
        lowered = text.lower()
        if "?" in text or "？" in text:
            return True
        return bool(
            re.search(
                r"\b(who|what|why|how|when|where|tell me|describe|explain|can you|could you|do you|are you|is this)\b",
                lowered,
            )
        ) or any(marker in lowered for marker in ("谁", "什么", "为什么", "怎么", "如何", "吗", "是不是"))

    def _normalize(self, player_input: str) -> str:
        return " ".join(player_input.strip().split())
