from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from backend.app.repositories.app_repository import AppRepository
from backend.app.schemas.evaluator import EvidenceRef
from backend.app.schemas.turn import DebateTurnResponse
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.level_persuasion_service import LevelPersuasionService
from backend.app.services.meter_service import MeterService
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService


class DebateOrchestrator:
    def __init__(
        self,
        app_repository: AppRepository,
        retrieval_service: RetrievalService,
        evaluation_service: EvaluationService,
        persona_service: PersonaService,
        meter_service: MeterService,
        conversation_context_service: ConversationContextService | None = None,
        level_persuasion_service: LevelPersuasionService | None = None,
    ) -> None:
        self.app_repository = app_repository
        self.retrieval_service = retrieval_service
        self.evaluation_service = evaluation_service
        self.persona_service = persona_service
        self.meter_service = meter_service
        self.conversation_context_service = conversation_context_service or ConversationContextService()
        self.level_persuasion_service = level_persuasion_service or LevelPersuasionService()

    def submit_turn(self, session_id: int, player_input: str) -> DebateTurnResponse:
        session = self.app_repository.get_session(session_id)
        meter_before = session.fortress_meter

        context = self._conversation_context(session_id)
        retrieval_query = self.conversation_context_service.build_retrieval_query(player_input, context)
        evidence = self.retrieval_service.retrieve(retrieval_query)
        evaluator_context = self.conversation_context_service.context_for_evaluation(player_input, context)
        evaluator = self.evaluation_service.evaluate(player_input, evidence, evaluator_context)
        evaluator_source = self.evaluation_service.last_source
        persuasion_refs = self._persuasion_refs(player_input, evidence)
        evaluator = self.level_persuasion_service.apply(
            level_id=session.current_level,
            meter_before=meter_before,
            player_input=player_input,
            retrieved_refs=persuasion_refs,
            evaluator=evaluator,
            prior_turns=self.app_repository.fetch_turns(session_id),
        )
        meter_after = self.meter_service.apply_delta(meter_before, evaluator.score_delta)
        persona = self.persona_service.respond(
            evaluator,
            meter_after,
            player_input,
            dialogue_history=self._persona_context(session_id),
            level_id=session.current_level,
        )
        persona_source = self.persona_service.last_source
        turn_index = self.app_repository.next_turn_index(session_id)
        self.app_repository.persist_turn(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            retrieved_refs=persuasion_refs,
            evaluator=evaluator,
            npc_response=persona.npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
        )
        return DebateTurnResponse(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            retrieved_refs=evidence,
            evaluator=evaluator,
            npc_response=persona.npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
            score_delta=evaluator.score_delta,
            evaluator_source=evaluator_source,
            persona_source=persona_source,
        )

    def stream_turn_events(self, session_id: int, player_input: str) -> Iterator[dict[str, Any]]:
        session = self.app_repository.get_session(session_id)
        meter_before = session.fortress_meter

        yield {"event": "phase", "phase": "retrieving"}
        context = self._conversation_context(session_id)
        retrieval_query = self.conversation_context_service.build_retrieval_query(player_input, context)
        evidence = self.retrieval_service.retrieve(retrieval_query)

        yield {"event": "phase", "phase": "evaluating"}
        evaluator_context = self.conversation_context_service.context_for_evaluation(player_input, context)
        evaluator = self.evaluation_service.evaluate(player_input, evidence, evaluator_context)
        evaluator_source = self.evaluation_service.last_source
        persuasion_refs = self._persuasion_refs(player_input, evidence)
        evaluator = self.level_persuasion_service.apply(
            level_id=session.current_level,
            meter_before=meter_before,
            player_input=player_input,
            retrieved_refs=persuasion_refs,
            evaluator=evaluator,
            prior_turns=self.app_repository.fetch_turns(session_id),
        )
        meter_after = self.meter_service.apply_delta(meter_before, evaluator.score_delta)
        yield {
            "event": "evaluator_complete",
            "verdict": evaluator.verdict,
            "confidence": evaluator.confidence,
            "meter_before": meter_before,
            "meter_after": meter_after,
            "score_delta": evaluator.score_delta,
            "evaluator_source": evaluator_source,
        }

        yield {"event": "phase", "phase": "persona"}
        npc_chunks: list[str] = []
        for chunk in self.persona_service.stream_dialogue(
            evaluator,
            meter_after,
            player_input,
            dialogue_history=self._persona_context(session_id),
            level_id=session.current_level,
        ):
            npc_chunks.append(chunk)
            yield {"event": "persona_delta", "text": chunk}

        npc_response = "".join(npc_chunks).strip()
        persona_source = self.persona_service.last_source
        turn_index = self.app_repository.next_turn_index(session_id)
        self.app_repository.persist_turn(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            retrieved_refs=persuasion_refs,
            evaluator=evaluator,
            npc_response=npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
        )
        response = DebateTurnResponse(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            retrieved_refs=evidence,
            evaluator=evaluator,
            npc_response=npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
            score_delta=evaluator.score_delta,
            evaluator_source=evaluator_source,
            persona_source=persona_source,
        )
        yield {"event": "complete", "turn": response.model_dump(mode="json")}

    def _persuasion_refs(
        self, player_input: str, evidence: list[EvidenceRef]
    ) -> list[EvidenceRef]:
        """Evidence used for persuasion-target matching.

        Evaluation retrieves with a query expanded from recent turns, which
        keeps short follow-ups meaningful. That expansion also makes the result
        depend on what was said earlier, so the same argument can match a
        target on one turn and miss it on the next. Persuasion progress must
        not depend on conversation order, so it is matched against a retrieval
        on the raw input instead. Retrieval is inexpensive relative to the rest
        of a turn, so running it a second time is cheaper than the alternatives.
        """
        raw_refs = self.retrieval_service.retrieve(player_input)
        merged = {ref.document_id: ref for ref in evidence}
        merged.update({ref.document_id: ref for ref in raw_refs})
        return list(merged.values())

    def _conversation_context(self, session_id: int):
        recent_turns = self.app_repository.fetch_recent_turns(
            session_id,
            self.conversation_context_service.max_turns,
        )
        return self.conversation_context_service.build_context(recent_turns)

    def _persona_context(self, session_id: int) -> dict[str, object]:
        recent_turns = self.app_repository.fetch_recent_turns(
            session_id,
            self.conversation_context_service.max_turns,
        )
        return self.conversation_context_service.build_persona_context(recent_turns)
