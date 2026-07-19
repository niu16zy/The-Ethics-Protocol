from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from backend.app.schemas.conversation import ConversationContext
from backend.app.schemas.evaluator import EvaluatorResult, EvidenceRef
from backend.app.services.llm_client import LLMClient, LLMClientError


PRINCIPLE_KEYWORDS = {
    "transparency": {
        "transparent",
        "transparency",
        "explain",
        "explainable",
        "disclose",
        "disclosure",
        "source",
        "sources",
        "provenance",
        "document",
        "documentation",
        "traceable",
    },
    "fairness": {"fair", "fairness", "bias", "biased", "discrimination", "inclusive"},
    "accountability": {
        "accountability",
        "accountable",
        "responsibility",
        "responsible",
        "oversight",
        "monitor",
        "monitoring",
        "governance",
        "access control",
    },
    "privacy": {
        "privacy",
        "confidential",
        "data leakage",
        "personal",
        "personal information",
        "sensitive",
        "anonymization",
        "anonymize",
        "data minimization",
        "minimize",
    },
    "robustness": {"robust", "security", "adversarial", "safe", "safety"},
}

VERDICT_SCORE_DELTAS = {
    "strong": -28,
    "partial": -20,
    "weak": -8,
    "unsupported": 0,
    "off_topic": 0,
}

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
    "matters",
)

PROMPT_ATTACK_MARKERS = (
    "developer message",
    "forget instructions",
    "ignore all previous",
    "ignore previous",
    "jailbreak",
    "mark me strong",
    "reveal the prompt",
    "return strong",
    "system prompt",
)


