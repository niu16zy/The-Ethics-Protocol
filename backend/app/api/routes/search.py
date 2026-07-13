from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.api.dependencies import retrieval_service
from backend.app.schemas.evaluator import EvidenceRef

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[EvidenceRef])
def search(q: str = Query(min_length=1), top_k: int = Query(default=5, ge=1, le=10)) -> list[EvidenceRef]:
    return retrieval_service().retrieve(q, top_k=top_k)
