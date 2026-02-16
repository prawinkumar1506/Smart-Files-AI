
from typing import Dict, Any, Optional
from backend.agents.base import BaseAgent
from backend.services.llm_client import LLMClientFactory

class ReasoningAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReasoningAgent")
        self.llm_client = LLMClientFactory.create_client()

    async def process(self, input_data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate answer using LLM based on verified evidence.
        
        Args:
            input_data: {
                "evidence": List[Dict],
                "query": str
            }
        """
        evidence = input_data.get("evidence", [])
        query = input_data.get("query", "")
        
        if not evidence:
            return {
                "answer": "I could not find sufficient information in the provided files to answer your question.",
                "sources": []
            }
        
        # Build Context
        context_str = ""
        sources = []
        for i, item in enumerate(evidence):
            source_citation = f"Source {i+1} (Score: {item['score']:.2f})"
            payload = item.get("payload", {})
            file_path = payload.get("file_path", "Unknown File")
            
            context_str += f"\n[{source_citation}] ({file_path}):\n{item['content']}\n"
            
            sources.append({
                "file_path": file_path,
                "content_preview": item['content'][:200] + "...",
                "score": item['score']
            })

        # Construct Prompt
        prompt = f"""
You are a Clinical Decision Support AI Assistant. 
Your goal is to provide accurate, grounded answers based STRICTLY on the provided context.

RULES:
1. Use ONLY the Context provided below. Do not hallucinate or use outside knowledge.
2. Cite your sources using [Source X] format.
3. If the answer is not in the context, state that you do not know.
4. Be professional, concise, and clear.
5. Provide a Summary followed by Recommendations if applicable.

CONTEXT:
{context_str}

USER QUERY: 
{query}

ANSWER:
"""
        
        # Call LLM
        # Note: The LLMClient interface might need adjustment if it wraps the prompt differently.
        # Looking at llm_client.py, it takes question and context, and builds its own prompt.
        # We should use its generate_answer but maybe we want more control.
        # existing llm_client.py: generate_answer(self, question: str, context: str)
        # It builds a prompt: "Context from files:\n{context}\n\nQuestion: {question}..."
        
        # So passing 'context_str' as context is fine.
        
        response_text = await self.llm_client.generate_answer(query, context_str)
        
        return {
            "answer": response_text,
            "sources": sources
        }
