#backend\services\llm_client.py
import os
from typing import Protocol, Optional
import logging
import httpx
import json
from dotenv import load_dotenv

load_dotenv(override=True)


logger = logging.getLogger(__name__)

class LLMClient(Protocol):
    async def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer based on the question and context"""
        ...

    async def rerank_results(self, query: str, results: list) -> list:
        """Rerank search results for relevance"""
        ...

    async def generate_session_name(self, message: str) -> str:
        """Generate a name for a chat session"""
        ...

class GeminiClient:
    """Client for Google Gemini API"""

    def __init__(self):
        # Try multiple sources for API key, prioritizing user-provided storage
        self.api_key =(
                self._load_api_key_from_storage() or
                os.getenv('GEMINI_API_KEY') or
                os.getenv('GOOGLE_API_KEY')
        )
        self.base_url = "https://generativelanguage.googleapis.com/v1"

        if self.api_key:
            logger.info("Gemini API key loaded successfully")
        else:
            logger.warning("Gemini API key not found. Please set GEMINI_API_KEY environment variable or configure in settings.")

    def _load_api_key_from_storage(self) -> Optional[str]:
        """Load API key from local storage file"""
        try:
            config_file = os.path.expanduser("~/.smartfile_ai_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('gemini_api_key')
        except Exception as e:
            logger.debug(f"Could not load config file: {str(e)}")
        return None

    async def generate_answer(self, question: str, context: str) -> str:
        if not self.api_key:
            return """Gemini API key not configured. Please:

1. Get your API key from https://ai.google.dev/
2. Set the GEMINI_API_KEY environment variable, or
3. Configure it in the Settings page

Without an API key, I can only search your files but cannot generate AI-powered answers."""

        try:
            prompt = f"""Based on the following context from the user's files, please answer the question accurately and helpfully.

Context from files:
{context}

Question: {question}

Please provide a clear, helpful answer based on the information in the context. If the context doesn't contain enough information to fully answer the question, please say so and provide what information you can based on what's available."""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-2.5-flash:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{
                            "parts": [{"text": prompt}]
                        }],
                        "generationConfig": {
                            "temperature": 0.7,
                            "topK": 40,
                            "topP": 0.95,
                            "maxOutputTokens": 1024,
                        }
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if "candidates" in result and len(result["candidates"]) > 0:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        return "I received an empty response from the AI service. Please try rephrasing your question."
                else:
                    error_msg = f"Gemini API error: {response.status_code}"
                    if response.status_code == 400:
                        error_msg += " - Invalid API key or request format"
                    elif response.status_code == 403:
                        error_msg += " - API key may be invalid or quota exceeded"
                    elif response.status_code == 429:
                        error_msg += " - Rate limit exceeded, please try again later"

                    logger.error(f"{error_msg} - {response.text}")
                    return f"Error calling Gemini API: {error_msg}"

        except httpx.TimeoutException:
            logger.error("Gemini API request timed out")
            return "The AI service request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error generating answer with Gemini: {str(e)}")
            return f"Error generating answer: {str(e)}"

    async def rerank_results(self, query: str, results: list) -> list:
        """Rerank search results using a more capable model."""
        if not self.api_key:
            # If no API key, return original results with a default score
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.5)
            return results

        try:
            # Prepare documents for reranking
            documents = [
                {
                    "id": str(i),
                    "content": f"File: {res['file_name']}\nContent: {res['content']}"
                } for i, res in enumerate(results)
            ]
            
            prompt = f"""Given the user's query and the following documents, please evaluate the relevance of each document to the query. Return a JSON object with document IDs as keys and their relevance scores (0.0 to 1.0) as values.

Query: "{query}"

Documents:
{json.dumps(documents, indent=2)}

