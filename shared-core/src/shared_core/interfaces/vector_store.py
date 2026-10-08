from abc import ABC, abstractmethod


class VectorStoreService(ABC):
    """Vector store abstraction. Implementations MUST enforce tenant filters."""

    @abstractmethod
    async def upsert_embeddings(self, vectors: list[dict], tenant_id: str) -> bool:
        """Force payload['tenant_id'] = tenant_id before write."""

    @abstractmethod
    async def similarity_search(
        self, query_vector: list[float], tenant_id: str, top_k: int = 5
    ) -> list[dict]:
        """Always apply tenant metadata filter."""
