
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
from backend.core.config import settings

logger = logging.getLogger(__name__)

class VectorMemory:
    def __init__(self):
        self.encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        if settings.USE_LOCAL_QDRANT:
            # Persistent local storage
            self.client = QdrantClient(path=settings.QDRANT_PATH)
        else:
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            
        self.collections = [
            settings.COLLECTION_TEXT,
            settings.COLLECTION_IMAGE,
            settings.COLLECTION_INTERACTION,
            settings.COLLECTION_GUIDELINES
        ]
        
        self._initialize_collections()

    def _initialize_collections(self):
        """Ensure all required collections exist with correct configuration"""
        existing = [c.name for c in self.client.get_collections().collections]
        
        for name in self.collections:
            if name not in existing:
                logger.info(f"Creating collection: {name}")
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=models.VectorParams(
                        size=settings.EMBEDDING_DIM,
                        distance=models.Distance.COSINE
                    )
                )

    def generate_embedding(self, text: str) -> List[float]:
        return self.encoder.encode(text).tolist()

    async def upsert_memory(self, 
                      collection: str, 
                      content: str, 
                      metadata: Dict[str, Any], 
                      embedding: Optional[List[float]] = None):
        """Store a memory item in Qdrant"""
        if embedding is None:
            embedding = self.generate_embedding(content)
            
        point_id = str(uuid.uuid4())
        
        # Enrich metadata
        payload = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        self.client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        logger.info(f"Upserted memory to {collection}: {point_id}")
        return point_id

    async def search_memory(self, 
                      collection: str, 
                      query_text: str, 
                      limit: int = 5, 
                      score_threshold: float = 0.5,
                      filter_conditions: Optional[Dict] = None) -> List[Dict]:
        """Search for memories"""
        query_vector = self.generate_embedding(query_text)
        
        query_filter = None
        if filter_conditions:
            # Simple exact match filter construction (can be expanded)
            must_conditions = []
            for key, value in filter_conditions.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            query_filter = models.Filter(must=must_conditions)

        search_result = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": hit.payload,
                "content": hit.payload.get("content", "")
            }
            for hit in search_result
        ]

    async def search_all_collections(self, query_text: str, limit: int = 5) -> Dict[str, List[Dict]]:
        """Search across all memory collections"""
        results = {}
        for collection in self.collections:
            results[collection] = await self.search_memory(collection, query_text, limit)
        return results

    async def delete_file_memories(self, file_path: str):
        """Delete all memories associated with a specific file path"""
        for collection in self.collections:
            self.client.delete(
                collection_name=collection,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_path",
                                match=models.MatchValue(value=file_path)
                            )
                        ]
                    )
                )
            )
        logger.info(f"Deleted memories for file: {file_path}")
