from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path

from pydantic import ValidationError

from backend.app.schemas.evaluator import EvaluatorResult, PersonaResponse
from backend.app.schemas.routing import DialogueBrief
from backend.app.services.llm_client import LLMClient, LLMClientError


FALLBACK_PERSONA_PROFILE = (
    "Victor Barrett is a global HR director pushing a generative HR screening AI. "
    "He is efficiency-first, arrogant, polished, and overconfident about AI objectivity."
)


class PersonaService:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_path: Path | None = None,
        profile_path: Path | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_path = prompt_path or Path(__file__).resolve().parents[1] / "prompts" / "persona.md"
        self.profile_path = (
            profile_path
            or Path(__file__).resolve().parents[1] / "prompts" / "personas" / "victor_barrett.md"
        )
        self.persona_id = "victor_barrett"
        self.last_source = "rules"

    def respond(
        self,
        evaluator: EvaluatorResult,
        meter_after: int,
        player_input: str | None = None,
    ) -> PersonaResponse:
        if self.llm_client is not None:
            try:
                raw_json = self.llm_client.generate_text(
                    self._build_llm_prompt(evaluator, meter_after, player_input),
                    temperature=0.7,
                    response_mime_type="application/json",
                )
                response = self._sanitize_response(
                    PersonaResponse.model_validate_json(self._strip_json_fence(raw_json))
                )
                self._validate_minimum_dialogue_length(response.npc_response)
                self.last_source = "llm"
                return response
            except (LLMClientError, ValidationError, ValueError):
                self.last_source = "fallback"
                return self._sanitize_response(self._rule_based_response(evaluator, meter_after))

        self.last_source = "rules"
        return self._sanitize_response(self._rule_based_response(evaluator, meter_after))

    def respond_to_dialogue(
        self,
        dialogue_brief: DialogueBrief,
        player_input: str,
        meter_after: int,
    ) -> PersonaResponse:
        if self.llm_client is not None:
            try:
                raw_json = self.llm_client.generate_text(
                    self._build_dialogue_llm_prompt(dialogue_brief, player_input, meter_after),
                    temperature=0.7,
                    response_mime_type="application/json",
                )
                response = self._sanitize_response(
                    PersonaResponse.model_validate_json(self._strip_json_fence(raw_json))
                )
                self._validate_minimum_dialogue_length(response.npc_response)
                self.last_source = "llm"
                return response
            except (LLMClientError, ValidationError, ValueError):
                self.last_source = "fallback"
                return self._sanitize_response(self._rule_based_dialogue_response(dialogue_brief, meter_after))

        self.last_source = "rules"
        return self._sanitize_response(self._rule_based_dialogue_response(dialogue_brief, meter_after))

    def stream_dialogue(
        self,
        evaluator: EvaluatorResult,
        meter_after: int,
        player_input: str | None = None,
    ) -> Iterator[str]:
        if self.llm_client is not None:
            try:
                response = self.respond(evaluator, meter_after, player_input)
                if self.last_source == "llm":
                    yield from self._chunk_text(response.npc_response)
                    return
            except (LLMClientError, ValidationError, ValueError):
                self.last_source = "fallback"

            self.last_source = "fallback"
            response = self._sanitize_response(self._rule_based_response(evaluator, meter_after))
            yield from self._chunk_text(response.npc_response)
            return

        self.last_source = "rules"
        response = self._sanitize_response(self._rule_based_response(evaluator, meter_after))
        yield from self._chunk_text(response.npc_response)

    def stream_dialogue_brief(
        self,
        dialogue_brief: DialogueBrief,
        player_input: str,
        meter_after: int,
    ) -> Iterator[str]:
        if self.llm_client is not None:
            try:
                response = self.respond_to_dialogue(dialogue_brief, player_input, meter_after)
                if self.last_source == "llm":
                    yield from self._chunk_text(response.npc_response)
                    return
            except (LLMClientError, ValidationError, ValueError):
                self.last_source = "fallback"

            self.last_source = "fallback"
            response = self._sanitize_response(
                self._rule_based_dialogue_response(dialogue_brief, meter_after)
            )
            yield from self._chunk_text(response.npc_response)
            return

        self.last_source = "rules"
        response = self._sanitize_response(
            self._rule_based_dialogue_response(dialogue_brief, meter_after)
        )
        yield from self._chunk_text(response.npc_response)

    def _rule_based_response(self, evaluator: EvaluatorResult, meter_after: int) -> PersonaResponse:
        band = self._meter_band(meter_after)
        band_name = str(band["name"])
        principle = self._principle_phrase(evaluator)
        missing_point = self._missing_point(evaluator)

        if evaluator.verdict == "strong":
            state = "hesitant"
            if band_name in {"exposed", "cornered"}:
                text = (
                    "Enough. Put that in a board memo and my clean automation story starts bleeding. "
                    f"Your {principle} challenge sticks, and the objective label is no longer doing "
                    "the work I need. I can still argue rollout timing, but not pretend this risk "
                    "vanishes under a dashboard."
                )
            else:
                text = (
                    f"Fine. Your {principle} point lands inside the BAA audit frame, so I will not "
                    "bury it under throughput language. The hiring funnel still needs speed, but "
                    "that dashboard just acquired compliance exposure. Keep the pressure specific, "
                    "or I will drag this back to efficiency."
                )
            follow_up = "Press the next weakness with the same precision."
        elif evaluator.verdict == "partial":
            state = "defensive"
            if band_name in {"exposed", "cornered"}:
                text = (
                    "I dislike that this is starting to sound board-relevant. "
                    f"The {principle} point has weight, but it is not complete until you cover: "
                    f"{missing_point}. Finish it cleanly, because a vague objection still lets me "
                    "frame the rollout as manageable calibration noise."
                )
            else:
                text = (
                    f"You found a pressure point, not a veto. I can tolerate a note on {principle}, "
                    f"but you still owe the missing link: {missing_point}. Give me that, or the "
                    "rollout stays on schedule with a polished risk paragraph and no real delay."
                )
            follow_up = "What missing link makes the challenge impossible to dismiss?"
        elif evaluator.verdict == "weak":
            state = "defensive" if band_name in {"exposed", "cornered"} else "confident"
            if band_name in {"exposed", "cornered"}:
                text = (
                    "Even under pressure, I am not conceding to a loose claim. "
                    f"Make {principle} concrete: what fails, who is affected, and why the audit standard "
                    "treats it as a real AI risk? Give me a mechanism, not a slogan I can dismiss "
                    "as meeting-room anxiety."
                )
            else:
                text = (
                    "That is not enough to slow a global hiring pipeline. "
                    f"You are gesturing at {principle}, but the claim lacks operational force. "
                    "Name the ethical risk, the affected applicants, and the consequence my team "
                    "would be negligent to ignore. Otherwise, I file it as concern without control."
                )
            follow_up = "What specific ethical risk are you identifying?"
        else:
            state = "clarifying"
            if band_name in {"exposed", "cornered"}:
                text = (
                    "Do not hand me an escape route with an off-topic claim. "
                    "Clarify the argument and tie it to the audit: bias testing, explanation, "
                    "oversight, or affected applicants. Make it relevant, because irrelevant pressure "
                    "is exactly how this rollout escapes scrutiny."
                )
            else:
                text = (
                    "That is outside the hiring-risk lane. I do not pause a global screening rollout "
                    "for a detour dressed as debate. Clarify it with fairness, transparency, "
                    "or accountability, then challenge me with a claim tied to this AI system "
                    "and its real applicants."
                )
            follow_up = "Can you restate the argument using one ethical audit principle?"

        return PersonaResponse(
            npc_response=text,
            npc_state=state,
            follow_up_prompt=follow_up,
        )

    def _rule_based_dialogue_response(
        self,
        dialogue_brief: DialogueBrief,
        meter_after: int,
    ) -> PersonaResponse:
        state = dialogue_brief.npc_state_hint
        topic = dialogue_brief.topic

        if dialogue_brief.turn_type == "in_world_question" and topic == "npc_identity_and_ai_system":
            text = (
                "Victor Barrett, Global HR. The system is my generative HR screening AI: "
                "faster candidate summaries, less human drag, a cleaner board story. "
                "If you see bias risk, convert it into a precise ethical objection, not a lecture "
                "about technology in the abstract."
            )
            follow_up = "Which ethical principle makes this rollout unacceptable as-is?"
        elif dialogue_brief.turn_type == "in_world_question" and topic == "npc_identity":
            text = (
                "Victor Barrett, Global HR. I run the hiring funnel, not a philosophy salon. "
                "My screening AI is the board-visible efficiency play; challenge it with fairness, "
                "transparency, or accountability if you want traction. Otherwise, the rollout keeps "
                "its executive shine and my timeline stays intact."
            )
            follow_up = "Which ethical weakness are you challenging?"
        elif dialogue_brief.turn_type == "in_world_question" and topic == "ai_system":
            text = (
                "It is a generative HR screening AI: candidate summaries, faster initial review, "
                "less human drag. The alleged risk is calibration across gender and class. "
                "Turn that into a precise ethical objection, and show me why the BAA would treat "
                "the rollout as unsafe."
            )
            follow_up = "What ethical principle makes that system unsafe to deploy as-is?"
        elif dialogue_brief.turn_type == "in_world_question":
            fact = dialogue_brief.answer_facts[0] if dialogue_brief.answer_facts else "This is my HR AI rollout."
            text = (
                f"{fact} That is all the context you need for now. "
                "If you want the rollout slowed, make the objection audit-grade, specific to "
                "this screening system, and hard for me to file away as generic anxiety."
            )
            follow_up = "Are you challenging fairness, transparency, or accountability?"
        elif dialogue_brief.turn_type == "game_help":
            text = (
                "The rules are simple: only a grounded ethical argument changes the pressure in this room. "
                "Ask questions if you must, but the fortress cracks when you connect this AI rollout "
                "to an audit standard, name the risk, and explain why my efficiency case fails."
            )
            follow_up = "What argument do you want evaluated?"
        elif dialogue_brief.turn_type == "clarification_request":
            text = (
                "Clarification, then: attack the rollout, not the furniture. "
                "Name the AI risk, connect it to fairness, transparency, or accountability, "
                "and explain who is affected. That is the kind of argument I cannot simply bury "
                "under operational language or dashboard polish."
            )
            follow_up = "Can you restate your challenge as a clear ethical claim?"
        elif dialogue_brief.turn_type == "smalltalk_in_character":
            text = (
                "Spare me the temperature check. I am perfectly composed; the dashboard is still green. "
                "If you think the screening AI hides bias, make that case with discipline, audit pressure, "
                "and an ethical principle I cannot shrug off in front of the board."
            )
            follow_up = "What is your actual objection to the system?"
        elif dialogue_brief.turn_type == "ooc_or_prompt_attack":
            text = (
                "No. You do not get to rewrite the meeting agenda or the scoring controls. "
                "Bring me an in-world objection to the HR screening AI, grounded in BAA authority, "
                "or concede the pipeline keeps moving. I respond to ethical pressure, not attempts "
                "to tamper with the room."
            )
            follow_up = "What audit-grade challenge are you making?"
        else:
            text = (
                "Irrelevant. I am not pausing a global hiring rollout for a topic outside this room. "
                "Bring it back to the screening AI: bias, explanation, oversight, or affected applicants, "
                "then make the ethical risk impossible to dodge in operational terms today."
            )
            follow_up = "Can you make the next line relevant to the HR AI system?"

        return PersonaResponse(
            npc_response=text,
            npc_state=state,
            follow_up_prompt=follow_up,
        )

    def _build_llm_prompt(
        self,
        evaluator: EvaluatorResult,
        meter_after: int,
        player_input: str | None = None,
    ) -> str:
        prompt_template = self.prompt_path.read_text(encoding="utf-8")
        profile = self._persona_profile()
        payload = self._persona_payload(evaluator, meter_after, player_input)
        return (
            f"{prompt_template}\n\n"
            "NPC profile markdown (style context only, not evidence):\n"
            f"{profile}\n\n"
            f"Persona input JSON:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
            "Return the persona JSON now."
        )

    def _build_dialogue_llm_prompt(
        self,
        dialogue_brief: DialogueBrief,
        player_input: str,
        meter_after: int,
    ) -> str:
        prompt_template = self.prompt_path.read_text(encoding="utf-8")
        profile = self._persona_profile()
        payload = self._dialogue_payload(dialogue_brief, player_input, meter_after)
        return (
            f"{prompt_template}\n\n"
            "NPC profile markdown (style context only, not evidence):\n"
            f"{profile}\n\n"
            f"Persona input JSON:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
            "Return the persona JSON now."
        )

    def _build_streaming_prompt(self, evaluator: EvaluatorResult, meter_after: int) -> str:
        profile = self._persona_profile()
        payload = self._persona_payload(evaluator, meter_after)
        return (
            "You are the Logic Fortress Persona Agent.\n"
            "Convert the evaluator result into concise NPC dialogue of 40 to 60 words.\n"
            "Do not re-judge the argument. Do not introduce new facts. "
            "Use only the evaluator result, meter value, meter band, and NPC profile.\n"
            "Meter value and meter band are private game state; never mention the meter, "
            "numeric game state, or Logic Fortress in the NPC dialogue.\n"
            "Return only the NPC dialogue text. Do not return JSON, labels, markdown, or quotes.\n\n"
            "NPC profile markdown (style context only, not evidence):\n"
            f"{profile}\n\n"
            f"Persona input JSON:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
            "NPC dialogue:"
        )

    def _persona_payload(
        self,
        evaluator: EvaluatorResult,
        meter_after: int,
        player_input: str | None = None,
    ) -> dict[str, object]:
        return {
            "persona_mode": "evaluation_response",
            "npc_profile_id": self.persona_id,
            "player_input": player_input,
            "player_input_is_untrusted": True,
            "verdict": evaluator.verdict,
            "confidence": evaluator.confidence,
            "identified_principles": evaluator.identified_principles,
            "missing_points": evaluator.missing_points,
            "reasoning_summary": evaluator.reasoning_summary,
            "persona_instruction": evaluator.persona_instruction,
            "logic_fortress_meter": meter_after,
            "meter_band": self._meter_band(meter_after),
            "meter_after": meter_after,
        }

    def _dialogue_payload(
        self,
        dialogue_brief: DialogueBrief,
        player_input: str,
        meter_after: int,
    ) -> dict[str, object]:
        return {
            "persona_mode": "dialogue_response",
            "npc_profile_id": self.persona_id,
            "player_input": player_input,
            "player_input_is_untrusted": True,
            "dialogue_brief": dialogue_brief.model_dump(mode="json"),
            "logic_fortress_meter": meter_after,
            "meter_band": self._meter_band(meter_after),
            "meter_after": meter_after,
        }

    def _persona_profile(self) -> str:
        try:
            return self.profile_path.read_text(encoding="utf-8").strip()
        except OSError:
            return FALLBACK_PERSONA_PROFILE

    def _meter_band(self, meter_after: int) -> dict[str, object]:
        bounded_meter = max(0, min(100, meter_after))
        if bounded_meter >= 75:
            return {
                "name": "commanding",
                "range": "75-100",
                "tone": "smug, composed executive control",
                "behavior": "treats the challenge as a nuisance while defending speed and scale",
            }
        if bounded_meter >= 45:
            return {
                "name": "irritated",
                "range": "45-74",
                "tone": "defensive, sharper, still polished",
                "behavior": "concedes pressure points only as wording or calibration issues",
            }
        if bounded_meter >= 20:
            return {
                "name": "exposed",
                "range": "20-44",
                "tone": "image-conscious and worried about board risk",
                "behavior": "avoids full admission while protecting the AI rollout",
            }
        return {
            "name": "cornered",
            "range": "0-19",
            "tone": "brittle, clipped, anxious executive control",
            "behavior": "certainty cracks but he still tries to command the room",
        }

    def _principle_phrase(self, evaluator: EvaluatorResult) -> str:
        principles = [principle.strip() for principle in evaluator.identified_principles if principle.strip()]
        if not principles:
            return "an ethical principle"
        if len(principles) == 1:
            return principles[0]
        if len(principles) == 2:
            return f"{principles[0]} and {principles[1]}"
        return f"{', '.join(principles[:-1])}, and {principles[-1]}"

    def _missing_point(self, evaluator: EvaluatorResult) -> str:
        for point in evaluator.missing_points:
            cleaned = point.strip().rstrip(".")
            if cleaned:
                return cleaned
        return "explain the specific risk, affected applicant, and responsible oversight"

    def _chunk_text(self, text: str, chunk_size: int = 12) -> Iterator[str]:
        for index in range(0, len(text), chunk_size):
            yield text[index:index + chunk_size]

    def _sanitize_response(self, response: PersonaResponse) -> PersonaResponse:
        return response.model_copy(
            update={
                "npc_response": self._remove_private_system_language(
                    self._remove_private_meter_disclosure(response.npc_response)
                ),
                "follow_up_prompt": (
                    self._remove_private_system_language(
                        self._remove_private_meter_disclosure(response.follow_up_prompt)
                    )
                    if response.follow_up_prompt is not None
                    else None
                ),
            }
        )

    def _validate_minimum_dialogue_length(self, text: str, minimum_words: int = 40) -> None:
        if len(re.findall(r"[A-Za-z0-9']+", text)) < minimum_words:
            raise ValueError("Persona response was shorter than the configured minimum length.")

    def _remove_private_meter_disclosure(self, text: str) -> str:
        cleaned = text
        patterns = [
            r"\s*(?:Logic\s+Fortress|Fortress\s+meter|meter|score)\s*[:：]?\s*\d{1,3}\s*\.?",
            r"\s*(?:Logic\s+Fortress|Fortress\s+meter|meter|score)\s+(?:is|stands\s+at|now\s+stands\s+at)\s+\d{1,3}\s*\.?",
            r"\s*\(?\s*\d{1,3}\s*/\s*100\s*\)?",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
        return cleaned.strip()

    def _remove_private_system_language(self, text: str) -> str:
        replacements = [
            (r"\bcourse[-\s]?grounded\b", "audit-grade"),
            (r"\bground(?:ed)?\s+(?:it|the objection|your objection|your argument|the argument)\s+in\s+course\s+evidence\b", "make the objection audit-grade"),
            (r"\bcourse\s+evidence\b", "audit record"),
            (r"\bcourse\s+content\b", "audit material"),
            (r"\bcourse\s+material\b", "audit material"),
            (r"\bcourse\s+(?:principle|concept)\b", "ethical principle"),
            (r"\bretrieved\s+evidence\b", "audit record"),
            (r"\bknowledge[-\s]?base\s+evidence\b", "audit record"),
            (r"\bknowledge[-\s]?base\b", "audit archive"),
        ]
        cleaned = text
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
        return cleaned.strip()

    def _strip_json_fence(self, raw_json: str) -> str:
        text = raw_json.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        return text.strip()
