# #backend\services\embedding_service.py
# import numpy as np
# from typing import List
# import logging
# from sentence_transformers import SentenceTransformer
#
# logger = logging.getLogger(__name__)
#
# class EmbeddingService:
#     def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
#         """Initialize the embedding service with a sentence transformer model"""
#         self.model_name = model_name
#         self.model = None
#         self._load_model()
#
#     def _load_model(self):
#         """Load the sentence transformer model"""
#         try:
#             self.model = SentenceTransformer(self.model_name)
#             logger.info(f"Loaded embedding model: {self.model_name}")
#         except Exception as e:
#             logger.error(f"Failed to load embedding model: {str(e)}")
#             raise
#
#     async def generate_embedding(self, text: str) -> np.ndarray:
#         """Generate embedding for a single text"""
#         if not self.model:
#             raise RuntimeError("Embedding model not loaded")
#
#         try:
#             # Generate embedding
#             embedding = self.model.encode(text, convert_to_numpy=True)
#             return embedding.astype(np.float32)
#         except Exception as e:
#             logger.error(f"Failed to generate embedding: {str(e)}")
#             raise
#
#     async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
#         """Generate embeddings for multiple texts"""
#         if not self.model:
#             raise RuntimeError("Embedding model not loaded")
#
#         try:
#             embeddings = self.model.encode(texts, convert_to_numpy=True)
#             return [emb.astype(np.float32) for emb in embeddings]
#         except Exception as e:
#             logger.error(f"Failed to generate embeddings: {str(e)}")
#             raise
#
#     def get_embedding_dimension(self) -> int:
#         """Get the dimension of the embeddings"""
#         if not self.model:
#             raise RuntimeError("Embedding model not loaded")
#         return self.model.get_sentence_embedding_dimension()
import numpy as np
from typing import List
import logging
import traceback
import os

# Suppress the symlink warning from huggingface_hub
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "intfloat/e5-small-v2"):
        """Initialize the embedding service with a sentence transformer model"""
        self.model_name = model_name
        self.model = None
        self.local_model_path = os.path.join(os.path.dirname(__file__), '..', 'embedding_model', self.model_name.replace('/', '_'))
        self._load_model()

    def _load_model(self):
        """Load the sentence transformer model from local path if available, otherwise download and save it."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")

            # Try to import sentence_transformers
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                logger.error("sentence-transformers not installed. Please install it with: pip install sentence-transformers")
                raise ImportError("sentence-transformers package is required") from e

            # Check if the model is available locally
            if os.path.exists(self.local_model_path):
                logger.info(f"Found local model at: {self.local_model_path}")
                self.model = SentenceTransformer(self.local_model_path)
            else:
                logger.info("Local model not found. Downloading from Hugging Face Hub...")
                # Load the model from Hugging Face Hub
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"Saving model to: {self.local_model_path}")
                # Create directory if it doesn't exist
                os.makedirs(self.local_model_path, exist_ok=True)
                # Save the model for future offline use
                self.model.save(self.local_model_path)


            # Test the model with a simple sentence
            test_embedding = self.model.encode("test sentence", convert_to_numpy=True)
            logger.info(f"Embedding model loaded successfully")
            logger.info(f"Model info: {self.model_name}, embedding dimension: {len(test_embedding)}")

        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")

        try:
            # Clean and validate input text
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                text = "empty content"

            text = text.strip()

            # Log text info for debugging
            logger.debug(f"Generating embedding for text (length: {len(text)}): '{text[:100]}{'...' if len(text) > 100 else ''}'")

            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)

            # Validate embedding
            if embedding is None or len(embedding) == 0:
                raise ValueError("Generated embedding is empty")

            embedding = embedding.astype(np.float32)
            logger.debug(f"Generated embedding with shape: {embedding.shape}")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding for text: '{text[:100]}...'")
            logger.error(f"Error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")

        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")

            # Clean texts
            cleaned_texts = []
            for text in texts:
                if text and text.strip():
                    cleaned_texts.append(text.strip())
                else:
                    cleaned_texts.append("empty content")

            embeddings = self.model.encode(cleaned_texts, convert_to_numpy=True)
            result = [emb.astype(np.float32) for emb in embeddings]

            logger.info(f"Generated {len(result)} embeddings")
            return result

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        if not self.model:
            raise RuntimeError("Embedding model not loaded")
        return self.model.get_sentence_embedding_dimension()
