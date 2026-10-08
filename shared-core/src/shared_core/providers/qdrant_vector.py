import httpx

from shared_core.interfaces.vector_store import VectorStoreService


class QdrantVectorStore(VectorStoreService):
    """Minimal Qdrant client used to confirm vector connectivity in Phase 1."""

    def __init__(
        self,
        base_url: str,
        collection_name: str = "documents",
        vector_size: int = 8,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.collection_name = collection_name
        self.vector_size = vector_size

    async def ensure_collection(self) -> None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/collections/{self.collection_name}"
            )
            if response.status_code == 200:
                return
            create = await client.put(
                f"{self.base_url}/collections/{self.collection_name}",
                json={
                    "vectors": {
                        "size": self.vector_size,
                        "distance": "Cosine",
                    }
                },
            )
            create.raise_for_status()

    async def upsert_embeddings(self, vectors: list[dict], tenant_id: str) -> bool:
        await self.ensure_collection()
        points = []
        for index, item in enumerate(vectors):
            payload = dict(item.get("payload") or {})
            payload["tenant_id"] = tenant_id
            points.append(
                {
                    "id": item.get("id", index + 1),
                    "vector": item["vector"],
                    "payload": payload,
                }
            )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/collections/{self.collection_name}/points",
                json={"points": points},
            )
            response.raise_for_status()
        return True

    async def similarity_search(
        self, query_vector: list[float], tenant_id: str, top_k: int = 5
    ) -> list[dict]:
        await self.ensure_collection()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/collections/{self.collection_name}/points/search",
                json={
                    "vector": query_vector,
                    "limit": top_k,
                    "with_payload": True,
                    "filter": {
                        "must": [
                            {
                                "key": "tenant_id",
                                "match": {"value": tenant_id},
                            }
                        ]
                    },
                },
            )
            response.raise_for_status()
            return response.json().get("result", [])

    async def healthcheck(self) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for path in ("/readyz", "/healthz"):
                try:
                    response = await client.get(f"{self.base_url}{path}")
                    if response.status_code == 200:
                        return True
                except httpx.HTTPError:
                    continue
        return False
