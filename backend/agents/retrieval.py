
from typing import Dict, Any, List, Optional
from backend.agents.base import BaseAgent
from backend.memory.vector_memory import VectorMemory
from backend.core.config import settings

class RetrievalAgent(BaseAgent):
    def __init__(self, vector_memory: VectorMemory):
        super().__init__("RetrievalAgent")
        self.memory = vector_memory

    async def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retrieve relevant information from vector memory.
        
        Args:
            input_data: {
                "query": str,
                "filters": Optional[Dict]   # e.g., {"patient_id": "123"}
            }
        """
        query = input_data.get("query")
        filters = input_data.get("filters")
        
        if not query:
            return {"results": []}

        # Retrieve from Clinical Text Memory
        text_results = await self.memory.search_memory(
            collection=settings.COLLECTION_TEXT,
            query_text=query,
            limit=5,
            score_threshold=0.4,
            filter_conditions=filters
        )
        
        # Retrieve from Interaction Memory (History)
        history_results = await self.memory.search_memory(
            collection=settings.COLLECTION_INTERACTION,
            query_text=query,
            limit=2,
            score_threshold=0.5,
             filter_conditions=filters
        )

        # Combine results
        evidence_bundle = {
            "text_evidence": text_results,
            "interaction_history": history_results,
            # Placeholder for image_evidence if we implemented multimodal search fully
            "image_evidence": [] 
        }
        
        self.log(f"Retrieved {len(text_results)} text chunks and {len(history_results)} history items.")
        return evidence_bundle
