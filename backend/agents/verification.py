
from typing import Dict, Any, List, Optional
from backend.agents.base import BaseAgent

class VerificationAgent(BaseAgent):
    def __init__(self):
        super().__init__("VerificationAgent")

    async def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Verify and filter retrieved evidence.
        
        Args:
            input_data: The evidence bundle from RetrievalAgent
        """
        text_evidence = input_data.get("text_evidence", [])
        
        verified_evidence = []
        seen_content = set()
        
        # 1. Deduplication
        for item in text_evidence:
            content = item.get("content", "").strip()
            if content not in seen_content:
                seen_content.add(content)
                verified_evidence.append(item)
        
        # 2. Quality Check (Simple Score Thresholding - already done in retrieval, but we can be stricter here)
        high_quality_evidence = [
            item for item in verified_evidence 
            if item.get("score", 0) > 0.45 
        ]
        
        # If we filtered too much, fallback to the original verified list to ensure we have *something*
        final_evidence = high_quality_evidence if high_quality_evidence else verified_evidence
        
        needs_re_retrieval = len(final_evidence) == 0
        
        self.log(f"Verified evidence: {len(text_evidence)} -> {len(final_evidence)} items.")
        
        return {
            "verified_evidence": final_evidence,
            "needs_re_retrieval": needs_re_retrieval
        }
