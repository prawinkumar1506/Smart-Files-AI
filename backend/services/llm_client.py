#backend\services\llm_client.py
import os
from typing import Protocol, Optional, Dict, Any
import logging
import httpx
import json
from dotenv import load_dotenv

load_dotenv(override=True)


logger = logging.getLogger(__name__)

class LLMClient(Protocol):
    """Protocol for LLM clients supporting multiple providers"""
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
            prompt = f'''Based on this user message, generate a short, descriptive title (maximum 5 words) for the conversation. 
            
User message: "{message}"
            
Respond with ONLY the title, no quotes, no explanation.'''
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-1.5-flash:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 15}
                    }
                )
            
            if response.status_code == 200:
                title = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                # Remove quotes if present
                title = title.strip('"').strip("'").strip()
                # Limit to 50 characters
                return title[:50] if len(title) > 50 else title
            else:
                return "New Chat"

        except Exception as e:
            logger.error(f"Error generating session name: {e}")
            return "New Chat"

class OpenRouterClient:
    """Client for OpenRouter API - supports multiple models including Claude, GPT-4, etc."""

    def __init__(self):
        self.api_key = (
            self._load_api_key_from_storage("openrouter_api_key") or
            os.getenv('OPENROUTER_API_KEY')
        )
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-70b-instruct")

        if self.api_key:
            logger.info(f"OpenRouter API key loaded successfully with model: {self.model}")
        else:
            logger.warning("OpenRouter API key not found. Please set OPENROUTER_API_KEY environment variable.")

    def _load_api_key_from_storage(self, key_name: str) -> Optional[str]:
        """Load API key from local storage file"""
        try:
            config_file = os.path.expanduser("~/.smartfile_ai_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get(key_name)
        except Exception as e:
            logger.debug(f"Could not load config file: {str(e)}")
        return None

    async def generate_answer(self, question: str, context: str) -> str:
        if not self.api_key:
            return """OpenRouter API key not configured. Please:

1. Get your API key from https://openrouter.ai/
2. Set the OPENROUTER_API_KEY environment variable, or
3. Configure it in the Settings page
"""

        try:
            prompt = f"""Based on the following context from the user's files, please answer the question accurately and helpfully.

Context from files:
{context}

Question: {question}

Please provide a clear, helpful answer based on the information in the context. If the context doesn't contain enough information to fully answer the question, please say so and provide what information you can based on what's available."""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "http://localhost",
                        "X-Title": "SmartFile AI"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "max_tokens": 1024,
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        return "I received an empty response from the AI service. Please try rephrasing your question."
                else:
                    error_msg = f"OpenRouter API error: {response.status_code}"
                    if response.status_code == 401:
                        error_msg += " - Invalid API key"
                    elif response.status_code == 429:
                        error_msg += " - Rate limit exceeded, please try again later"

                    logger.error(f"{error_msg} - {response.text}")
                    return f"Error calling OpenRouter API: {error_msg}"

        except httpx.TimeoutException:
            logger.error("OpenRouter API request timed out")
            return "The AI service request timed out. Please try again."
        except Exception as e:
            logger.error(f"Error generating answer with OpenRouter: {str(e)}")
            return f"Error generating answer: {str(e)}"

    async def rerank_results(self, query: str, results: list) -> list:
        if not self.api_key:
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.5)
            return results

        try:
            documents = [
                {
                    "id": str(i),
                    "content": f"File: {res['file_name']}\nContent: {res['content'][:300]}"
                } for i, res in enumerate(results)
            ]

            prompt = f"""Given the user's query and the following documents, evaluate relevance. Return JSON with document IDs and scores (0.0-1.0).

Query: "{query}"

Documents:
{json.dumps(documents, indent=2)}

Respond with ONLY the JSON object:
{{"0": 0.9, "1": 0.2}}"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "http://localhost",
                        "X-Title": "SmartFile AI"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0,
                    }
                )

            if response.status_code == 200:
                raw_text = response.json()["choices"][0]["message"]["content"]
                
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
                    for result in results:
                        result['relevance_score'] = result.get('similarity_score', 0.0)
                    return results
            else:
                for result in results:
                    result['relevance_score'] = result.get('similarity_score', 0.0)
                return results

        except Exception as e:
            logger.error(f"Error during reranking: {e}", exc_info=True)
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

    async def generate_session_name(self, message: str) -> str:
        if not self.api_key:
            return "New Chat"

        try:
            prompt = f'''Based on this user message, generate a short, descriptive title (maximum 5 words) for the conversation. 
            
User message: "{message}"
            
Respond with ONLY the title, no quotes, no explanation.'''

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "http://localhost",
                        "X-Title": "SmartFile AI"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 15
                    }
                )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip().strip('"')
            else:
                return "Chat"

        except Exception as e:
            logger.error(f"Error generating session name: {e}")
            return "Chat"


class GroqClient:
    """Client for Groq API - fastest LLM inference engine"""

    def __init__(self):
        self.api_key = (
            self._load_api_key_from_storage("groq_api_key") or
            os.getenv('GROQ_API_KEY')
        )
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")

        deprecated_models = {
            "llama2-70b-4096": "llama-3.1-8b-instant",
        }
        if self.model in deprecated_models:
            replacement = deprecated_models[self.model]
            logger.warning(f"Deprecated/invalid Groq model '{self.model}' detected. Using '{replacement}' instead.")
            self.model = replacement

        if self.api_key:
            logger.info(f"Groq API key loaded successfully with model: {self.model}")
        else:
            logger.warning("Groq API key not found. Please set GROQ_API_KEY environment variable.")

    def _load_api_key_from_storage(self, key_name: str) -> Optional[str]:
        """Load API key from local storage file"""
        try:
            config_file = os.path.expanduser("~/.smartfile_ai_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get(key_name)
        except Exception as e:
            logger.debug(f"Could not load config file: {str(e)}")
        return None

    async def generate_answer(self, question: str, context: str) -> str:
        if not self.api_key:
            return """Groq API key not configured. Please:

