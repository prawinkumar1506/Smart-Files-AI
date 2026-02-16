
import logging
from typing import Dict, Any, List
from backend.agents.base import BaseAgent
from backend.agents.ingestion import IngestionAgent
from backend.agents.retrieval import RetrievalAgent
from backend.agents.verification import VerificationAgent
from backend.agents.reasoning import ReasoningAgent
from backend.agents.safety import SafetyAgent
from backend.memory.vector_memory import VectorMemory

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("OrchestratorAgent")
        
        # Initialize Memory
        self.memory = VectorMemory()
        
        # Initialize Agents
        self.ingestion_agent = IngestionAgent(self.memory)
        self.retrieval_agent = RetrievalAgent(self.memory)
        self.verification_agent = VerificationAgent()
        self.reasoning_agent = ReasoningAgent()
        self.safety_agent = SafetyAgent()
        
        self.log("Orchestrator initialized with all sub-agents.")

    async def process(self, input_data: Any, context: Dict = None) -> Any:
        # Default entry point, can rout based on input type
        pass

    async def run_ingestion_flow(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Execute the Ingestion Workflow
        """
        self.log(f"Starting ingestion flow for {len(file_paths)} files.")
        
        result = await self.ingestion_agent.process({"file_paths": file_paths})
        
        return {
            "status": "completed",
            "details": result
        }

    async def run_query_flow(self, query: str, context_filters: Dict = None) -> Dict[str, Any]:
        """
        Execute the Query Workflow (RAG)
        """
        self.log(f"Starting query flow: {query}")
        
        # 1. Safety Pre-check
        safety_check = await self.safety_agent.process(query)
        if not safety_check["is_safe"]:
            self.log(f"Query blocked by Safety Agent: {safety_check['reason']}", level="warning")
            return {
                "success": False,
                "answer": "Sorry, I cannot process this request.",
                "reason": safety_check["reason"]
            }

        # 2. Retrieval
        retrieval_input = {
            "query": query,
            "filters": context_filters
        }
        retrieval_result = await self.retrieval_agent.process(retrieval_input)
        
        # 3. Verification
        verification_result = await self.verification_agent.process(retrieval_result)
        
        if verification_result["needs_re_retrieval"]:
            self.log("Verification indicates low quality evidence. Proceeding with best available.", level="warning")
            # In a more advanced system, we would trigger a second retrieval loop here
            # For now, we proceed with what we have (verification agent returns best available)

        # 4. Reasoning
        reasoning_input = {
            "query": query,
            "evidence": verification_result["verified_evidence"]
        }
        reasoning_result = await self.reasoning_agent.process(reasoning_input)
        
        # 5. Safety Post-check
        post_check = await self.safety_agent.post_check(reasoning_result["answer"])
        
        final_answer = post_check["modified_text"]
        if not post_check["is_safe"]:
            self.log("Response modified by Safety Agent.", level="warning")

        # 6. Store Interaction (Conceptually - would call an InteractionAgent to upsert this Q&A)
        # TODO: Implement Interaction Logging to Qdrant

        return {
            "success": True,
            "answer": final_answer,
            "sources": reasoning_result["sources"]
        }
