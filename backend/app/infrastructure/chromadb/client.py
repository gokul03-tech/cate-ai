"""
LexOrch-KG — ChromaDB Vector Store Client
Manages embeddings storage and semantic search for RAG pipeline.
"""

from typing import Any
from loguru import logger
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings


class ChromaDBClient:
    """
    ChromaDB client wrapper for the legal document vector store.
    
    Handles:
    - Collection management
    - Document embedding storage
    - Semantic similarity search
    - Metadata filtering
    """

    def __init__(self) -> None:
        self._client: chromadb.AsyncHttpClient | None = None
        self._collection = None

    async def connect(self) -> None:
        """Initialize connection to ChromaDB server."""
        self._client = await chromadb.AsyncHttpClient(
            host=settings.chromadb_host,
            port=settings.chromadb_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # Get or create the legal documents collection
        self._collection = await self._client.get_or_create_collection(
            name=settings.chromadb_collection_name,
            metadata={"hnsw:space": "cosine"},  # Cosine similarity
        )
        logger.info(
            f"ChromaDB connected → {settings.chromadb_host}:{settings.chromadb_port} "
            f"| Collection: {settings.chromadb_collection_name}"
        )

    async def add_documents(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """
        Add documents with embeddings to the collection.
        
        Args:
            documents: List of text chunks
            embeddings: Corresponding embedding vectors
            metadatas: Metadata for each chunk (case_id, page, section, etc.)
            ids: Unique IDs for each chunk
        """
        if not self._collection:
            await self.connect()

        await self._collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added {len(documents)} documents to ChromaDB")

    async def query(
        self,
        query_embeddings: list[list[float]],
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Semantic search in the vector store.
        
        Args:
            query_embeddings: Query vector(s)
            n_results: Number of results to return
            where: Metadata filter (e.g., {"case_id": "abc"})
            include: Fields to include in results
        
        Returns:
            ChromaDB query results with documents, distances, and metadata
        """
        if not self._collection:
            await self.connect()

        results = await self._collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
            include=include or ["documents", "distances", "metadatas"],
        )
        return results

    async def delete_by_case(self, case_id: str) -> None:
        """Remove all chunks belonging to a specific case."""
        if not self._collection:
            await self.connect()
        await self._collection.delete(where={"case_id": case_id})
        logger.info(f"Deleted ChromaDB documents for case {case_id}")

    async def get_collection_stats(self) -> dict[str, Any]:
        """Return stats about the current collection."""
        if not self._collection:
            await self.connect()
        count = await self._collection.count()
        return {
            "name": settings.chromadb_collection_name,
            "document_count": count,
        }

    async def heartbeat(self) -> bool:
        """Check ChromaDB connectivity."""
        try:
            if not self._client:
                await self.connect()
            await self._client.heartbeat()
            return True
        except Exception as e:
            logger.error(f"ChromaDB heartbeat failed: {e}")
            return False


# Global singleton client
chromadb_client = ChromaDBClient()