1. Get your API key from https://console.groq.com/
2. Set the GROQ_API_KEY environment variable, or
3. Configure it in the Settings page
"""

        try:
            prompt = f"""Based on the following context from the user's files, please answer the question accurately and helpfully.

Context from files:
{context}

Question: {question}

Please provide a clear, helpful answer."""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        return "Empty response from the AI service."
                else:
                    error_msg = f"Groq API error: {response.status_code}"
                    logger.error(f"{error_msg} - {response.text}")
                    return f"Error calling Groq API: {error_msg}"

        except httpx.TimeoutException:
            logger.error("Groq API request timed out")
            return "The AI service request timed out."
        except Exception as e:
            logger.error(f"Error with Groq: {str(e)}")
            return f"Error: {str(e)}"

    async def rerank_results(self, query: str, results: list) -> list:
        if not self.api_key:
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.5)
            return results

        try:
            documents = [
                {"id": str(i), "content": f"File: {res['file_name']}\nContent: {res['content'][:250]}"}
                for i, res in enumerate(results)
            ]

            prompt = f"""Query: "{query}"\n\nDocuments: {json.dumps(documents)}\n\nReturn JSON with relevance scores: {{"0": 0.9}}"""

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.0,
                    }
                )

            if response.status_code == 200:
                raw_text = response.json()["choices"][0]["message"]["content"]
                
                def extract_json(text: str) -> Optional[dict]:
                    start = text.find('{')
                    end = text.rfind('}')
                    if start != -1 and end != -1:
                        try:
                            return json.loads(text[start:end+1])
                        except json.JSONDecodeError:
                            return None
                    return None

                rerank_data = extract_json(raw_text)
                if rerank_data:
                    for i, result in enumerate(results):
                        result['relevance_score'] = rerank_data.get(str(i), 0.0)
                    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
                else:
                    for result in results:
                        result['relevance_score'] = result.get('similarity_score', 0.0)
                    return results
            else:
                for result in results:
                    result['relevance_score'] = result.get('similarity_score', 0.0)
                return results

        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

    async def generate_session_name(self, message: str) -> str:
        if not self.api_key:
            return "New Chat"

        try:
            prompt = f'''Based on this user message, generate a short, descriptive title (maximum 5 words) for the conversation. 
            
User message: "{message}"
            
Respond with ONLY the title, no quotes, no explanation.'''

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 15
                    }
                )

            if response.status_code == 200:
                title = response.json()["choices"][0]["message"]["content"].strip()
                # Remove quotes if present
                title = title.strip('"').strip("'").strip()
                # Limit to 50 characters
                return title[:50] if len(title) > 50 else title
            else:
                return "New Chat"

        except Exception as e:
            logger.error(f"Error generating session name: {e}")
            return "New Chat"


class OpenAIClient:
    """Client for OpenAI API (GPT-4, GPT-3.5, etc.)"""

    def __init__(self):
        self.api_key = (
            self._load_api_key_from_storage("openai_api_key") or
            os.getenv('OPENAI_API_KEY')
        )
        self.base_url = "https://api.openai.com/v1"
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        if self.api_key:
            logger.info(f"OpenAI API key loaded successfully with model: {self.model}")
        else:
            logger.warning("OpenAI API key not found.")

    def _load_api_key_from_storage(self, key_name: str) -> Optional[str]:
        """Load API key from local storage file"""
        try:
            config_file = os.path.expanduser("~/.smartfile_ai_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get(key_name)
        except Exception as e:
            logger.debug(f"Could not load config file: {str(e)}")
        return None

    async def generate_answer(self, question: str, context: str) -> str:
        if not self.api_key:
            return """OpenAI API key not configured. Please configure it in Settings."""

        try:
            prompt = f"""Based on the following context from the user's files, answer the question.

