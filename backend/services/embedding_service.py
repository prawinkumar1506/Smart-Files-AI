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
from typing import List, Dict, Union, Optional
import logging
import traceback
import os
import json

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

            # Always use the local model path
            logger.info(f"Loading model from local path: {self.local_model_path}")
            self.model = SentenceTransformer(self.local_model_path)


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

    async def generate_image_embedding(self, file_path: str) -> Dict[str, Union[np.ndarray, str]]:
        """
        Generate embeddings for an image file using CLIP and BLIP models.
        Returns a dictionary with image_embedding, text_embedding, and caption.
        """
        try:
            from services.file_processors import FileProcessorFactory
            from pathlib import Path

            # Get the image processor
            file_path_obj = Path(file_path)
            processor = FileProcessorFactory.get_processor(file_path_obj.suffix)

            # Check if it's an image processor
            if hasattr(processor, 'get_image_embedding'):
                # Use the image processor to get embeddings
                result = await processor.get_image_embedding(file_path_obj)

                # Validate the result
                if result["image_embedding"] is None or result["text_embedding"] is None:
                    logger.warning(f"Generated empty embeddings for image: {file_path}")
                    # Fallback to text embedding using the caption
                    caption = result.get("caption", "")
                    if caption:
                        text_embedding = await self.generate_embedding(f"image caption: {caption}")
                        return {
                            "image_embedding": np.zeros(self.get_embedding_dimension(), dtype=np.float32),
                            "text_embedding": text_embedding,
                            "caption": caption
                        }
                    else:
                        # If no caption, use a default embedding
                        return {
                            "image_embedding": np.zeros(self.get_embedding_dimension(), dtype=np.float32),
                            "text_embedding": await self.generate_embedding("empty image content"),
                            "caption": ""
                        }

                return result
            else:
                # For non-image files, use the regular text embedding approach
                # Extract text content
                text_content = await processor.extract_text(file_path_obj)

                # Generate text embedding
                text_embedding = await self.generate_embedding(text_content)

                return {
                    "image_embedding": None,
                    "text_embedding": text_embedding,
                    "caption": ""
                }

        except Exception as e:
            logger.error(f"Failed to generate image embedding for {file_path}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Fallback to a default embedding
            return {
                "image_embedding": np.zeros(self.get_embedding_dimension(), dtype=np.float32),
                "text_embedding": await self.generate_embedding("empty image content"),
                "caption": ""
            }

    async def generate_image_embeddings(self, file_paths: List[str]) -> List[Dict[str, Union[np.ndarray, str]]]:
        """
        Generate embeddings for multiple image files.
        Returns a list of dictionaries with image_embedding, text_embedding, and caption for each file.
        """
        results = []
        for file_path in file_paths:
            try:
                result = await self.generate_image_embedding(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate embedding for {file_path}: {str(e)}")
                results.append({
                    "image_embedding": np.zeros(self.get_embedding_dimension(), dtype=np.float32),
                    "text_embedding": await self.generate_embedding("empty image content"),
                    "caption": ""
                })
        return results
