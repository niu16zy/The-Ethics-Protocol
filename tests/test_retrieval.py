from __future__ import annotations

from pathlib import Path

from backend.app.repositories.knowledge_repository import KnowledgeRepository
from backend.app.services.retrieval_service import RetrievalService


def test_retriever_returns_traceable_document_refs():
    db_path = Path(__file__).resolve().parents[1] / "course_content.db"
    service = RetrievalService(KnowledgeRepository(db_path), default_top_k=3)

    results = service.retrieve("fairness bias hiring")

    assert results
    assert all(result.document_id for result in results)
    assert all(result.excerpt for result in results)


def test_retriever_cleans_full_sentence_for_fts_search():
    db_path = Path(__file__).resolve().parents[1] / "course_content.db"
    service = RetrievalService(KnowledgeRepository(db_path), default_top_k=3)

    results = service.retrieve(
        "A hiring AI can be unfair if biased training data discriminates against applicants, "
        "so fairness and transparency matter."
    )

    assert results
    assert any(result.score is not None for result in results)
    assert all(result.excerpt for result in results)
