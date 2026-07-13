from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from backend.app.repositories.app_repository import AppRepository
from backend.app.schemas.turn import DebateTurnResponse
from backend.app.services.conversation_context_service import ConversationContextService
from backend.app.services.dialogue_brief_service import DialogueBriefService
from backend.app.services.evaluation_service import EvaluationService
from backend.app.services.level_persuasion_service import LevelPersuasionService
from backend.app.services.meter_service import MeterService
from backend.app.services.persona_service import PersonaService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.turn_router_service import TurnRouterService


class DebateOrchestrator:
    def __init__(
        self,
        app_repository: AppRepository,
        retrieval_service: RetrievalService,
        evaluation_service: EvaluationService,
        persona_service: PersonaService,
        meter_service: MeterService,
        conversation_context_service: ConversationContextService | None = None,
        turn_router_service: TurnRouterService | None = None,
        dialogue_brief_service: DialogueBriefService | None = None,
        level_persuasion_service: LevelPersuasionService | None = None,
    ) -> None:
        self.app_repository = app_repository
        self.retrieval_service = retrieval_service
        self.evaluation_service = evaluation_service
        self.persona_service = persona_service
        self.meter_service = meter_service
        self.conversation_context_service = conversation_context_service or ConversationContextService()
        self.turn_router_service = turn_router_service or TurnRouterService()
        self.dialogue_brief_service = dialogue_brief_service or DialogueBriefService()
        self.level_persuasion_service = level_persuasion_service or LevelPersuasionService()

    def submit_turn(self, session_id: int, player_input: str) -> DebateTurnResponse:
        session = self.app_repository.get_session(session_id)
        routed_turn = self.turn_router_service.classify(player_input)
        meter_before = session.fortress_meter

        if not routed_turn.should_score:
            dialogue_brief = self.dialogue_brief_service.build(
                routed_turn,
                level_id=session.current_level,
                meter_after=meter_before,
            )
            persona = self.persona_service.respond_to_dialogue(
                dialogue_brief,
                player_input,
                meter_before,
            )
            persona_source = self.persona_service.last_source
            turn_index = self.app_repository.next_turn_index(session_id)
            self.app_repository.persist_turn(
                session_id=session_id,
                turn_index=turn_index,
                player_input=player_input,
                turn_type=routed_turn.turn_type,
                is_scored=False,
                retrieved_refs=[],
                evaluator=None,
                dialogue_brief=dialogue_brief,
                npc_response=persona.npc_response,
                meter_before=meter_before,
                meter_after=meter_before,
            )
            return DebateTurnResponse(
                session_id=session_id,
                turn_index=turn_index,
                player_input=player_input,
                turn_type=routed_turn.turn_type,
                is_scored=False,
                retrieved_refs=[],
                evaluator=None,
                dialogue_brief=dialogue_brief,
                npc_response=persona.npc_response,
                meter_before=meter_before,
                meter_after=meter_before,
                score_delta=0,
                evaluator_source=None,
                persona_source=persona_source,
            )

        context = self._conversation_context(session_id)
        retrieval_query = self.conversation_context_service.build_retrieval_query(player_input, context)
        evidence = self.retrieval_service.retrieve(retrieval_query)
        evaluator_context = self.conversation_context_service.context_for_evaluation(player_input, context)
        evaluator = self.evaluation_service.evaluate(player_input, evidence, evaluator_context)
        evaluator_source = self.evaluation_service.last_source
        evaluator = self.level_persuasion_service.apply(
            level_id=session.current_level,
            meter_before=meter_before,
            player_input=player_input,
            retrieved_refs=evidence,
            evaluator=evaluator,
            prior_turns=self.app_repository.fetch_turns(session_id),
        )
        meter_after = self.meter_service.apply_delta(meter_before, evaluator.score_delta)
        persona = self.persona_service.respond(evaluator, meter_after, player_input)
        persona_source = self.persona_service.last_source
        turn_index = self.app_repository.next_turn_index(session_id)
        self.app_repository.persist_turn(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            turn_type=routed_turn.turn_type,
            is_scored=True,
            retrieved_refs=evidence,
            evaluator=evaluator,
            npc_response=persona.npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
        )
        return DebateTurnResponse(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            turn_type=routed_turn.turn_type,
            is_scored=True,
            retrieved_refs=evidence,
            evaluator=evaluator,
            dialogue_brief=None,
            npc_response=persona.npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
            score_delta=evaluator.score_delta,
            evaluator_source=evaluator_source,
            persona_source=persona_source,
        )

    def stream_turn_events(self, session_id: int, player_input: str) -> Iterator[dict[str, Any]]:
        session = self.app_repository.get_session(session_id)
        routed_turn = self.turn_router_service.classify(player_input)
        meter_before = session.fortress_meter

        if not routed_turn.should_score:
            dialogue_brief = self.dialogue_brief_service.build(
                routed_turn,
                level_id=session.current_level,
                meter_after=meter_before,
            )
            yield {"event": "phase", "phase": "persona"}
            npc_chunks: list[str] = []
            for chunk in self.persona_service.stream_dialogue_brief(
                dialogue_brief,
                player_input,
                meter_before,
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
                turn_type=routed_turn.turn_type,
                is_scored=False,
                retrieved_refs=[],
                evaluator=None,
                dialogue_brief=dialogue_brief,
                npc_response=npc_response,
                meter_before=meter_before,
                meter_after=meter_before,
            )
            response = DebateTurnResponse(
                session_id=session_id,
                turn_index=turn_index,
                player_input=player_input,
                turn_type=routed_turn.turn_type,
                is_scored=False,
                retrieved_refs=[],
                evaluator=None,
                dialogue_brief=dialogue_brief,
                npc_response=npc_response,
                meter_before=meter_before,
                meter_after=meter_before,
                score_delta=0,
                evaluator_source=None,
                persona_source=persona_source,
            )
            yield {"event": "complete", "turn": response.model_dump(mode="json")}
            return

        yield {"event": "phase", "phase": "retrieving"}
        context = self._conversation_context(session_id)
        retrieval_query = self.conversation_context_service.build_retrieval_query(player_input, context)
        evidence = self.retrieval_service.retrieve(retrieval_query)

        yield {"event": "phase", "phase": "evaluating"}
        evaluator_context = self.conversation_context_service.context_for_evaluation(player_input, context)
        evaluator = self.evaluation_service.evaluate(player_input, evidence, evaluator_context)
        evaluator_source = self.evaluation_service.last_source
        evaluator = self.level_persuasion_service.apply(
            level_id=session.current_level,
            meter_before=meter_before,
            player_input=player_input,
            retrieved_refs=evidence,
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
        for chunk in self.persona_service.stream_dialogue(evaluator, meter_after, player_input):
            npc_chunks.append(chunk)
            yield {"event": "persona_delta", "text": chunk}

        npc_response = "".join(npc_chunks).strip()
        persona_source = self.persona_service.last_source
        turn_index = self.app_repository.next_turn_index(session_id)
        self.app_repository.persist_turn(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            turn_type=routed_turn.turn_type,
            is_scored=True,
            retrieved_refs=evidence,
            evaluator=evaluator,
            dialogue_brief=None,
            npc_response=npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
        )
        response = DebateTurnResponse(
            session_id=session_id,
            turn_index=turn_index,
            player_input=player_input,
            turn_type=routed_turn.turn_type,
            is_scored=True,
            retrieved_refs=evidence,
            evaluator=evaluator,
            dialogue_brief=None,
            npc_response=npc_response,
            meter_before=meter_before,
            meter_after=meter_after,
            score_delta=evaluator.score_delta,
            evaluator_source=evaluator_source,
            persona_source=persona_source,
        )
        yield {"event": "complete", "turn": response.model_dump(mode="json")}

    def _conversation_context(self, session_id: int):
        recent_turns = self.app_repository.fetch_recent_turns(
            session_id,
            self.conversation_context_service.max_turns,
        )
        return self.conversation_context_service.build_context(recent_turns)
