from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from backend.app.core.db import connect_sqlite
from backend.app.schemas.evaluator import EvidenceRef


STOPWORDS = {
    "about",
    "against",
    "also",
    "because",
    "being",
    "can",
    "could",
    "does",
    "from",
    "have",
    "into",
    "matter",
    "matters",
    "more",
    "must",
    "need",
    "needs",
    "should",
    "that",
    "their",
    "then",
    "there",
    "this",
    "through",
    "with",
    "would",
}


class KnowledgeRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def verify_schema(self) -> None:
        with connect_sqlite(self.db_path) as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        missing = {"documents", "documents_fts"} - tables
        if missing:
            raise RuntimeError(f"Knowledge DB missing required tables: {sorted(missing)}")

    def search(self, query: str, top_k: int) -> list[EvidenceRef]:
        clean_query = query.strip()
        if not clean_query:
            return []

        match_query = self._build_fts_query(clean_query)
        sql = """
            SELECT
                d.id AS document_id,
                d.course,
                d.lesson,
                d.topic,
                d.content,
                d.seq_order,
                bm25(documents_fts) AS rank_score
            FROM documents_fts
            JOIN documents d ON d.id = documents_fts.id
            WHERE documents_fts MATCH ?
            ORDER BY rank_score
            LIMIT ?
        """
        try:
            with connect_sqlite(self.db_path) as connection:
                rows = connection.execute(sql, (match_query, top_k)).fetchall()
        except sqlite3.OperationalError:
            return self._fallback_like_search(clean_query, top_k)

        return [self._row_to_evidence(row) for row in rows]

    def _fallback_like_search(self, query: str, top_k: int) -> list[EvidenceRef]:
        terms = self._extract_search_terms(query)
        if not terms:
            terms = [query]
        where = " OR ".join(["lower(content) LIKE lower(?) OR lower(topic) LIKE lower(?)"] * len(terms))
        params: list[str | int] = []
        for term in terms:
            pattern = f"%{term}%"
            params.extend([pattern, pattern])
        params.append(top_k)
        sql = f"""
            SELECT id AS document_id, course, lesson, topic, content, seq_order, NULL AS rank_score
            FROM documents
            WHERE {where}
            ORDER BY seq_order
            LIMIT ?
        """
        with connect_sqlite(self.db_path) as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_evidence(row) for row in rows]

    def _build_fts_query(self, query: str) -> str:
        tokens = self._extract_search_terms(query)
        if not tokens:
            return f'"{query.replace(chr(34), "")}"'
        return " OR ".join(tokens)

    def _extract_search_terms(self, query: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z][A-Za-z0-9_]+", query.lower())
        unique_tokens: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            if len(token) <= 2 or token in STOPWORDS or token in seen:
                continue
            seen.add(token)
            unique_tokens.append(token)
        return unique_tokens

    def _row_to_evidence(self, row: sqlite3.Row) -> EvidenceRef:
        content = row["content"] or ""
        excerpt = content if len(content) <= 220 else f"{content[:217]}..."
        score = row["rank_score"]
        return EvidenceRef(
            document_id=row["document_id"],
            course=row["course"],
            lesson=row["lesson"],
            topic=row["topic"],
            seq_order=row["seq_order"],
            excerpt=excerpt,
            score=float(score) if score is not None else None,
        )
