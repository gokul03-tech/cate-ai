"""
LexOrch-KG — Agent 4: Retrieval Agent
Combines ChromaDB vector search with Neo4j graph traversal for context-rich RAG.
"""

import uuid
from typing import Any

from loguru import logger
from sentence_transformers import SentenceTransformer

from app.agents.base_agent import BaseAgent, AgentResult
from app.core.config import settings
from app.infrastructure.chromadb.client import chromadb_client
from app.infrastructure.neo4j.client import neo4j_client


class RetrievalAgent(BaseAgent):
    """
    Agent 4 — Retrieval (RAG Pipeline)
    
    Responsibilities:
    1. Encode document chunks into embeddings
    2. Store embeddings in ChromaDB
    3. Retrieve similar legal precedents via semantic search
    4. Augment with Neo4j graph traversal results
    5. Merge vector + graph retrieval results
    """

    def __init__(self) -> None:
        super().__init__("RetrievalAgent", step=4)
        # Load embedding model (cached after first download)
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self.embedder = SentenceTransformer(
            settings.embedding_model,
            cache_folder=".cache",
        )

    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        case_id = str(state["case_id"])
        chunks = state.get("chunks", [])
        summary = state.get("summary", "")
        entities = state.get("entities", [])

        # ── Step 1: Create embeddings for all chunks ────────────────────────
        if chunks:
            await self._store_embeddings(case_id, chunks)

        # ── Step 2: Build query from summary + key entities ─────────────────
        query_text = self._build_query(summary, entities)

        # ── Step 3: Vector search in ChromaDB ───────────────────────────────
        vector_results = await self._vector_search(query_text, case_id)

        # ── Step 4: Graph-based retrieval from Neo4j ─────────────────────────
        graph_results = await self._graph_retrieval(entities)

        # ── Step 5: Merge and rank results ───────────────────────────────────
        merged_precedents = self._merge_results(vector_results, graph_results)

        logger.info(
            f"[RetrievalAgent] Retrieved {len(merged_precedents)} precedents "
            f"(vector={len(vector_results)}, graph={len(graph_results)})"
        )

        state.update({
            "retrieved_precedents": merged_precedents,
            "embedding_count": len(chunks),
        })

        result = AgentResult(
            agent_name=self.name,
            status="completed",
            output={
                "embeddings_stored": len(chunks),
                "vector_results": len(vector_results),
                "graph_results": len(graph_results),
                "merged_precedents": len(merged_precedents),
            },
        )
        return state, result

    async def _store_embeddings(
        self, case_id: str, chunks: list[dict[str, Any]]
    ) -> None:
        """Encode chunks and upsert into ChromaDB."""
        texts = [c["text"] for c in chunks]
        # Batch encode for efficiency
        embeddings = self.embedder.encode(
            texts, batch_size=32, show_progress_bar=False
        ).tolist()

        metadatas = []
        for i, chunk in enumerate(chunks):
            metadatas.append({
                "case_id": case_id,
                "chunk_index": i,
                "page_number": chunk.get("metadata", {}).get("page", 0),
                "section": chunk.get("metadata", {}).get("section", ""),
            })

        ids = [chunk["id"] for chunk in chunks]

        await chromadb_client.add_documents(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"[RetrievalAgent] Stored {len(chunks)} embeddings in ChromaDB")

    def _build_query(
        self, summary: str, entities: list[dict[str, Any]]
    ) -> str:
        """Build a rich query string for semantic search."""
        # Take summary + key entity types
        entity_values = [
            e.get("value", "") for e in entities
            if e.get("type") in ("ACT", "SECTION", "CASE_NUMBER")
        ]
        query_parts = [summary[:500]]
        if entity_values:
            query_parts.append(" ".join(entity_values[:10]))
        return " ".join(query_parts)

    async def _vector_search(
        self, query: str, exclude_case_id: str
    ) -> list[dict[str, Any]]:
        """Semantic search in ChromaDB, excluding current case chunks."""
        if not query:
            return []

        query_embedding = self.embedder.encode([query]).tolist()

        try:
            results = await chromadb_client.query(
                query_embeddings=query_embedding,
                n_results=10,
                where={"case_id": {"$ne": exclude_case_id}},  # Exclude self
            )

            precedents = []
            documents = results.get("documents", [[]])[0]
            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            for doc, dist, meta in zip(documents, distances, metadatas):
                precedents.append({
                    "text": doc,
                    "similarity_score": 1 - dist,  # Convert distance to similarity
                    "source": "chromadb",
                    "metadata": meta,
                    "title": f"Precedent from case {meta.get('case_id', 'unknown')[:8]}",
                })

            return sorted(precedents, key=lambda x: x["similarity_score"], reverse=True)
        except Exception as e:
            logger.error(f"ChromaDB vector search failed: {e}")
            return []

    async def _graph_retrieval(
        self, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find related cases through Neo4j graph traversal."""
        try:
            # Find cases sharing the same Acts/Laws
            act_values = [
                e["value"] for e in entities
                if e.get("type") in ("ACT", "SECTION") and e.get("value")
            ]

            if not act_values:
                return []

            query = """
            MATCH (a:Act)-[:GOVERNED_BY]-(c:Case)
            WHERE a.name IN $act_names
            RETURN c.id as case_id, c.title as title, 
                   count(a) as shared_acts
            ORDER BY shared_acts DESC
            LIMIT 5
            """
            results = await neo4j_client.run_query(
                query, {"act_names": act_values[:10]}
            )

            return [
                {
                    "title": r.get("title", "Related Case"),
                    "text": f"Case {r.get('case_id', '')}: Shares {r.get('shared_acts', 0)} legal provisions",
                    "similarity_score": min(0.95, r.get("shared_acts", 1) * 0.2),
                    "source": "neo4j",
                    "metadata": {"case_id": r.get("case_id")},
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Neo4j graph retrieval failed: {e}")
            return []

    def _merge_results(
        self,
        vector_results: list[dict],
        graph_results: list[dict],
    ) -> list[dict[str, Any]]:
        """Merge and deduplicate results from both retrieval methods."""
        all_results = vector_results + graph_results
        # Sort by similarity score descending
        all_results.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        return all_results[:10]  # Return top 10
