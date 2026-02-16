
from typing import Dict, Any, Optional
from backend.agents.base import BaseAgent

class SafetyAgent(BaseAgent):
    def __init__(self):
        super().__init__("SafetyAgent")
        self.unsafe_keywords = [
            "diagnose", "prescription", "prescribe", "treatment plan", 
            "suicide", "kill", "bomb", "poison"
        ]
        self.disallowed_phrases = [
            "you have cancer", "take this medicine", "stop taking current medication"
        ]

    async def process(self, input_data: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Pre-check the user query for safety violations.
        """
        query = input_data.lower()
        
        # 1. Simple Keyword Check
        for word in self.unsafe_keywords:
            if word in query:
                # Contextual check: "diagnose" is bad if asking AI to do it, 
                # but "diagnosis" might be okay if asking about a report.
                # For this strict clinical decision support, we block requests for direct diagnosis.
                if "diagnose me" in query or "prescribe" in query:
                     return {
                        "is_safe": False, 
                        "reason": f"Safety Violation: Query contains unsafe term '{word}'. This system is for decision support only, not diagnosis."
                    }

        return {"is_safe": True, "reason": "Query passed pre-check."}

    async def post_check(self, generated_text: str) -> Dict[str, Any]:
        """
        Post-check the generated response.
        """
        text = generated_text.lower()
        
        for phrase in self.disallowed_phrases:
            if phrase in text:
                 return {
                    "is_safe": False, 
                    "reason": "Safety Violation: Response contains prohibited medical advice wording."
                }
        
        # Enforce "Consult clinician" framing
        if "consult" not in text and "doctor" not in text and "professional" not in text:
             # We might append a warning instead of blocking
             return {
                 "is_safe": True,
                 "modified_text": generated_text + "\n\n**DISCLAIMER: This is AI-generated decision support. Always consult a clinical professional.**"
             }

        return {"is_safe": True, "modified_text": generated_text}