Context:
{context}

Question: {question}

Answer:"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 1024,
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    else:
                        return "Empty response from OpenAI API."
                else:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Error with OpenAI: {str(e)}")
            return f"Error: {str(e)}"

    async def rerank_results(self, query: str, results: list) -> list:
        if not self.api_key:
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.5)
            return results

        try:
            docs = [{"id": str(i), "content": f"{res['file_name']}: {res['content'][:250]}"} for i, res in enumerate(results)]
            prompt = f"""Query: {query}\n\nDocs: {json.dumps(docs)}\n\nReturn JSON: {{"0": 0.9}}"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
                )

            if response.status_code == 200:
                raw_text = response.json()["choices"][0]["message"]["content"]
                start = raw_text.find('{')
                end = raw_text.rfind('}')
                if start != -1 and end != -1:
                    try:
                        data = json.loads(raw_text[start:end+1])
                        for i, result in enumerate(results):
                            result['relevance_score'] = data.get(str(i), 0.0)
                        return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
                    except:
                        pass
            
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

        except Exception as e:
            logger.error(f"Error reranking: {e}")
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

    async def generate_session_name(self, message: str) -> str:
        if not self.api_key:
            return "New Chat"

        try:
            prompt = f'''Based on this user message, generate a short, descriptive title (maximum 5 words) for the conversation. 
            
User message: "{message}"
            
Respond with ONLY the title, no quotes, no explanation.'''

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 15
                    }
                )

            if response.status_code == 200:
                title = response.json()["choices"][0]["message"]["content"].strip()
                # Remove quotes if present
                title = title.strip('"').strip("'").strip()
                # Limit to 50 characters
                return title[:50] if len(title) > 50 else title
            return "New Chat"

        except Exception as e:
            logger.error(f"Error: {e}")
            return "New Chat"


class AnthropicClient:
    """Client for Anthropic Claude API"""

    def __init__(self):
        self.api_key = (
            self._load_api_key_from_storage("anthropic_api_key") or
            os.getenv('ANTHROPIC_API_KEY')
        )
        self.base_url = "https://api.anthropic.com/v1"
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

        if self.api_key:
            logger.info(f"Anthropic API key loaded successfully with model: {self.model}")
        else:
            logger.warning("Anthropic API key not found.")

    def _load_api_key_from_storage(self, key_name: str) -> Optional[str]:
        """Load API key from local storage file"""
        try:
            config_file = os.path.expanduser("~/.smartfile_ai_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get(key_name)
        except Exception as e:
            logger.debug(f"Could not load config file: {str(e)}")
        return None

    async def generate_answer(self, question: str, context: str) -> str:
        if not self.api_key:
            return """Anthropic API key not configured. Please configure it in Settings."""

        try:
            prompt = f"""Based on the following context from the user's files, answer the question.