Respond with ONLY the JSON object. For example:
{{
  "0": 0.9,
  "1": 0.2,
  "2": 0.7
}}
"""
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-1.5-flash:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.0}
                    }
                )
            
            if response.status_code == 200:
                raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                
                # Helper to find and parse JSON from a string
                def extract_json(text: str) -> Optional[dict]:
                    start_index = text.find('{')
                    end_index = text.rfind('}')
                    if start_index != -1 and end_index != -1:
                        json_str = text[start_index:end_index+1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            return None
                    return None

                rerank_data = extract_json(raw_text)

                if rerank_data:
                    for i, result in enumerate(results):
                        result['relevance_score'] = rerank_data.get(str(i), 0.0)
                    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
                else:
                    logger.warning("Could not parse JSON from reranker, returning original order.")
                    for result in results:
                        result['relevance_score'] = result.get('similarity_score', 0.0)
                    return results
            else:
                logger.error(f"Reranking failed with status {response.status_code}: {response.text}")
                # Fallback: use original similarity scores
                for result in results:
                    result['relevance_score'] = result.get('similarity_score', 0.0)
                return results

        except Exception as e:
            logger.error(f"Error during reranking: {e}", exc_info=True)
            # Fallback: use original similarity scores
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

    async def generate_session_name(self, message: str) -> str:
        """Generate a concise, relevant name for a chat session."""
        if not self.api_key:
            return "New Chat"

        try:
            prompt = f'Generate a very short, snappy title (3-5 words) for a chat that starts with this message: "{message}". Just return the title, nothing else.'
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-1.5-flash:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 20}
                    }
                )
            
            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip().strip('"')
            else:
                return "Chat"

        except Exception as e:
            logger.error(f"Error generating session name: {e}")
            return "Chat"

class OllamaClient:
    """Client for Ollama local LLM"""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = "tinyllama:latest"
        self.initialized = False
        
        try:
            logger.info(f"Initializing Ollama client with model: {self.model}")
            self.initialized = True
            logger.info("Ollama client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}", exc_info=True)

    async def generate_answer(self, question: str, context: str) -> str:
        if not self.initialized:
            return "Ollama service is not available. Please ensure Ollama is running."

        # Truncate context to fit within reasonable limits
        max_context_length = 1500  # Leave room for prompt and answer
        if len(context) > max_context_length:
            context = context[:max_context_length] + "..."

        prompt = f"""Based on the following context from the user's files, please answer the question accurately and helpfully.

Context from files:
{context}

Question: {question}

Answer:"""

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return f"Error calling Ollama API: {response.status_code}"

        except httpx.TimeoutException:
            logger.error("Ollama API request timed out")
            return "The local LLM service request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error generating answer with Ollama: {str(e)}")
            return f"Error generating answer: {str(e)}"

    async def generate_json(self, prompt: str) -> dict:
        """Generate a JSON-only response from Ollama using JSON mode."""
        if not self.initialized:
            return {}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.1
                        }
                    }
                )

            if response.status_code == 200:
                raw_text = response.json().get("response", "")
                try:
                    return json.loads(raw_text)
                except json.JSONDecodeError:
                    return {}
            else:
                logger.error(f"Ollama JSON API error: {response.status_code} - {response.text}")
                return {}

        except httpx.TimeoutException:
            logger.error("Ollama JSON API request timed out")
            return {}
        except Exception as e:
            logger.error(f"Error generating JSON with Ollama: {str(e)}")
            return {}

    async def rerank_results(self, query: str, results: list) -> list:
        """Rerank search results using Ollama."""
        try:
            # Prepare documents for reranking
            documents = [
                {
                    "id": str(i),
                    "content": f"File: {res['file_name']}\nContent: {res['content'][:200]}"
                } for i, res in enumerate(results)
            ]
            
            prompt = f"""Given the user's query and the following documents, please evaluate the relevance of each document to the query. Return a JSON object with document IDs as keys and their relevance scores (0.0 to 1.0) as values.

Query: "{query}"

Documents:
{json.dumps(documents, indent=2)}

