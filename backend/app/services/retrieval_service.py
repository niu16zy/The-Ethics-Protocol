from __future__ import annotations

from dataclasses import dataclass

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.schemas.evaluator import EvidenceRef


@dataclass(frozen=True)
class RetrievalQuery:
    query_text: str
    original_input: str
    context_terms: list[str]
    used_context: bool = False


class RetrievalService:
    def __init__(self, repository: KnowledgeRepository, default_top_k: int = 3) -> None:
        self.repository = repository
        self.default_top_k = default_top_k

    def retrieve(self, query: str | RetrievalQuery, top_k: int | None = None) -> list[EvidenceRef]:
        self.repository.verify_schema()
        query_text = query.query_text if isinstance(query, RetrievalQuery) else query
        return self.repository.search(query_text, top_k or self.default_top_k)