Context:
{context}

Question: {question}

Answer:"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if "content" in result and len(result["content"]) > 0:
                        return result["content"][0]["text"]
                    else:
                        return "Empty response from Claude API."
                else:
                    logger.error(f"Claude API error: {response.status_code} - {response.text}")
                    return f"Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Error with Claude: {str(e)}")
            return f"Error: {str(e)}"

    async def rerank_results(self, query: str, results: list) -> list:
        if not self.api_key:
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.5)
            return results

        try:
            docs = [{"id": str(i), "content": f"{res['file_name']}: {res['content'][:250]}"} for i, res in enumerate(results)]
            prompt = f"""Query: {query}\n\nDocs: {json.dumps(docs)}\n\nReturn JSON: {{"0": 0.9}}"""

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )

            if response.status_code == 200:
                raw_text = response.json()["content"][0]["text"]
                start = raw_text.find('{')
                end = raw_text.rfind('}')
                if start != -1 and end != -1:
                    try:
                        data = json.loads(raw_text[start:end+1])
                        for i, result in enumerate(results):
                            result['relevance_score'] = data.get(str(i), 0.0)
                        return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
                    except:
                        pass
            
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

        except Exception as e:
            logger.error(f"Error reranking: {e}")
            for result in results:
                result['relevance_score'] = result.get('similarity_score', 0.0)
            return results

    async def generate_session_name(self, message: str) -> str:
        if not self.api_key:
            return "New Chat"

        try:
            prompt = f'''Based on this user message, generate a short, descriptive title (maximum 5 words) for the conversation. 
            
User message: "{message}"
            
Respond with ONLY the title, no quotes, no explanation.'''

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 20,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )

            if response.status_code == 200:
                title = response.json()["content"][0]["text"].strip()
                # Remove quotes if present
                title = title.strip('"').strip("'").strip()
                # Limit to 50 characters
                return title[:50] if len(title) > 50 else title
            return "New Chat"

        except Exception as e:
            logger.error(f"Error: {e}")
            return "New Chat"


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
        prompt = f'''Based on this user message, generate a short, descriptive title (maximum 5 words) for the conversation. 
        
User message: "{message}"
        
Respond with ONLY the title, no quotes, no explanation.'''
        
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
                title = response.json().get("response", "New Chat").strip()
                # Remove quotes if present
                title = title.strip('"').strip("'").strip()
                # Limit to 50 characters
                return title[:50] if len(title) > 50 and title else title if title else "New Chat"
            else:
                return "New Chat"

        except Exception as e:
            logger.error(f"Error generating session name with Ollama: {e}")
            return "New Chat"


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
    """Factory for creating LLM clients with support for multiple providers"""
    _clients = {}

    @staticmethod
    def clear_cache(client_type: str = None):
        """Clear cached clients. If client_type is provided, clear only that type."""
        if client_type:
            client_type = client_type.lower().strip()
            if client_type in LLMClientFactory._clients:
                logger.info(f"Clearing cached client for: {client_type}")
                del LLMClientFactory._clients[client_type]
        else:
            logger.info("Clearing all cached LLM clients")
            LLMClientFactory._clients.clear()

    @staticmethod
    def create_client(client_type: str = "ollama") -> LLMClient:
        """Create an LLM client of the specified type with fallback support"""
        client_type = client_type.lower().strip() if client_type else "ollama"

        if client_type in LLMClientFactory._clients:
            return LLMClientFactory._clients[client_type]

        logger.info(f"Creating LLM client of type: {client_type}")

        try:
            if client_type == "gemini":
                client = GeminiClient()
                if not client.api_key:
                    raise ValueError("Gemini API key not found.")
                LLMClientFactory._clients[client_type] = client
                return client

            elif client_type == "openrouter":
                client = OpenRouterClient()
                if not client.api_key:
                    raise ValueError("OpenRouter API key not found.")
                LLMClientFactory._clients[client_type] = client
                return client

            elif client_type == "groq":
                client = GroqClient()
                if not client.api_key:
                    raise ValueError("Groq API key not found.")
                LLMClientFactory._clients[client_type] = client
                return client

            elif client_type == "openai":
                client = OpenAIClient()
                if not client.api_key:
                    raise ValueError("OpenAI API key not found.")
                LLMClientFactory._clients[client_type] = client
                return client

            elif client_type == "anthropic":
                client = AnthropicClient()
                if not client.api_key:
                    raise ValueError("Anthropic API key not found.")
                LLMClientFactory._clients[client_type] = client
                return client

            elif client_type == "ollama":
                client = OllamaClient()
                if not client.initialized:
                    raise ValueError("Ollama service not initialized.")
                LLMClientFactory._clients[client_type] = client
                return client
            
            elif client_type in ["local", "phi"]:
                logger.warning(f"Client type '{client_type}' is deprecated, using 'ollama' instead.")
                return LLMClientFactory.create_client("ollama")

            else:
                logger.error(f"Unknown LLM client type: {client_type}")
                return FallbackClient()

        except Exception as e:
            logger.error(f"Failed to create {client_type} client: {e}")
            return FallbackClient()

    @staticmethod
    def get_available_providers() -> Dict[str, Dict[str, Any]]:
        """Return information about available LLM providers"""
        return {
            "gemini": {
                "name": "Google Gemini",
                "display_name": "Google Gemini (Cloud)",
                "type": "cloud",
                "requires_key": True,
                "api_key_name": "gemini_api_key",
                "env_var": "GEMINI_API_KEY",
                "url": "https://ai.google.dev/",
                "models": ["gemini-2.5-flash", "gemini-1.5-flash"],
                "default_model": "gemini-2.5-flash",
                "capabilities": ["generate_answer", "rerank", "session_naming"]
            },
            "openrouter": {
                "name": "OpenRouter",
                "display_name": "OpenRouter (Multi-Model)",
                "type": "cloud",
                "requires_key": True,
                "api_key_name": "openrouter_api_key",
                "env_var": "OPENROUTER_API_KEY",
                "url": "https://openrouter.ai/",
                "models": ["meta-llama/llama-3.1-8b-instruct", "openai/gpt-4o-mini", "anthropic/claude-3.5-sonnet"],
                "default_model": "meta-llama/llama-3.1-8b-instruct",
                "capabilities": ["generate_answer", "rerank", "session_naming"]
            },
            "groq": {
                "name": "Groq",
                "display_name": "Groq (Fast Inference)",
                "type": "cloud",
                "requires_key": True,
                "api_key_name": "groq_api_key",
                "env_var": "GROQ_API_KEY",
                "url": "https://console.groq.com/",
                "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
                "default_model": "llama-3.1-8b-instant",
                "capabilities": ["generate_answer", "rerank", "session_naming"]
            },
            "openai": {
                "name": "OpenAI",
                "display_name": "OpenAI (GPT Models)",
                "type": "cloud",
                "requires_key": True,
                "api_key_name": "openai_api_key",
                "env_var": "OPENAI_API_KEY",
                "url": "https://platform.openai.com/",
                "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "default_model": "gpt-3.5-turbo",
                "capabilities": ["generate_answer", "rerank", "session_naming"]
            },
            "anthropic": {
                "name": "Anthropic",
                "display_name": "Anthropic Claude (Advanced AI)",
                "type": "cloud",
                "requires_key": True,
                "api_key_name": "anthropic_api_key",
                "env_var": "ANTHROPIC_API_KEY",
                "url": "https://console.anthropic.com/",
                "models": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-latest"],
                "default_model": "claude-3-5-sonnet-latest",
                "capabilities": ["generate_answer", "rerank", "session_naming"]
            },
            "ollama": {
                "name": "Ollama",
                "display_name": "Ollama (Local LLM)",
                "type": "local",
                "requires_key": False,
                "api_key_name": None,
                "env_var": "OLLAMA_BASE_URL",
                "url": "https://ollama.ai/",
                "models": ["llama3.2:3b", "mistral:7b", "qwen2.5:7b", "llava:7b"],
                "default_model": "llama3.2:3b",
                "capabilities": ["generate_answer", "rerank", "session_naming"]
            }
        }