Respond with ONLY the JSON object. For example:
{{
  "0": 0.9,
  "1": 0.2,
  "2": 0.7
}}"""

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
            
            if response.status_code == 200:
                raw_text = response.json().get("response", "")
                
                # Helper to find and parse JSON from a string
                def extract_json(text: str) -> Optional[dict]:
                    start_index = text.find('{')
                    end_index = text.rfind('}')
                    if start_index != -1 and end_index != -1:
                        json_str = text[start_index:end_index+1]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            return None
                    return None

                rerank_data = extract_json(raw_text)

                if rerank_data:
                    for i, result in enumerate(results):
                        result['relevance_score'] = rerank_data.get(str(i), 0.0)
                    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
                else:
                    logger.warning("Could not parse JSON from reranker, returning original order.")
                    for result in results:
                        result['relevance_score'] = result.get('similarity_score', 0.0)
                    return results
            else:
                logger.error(f"Reranking failed with status {response.status_code}: {response.text}")
                # Fallback: use original similarity scores
                for result in results:
                    result['relevance_score'] = result.get('similarity_score', 0.0)
                return results

        except Exception as e:
            logger.error(f"Error during reranking: {e}", exc_info=True)
            # Fallback: use original similarity scores
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

    async def generate_session_name(self, message: str) -> str:
        """Generate a concise, relevant name for a chat session."""
        prompt = f'Generate a very short, snappy title (3-5 words) for a chat that starts with this message: "{message}". Just return the title, nothing else. Title:'
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
            
            if response.status_code == 200:
                title = response.json().get("response", "New Chat").strip().strip('"')
                return title if title else "New Chat"
            else:
                return "Chat"

        except Exception as e:
            logger.error(f"Error generating session name with Ollama: {e}")
            return "Chat"


class FallbackClient:
    """
    Fallback client used when primary LLM clients fail to initialize.
    Returns a helpful error message with configuration instructions.
    """
    async def generate_answer(self, question: str, context: str) -> str:
        return (
            "⚠️ AI Service Unavailable\n\n"
            "Please check your configuration:\n\n"
            "1. Get a Gemini API key from https://ai.google.dev/\n"
            "2. Set it as GEMINI_API_KEY in your .env file\n"
            "3. Or configure it in the Settings page\n\n"
            "Without an API key, I can search your files but can't generate AI answers.\n\n"
            f"Context from your files:\n{context[:500]}{'...' if len(context) > 500 else ''}"
        )

    async def rerank_results(self, query: str, results: list) -> list:
        """
        Fallback rerank just returns original results, as no AI is available.
        """
        for result in results:
            result['relevance_score'] = result.get('similarity_score', 0.0)
        return results

    async def generate_session_name(self, message: str) -> str:
        """
        Fallback session name generator.
        """
        return "New Chat"

class LLMClientFactory:
    """Factory for creating LLM clients"""
    _clients = {}

    @staticmethod
    def create_client(client_type: str = "ollama") -> LLMClient:
        """Create an LLM client of the specified type with fallback support"""
        client_type = client_type.lower() if client_type else "ollama"

        if client_type in LLMClientFactory._clients:
            return LLMClientFactory._clients[client_type]

        logger.info(f"Creating LLM client of type: {client_type}")

        if client_type == "gemini":
            try:
                client = GeminiClient()
                if not client.api_key:
                    raise ValueError("Gemini API key not found.")
                LLMClientFactory._clients[client_type] = client
                return client
            except Exception as e:
                logger.error(f"Failed to create Gemini client: {e}")
                return FallbackClient()

        elif client_type == "ollama":
            try:
                client = OllamaClient()
                if not client.initialized:
                    raise ValueError("Ollama service not initialized.")
                LLMClientFactory._clients[client_type] = client
                return client
            except Exception as e:
                logger.error(f"Failed to create Ollama client: {e}")
                return FallbackClient()
        
        elif client_type == "local":
            logger.warning("Client type 'local' is ambiguous, defaulting to 'ollama'.")
            return LLMClientFactory.create_client("ollama")
        
        elif client_type == "phi":
            logger.warning("Client type 'phi' is deprecated, using 'ollama' instead.")
            return LLMClientFactory.create_client("ollama")

        else:
            logger.error(f"Unknown LLM client type: {client_type}")
            return FallbackClient()