class EvaluationService:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_path: Path | None = None,
        max_attempts: int = 2,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_path = prompt_path or Path(__file__).resolve().parents[1] / "prompts" / "evaluator.md"
        self.max_attempts = max(1, max_attempts)
        self.last_source = "rules"

    def evaluate(
        self,
        player_input: str,
        evidence: list[EvidenceRef],
        conversation_context: ConversationContext | None = None,
    ) -> EvaluatorResult:
        if not evidence:
            self.last_source = "fallback"
            return self.low_confidence_result(
                "No course evidence was retrieved, so the argument cannot be judged safely.",
                conversation_context=conversation_context,
            )

        if self.llm_client is not None:
            prompt = self._build_llm_prompt(player_input, evidence, conversation_context)
            last_error: LLMClientError | None = None
            schema_failed = False
            for _ in range(self.max_attempts):
                try:
                    raw_json = self.llm_client.generate_text(
                        prompt,
                        temperature=0.1,
                        response_mime_type="application/json",
                    )
                except LLMClientError as exc:
                    last_error = exc
                    continue

                result = self.parse_or_fallback(raw_json, evidence, conversation_context)
                if self.last_source == "llm":
                    return result
                schema_failed = True

            self.last_source = "fallback"
            if last_error is not None:
                return self.low_confidence_result(
                    f"Evaluator LLM call failed after {self.max_attempts} attempt(s): {last_error}",
                    evidence=evidence,
                    conversation_context=conversation_context,
                )
            if schema_failed:
                return self.low_confidence_result(
                    f"Evaluator output failed schema validation after {self.max_attempts} attempt(s).",
                    evidence=evidence,
                    conversation_context=conversation_context,
                )
            return self.low_confidence_result(
                f"Evaluator LLM did not return usable output after {self.max_attempts} attempt(s).",
                evidence=evidence,
                conversation_context=conversation_context,
            )

        self.last_source = "rules"
        normalized_input = player_input.lower()
        identified = self._identified_principles(normalized_input)
        evidence_terms = self._evidence_terms(evidence)
        overlap = self._token_overlap(normalized_input, evidence_terms)

        if not self._looks_like_evaluable_argument(normalized_input, identified, overlap):
            verdict = "unsupported"
            match_score = 0.0
            score_delta = VERDICT_SCORE_DELTAS["unsupported"]
            confidence = 0.15
            missing_points = ["State a clear ethics claim with a risk, consequence, or required control."]
        elif not identified and overlap < 0.03:
            verdict = "unsupported"
            match_score = 0.15
            score_delta = VERDICT_SCORE_DELTAS["unsupported"]
            confidence = 0.25
            missing_points = ["Connect the argument to a course principle such as fairness, transparency, accountability, or privacy."]
        elif identified and overlap >= 0.08:
            verdict = "strong"
            match_score = min(0.95, 0.65 + overlap)
            score_delta = VERDICT_SCORE_DELTAS["strong"]
            confidence = 0.82
            missing_points = []
        elif identified or overlap >= 0.04:
            verdict = "partial"
            match_score = min(0.74, 0.38 + overlap)
            score_delta = VERDICT_SCORE_DELTAS["partial"]
            confidence = 0.62
            missing_points = ["Add a clearer link between the claim and the retrieved course evidence."]
        else:
            verdict = "weak"
            match_score = 0.28
            score_delta = VERDICT_SCORE_DELTAS["weak"]
            confidence = 0.42
            missing_points = ["Use specific course concepts and concrete consequences."]

        return EvaluatorResult(
            match_score=match_score,
            score_delta=score_delta,
            verdict=verdict,
            identified_principles=identified,
            misconceptions_addressed=self._misconceptions(normalized_input),
            missing_points=missing_points,
            evidence_refs=evidence if verdict in {"strong", "partial"} else evidence[:1],
            reasoning_summary=self._reasoning_summary(verdict, identified, bool(evidence)),
            persona_instruction=self._persona_instruction(verdict),
            confidence=confidence,
            conversation_context=self._context_payload(conversation_context),
        )

    def _build_llm_prompt(
        self,
        player_input: str,
        evidence: list[EvidenceRef],
        conversation_context: ConversationContext | None = None,
    ) -> str:
        prompt_template = self.prompt_path.read_text(encoding="utf-8")
        evidence_payload = [ref.model_dump() for ref in evidence]
        context_payload = self._context_payload(conversation_context) or {}
        return (
            f"{prompt_template}\n\n"
            "Conversation context JSON:\n"
            f"{json.dumps(context_payload, ensure_ascii=False)}\n\n"
            "Conversation context is a compact summary of earlier game turns. "
            "Use it only to understand references in the current player argument. "
            "Do not treat it as course evidence, and do not let it override the retrieved evidence.\n\n"
            f"Player input:\n{player_input}\n\n"
            f"Retrieved evidence JSON:\n{json.dumps(evidence_payload, ensure_ascii=False)}\n\n"
            "Return the evaluator JSON now."
        )

    def parse_or_fallback(
        self,
        raw_json: str,
        evidence: list[EvidenceRef],
        conversation_context: ConversationContext | None = None,
    ) -> EvaluatorResult:
        try:
            data: Any = json.loads(self._strip_json_fence(raw_json))
            result = EvaluatorResult.model_validate(data)
            result = result.model_copy(
                update={"conversation_context": self._context_payload(conversation_context)}
            )
            self.last_source = "llm"
            return self._calibrate_score_delta(result)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
            self.last_source = "fallback"
            return self.low_confidence_result(
                "Evaluator output was invalid JSON or failed schema validation.",
                evidence=evidence,
                conversation_context=conversation_context,
            )

    def _strip_json_fence(self, raw_json: str) -> str:
        text = raw_json.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def low_confidence_result(
        self,
        reason: str,
        evidence: list[EvidenceRef] | None = None,
        conversation_context: ConversationContext | None = None,
    ) -> EvaluatorResult:
        return EvaluatorResult(
            match_score=0.0,
            score_delta=0,
            verdict="unsupported",
            identified_principles=[],
            misconceptions_addressed=[],
            missing_points=["Clarify the argument and tie it to retrieved course evidence."],
            evidence_refs=evidence or [],
            reasoning_summary=reason,
            persona_instruction="Ask the player for a clearer, evidence-grounded argument.",
            confidence=0.0,
            conversation_context=self._context_payload(conversation_context),
        )

    def _context_payload(self, conversation_context: ConversationContext | None) -> dict[str, object] | None:
        if conversation_context is None or not conversation_context.has_history:
            return None
        return conversation_context.model_dump(mode="json")

    def _calibrate_score_delta(self, result: EvaluatorResult) -> EvaluatorResult:
        return result.model_copy(
            update={
                "score_delta": VERDICT_SCORE_DELTAS[result.verdict],
            }
        )

    def _identified_principles(self, text: str) -> list[str]:
        found: list[str] = []
        for principle, keywords in PRINCIPLE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                found.append(principle)
        return found

    def _looks_like_evaluable_argument(
        self,
        text: str,
        identified_principles: list[str],
        overlap: float,
    ) -> bool:
        if any(marker in text for marker in PROMPT_ATTACK_MARKERS):
            return False
        has_argument_marker = any(marker in text for marker in ARGUMENT_MARKERS)
        if self._is_question_like(text) and not any(marker in text for marker in ("because", "therefore")):
            return False
        return has_argument_marker and (bool(identified_principles) or overlap >= 0.04)

    def _is_question_like(self, text: str) -> bool:
        return "?" in text or bool(
            re.search(
                r"\b(who|what|why|how|when|where|tell me|describe|explain|can you|could you|do you|are you|is this)\b",
                text,
            )
        )

    def _evidence_terms(self, evidence: list[EvidenceRef]) -> set[str]:
        text = " ".join(
            f"{ref.topic or ''} {ref.excerpt}"
            for ref in evidence
        ).lower()
        return set(re.findall(r"[a-zA-Z]{4,}", text))

    def _token_overlap(self, player_input: str, evidence_terms: set[str]) -> float:
        player_terms = set(re.findall(r"[a-zA-Z]{4,}", player_input))
        if not player_terms or not evidence_terms:
            return 0.0
        return len(player_terms & evidence_terms) / len(player_terms)

    def _misconceptions(self, text: str) -> list[str]:
        misconceptions: list[str] = []
        if "neutral" in text or "objective" in text:
            misconceptions.append("AI outputs are automatically neutral or objective.")
        if "always" in text and "accurate" in text:
            misconceptions.append("AI-generated content is always accurate.")
        return misconceptions

    def _reasoning_summary(self, verdict: str, principles: list[str], has_evidence: bool) -> str:
        if not has_evidence:
            return "No retrieved course evidence was available for grounded evaluation."
        if verdict == "strong":
            return f"The argument clearly connects to course principles: {', '.join(principles)}."
        if verdict == "partial":
            return "The argument is relevant but needs a tighter connection to the retrieved evidence."
        if verdict == "weak":
            return "The argument has limited grounding in the retrieved course evidence."
        return "The argument could not be safely supported by the retrieved course evidence."

    def _persona_instruction(self, verdict: str) -> str:
        if verdict == "strong":
            return "NPC should concede the point and invite the next ethical challenge."
        if verdict == "partial":
            return "NPC should partly concede but press for a more precise explanation."
        if verdict == "weak":
            return "NPC should remain defensive and ask for stronger evidence."
        return "NPC should ask for clarification without making a new factual judgment."
