#backend\services\llm_client.py
import os
from typing import Protocol, Optional
import logging
import httpx
import json
from dotenv import load_dotenv
load_dotenv()


logger = logging.getLogger(__name__)

class LLMClient(Protocol):
    async def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer based on the question and context"""
        ...

class GeminiClient:
    """Client for Google Gemini API"""

    def __init__(self, api_key: Optional[str] = None):
        # Try multiple sources for API key
        self.api_key =(
                api_key or
                os.getenv('GEMINI_API_KEY') or
                os.getenv('GOOGLE_API_KEY') or 
                self._load_api_key_from_storage()
        )
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

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
                    f"{self.base_url}/models/gemini-1.5-flash:generateContent",
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

class LocalLLMClient:
    """Client for local LLM (placeholder implementation)"""

    def __init__(self):
        logger.info("Local LLM client initialized (placeholder)")

    async def generate_answer(self, question: str, context: str) -> str:
        # This is a placeholder - in a real implementation, you would
        # load a local model like Mistral or LLaMA using transformers or llama.cpp
        return f"""Based on the provided context, I would answer your question: "{question}"

However, this is a placeholder response as the local LLM is not yet implemented. 
To use local LLM capabilities, you would need to:

1. Install transformers library
2. Download a model like Mistral-7B
3. Implement the inference logic

For now, please configure the Gemini API key in settings to get AI-powered answers.

Context found in your files:
{context[:500]}{"..." if len(context) > 500 else ""}"""


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

class LLMClientFactory:
    """Factory for creating LLM clients"""

    @staticmethod
    def create_client(client_type: str = "gemini") -> LLMClient:
        """Create an LLM client of the specified type with fallback support"""
        client_type = client_type.lower()

        # Handle Gemini client creation with proper error checking
        if client_type == "gemini":
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("Gemini API key missing. Set GEMINI_API_KEY environment variable.")

                # Validate key format (basic check)
                if len(api_key) < 30 or not api_key.startswith("AI"):
                    raise ValueError("Invalid Gemini API key format")

                return GeminiClient(api_key)
            except Exception as e:
                logger.error(f"Gemini client initialization failed: {str(e)}")
                logger.warning("Falling back to default client")
                return FallbackClient()  # Ensure this is implemented

        # Handle local client option
        elif client_type == "local":
            try:
                return LocalLLMClient()  # Ensure this class exists
            except Exception as e:
                logger.error(f"Local client initialization failed: {str(e)}")
                return FallbackClient()

        # Handle unknown client types
        else:
            logger.warning(f"Unknown client type: '{client_type}'. Defaulting to Gemini.")
            try:
                # Attempt to create Gemini as fallback
                api_key = os.getenv("GEMINI_API_KEY")
                return GeminiClient(api_key) if api_key else FallbackClient()
            except Exception:
                return FallbackClient()
