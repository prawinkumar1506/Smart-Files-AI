import os
import json
from typing import List, Dict, Optional, Union
from datetime import datetime
import numpy as np
from services.vector_store import VectorStore
from services.file_processors import FileProcessorFactory
from services.embedding_service import EmbeddingService

class SmartImagesService:
    def __init__(self, vector_store=None, embedding_service=None):
        # Use provided vector_store or create a new one
        self.vector_store = vector_store
        self.embedding_service = embedding_service or EmbeddingService()
        self.llm_client = None
        self.images_dir = "data/images"

    async def get_indexed_images(self) -> List[Dict]:
        """Fetch all indexed images from the vector store with captions."""
        try:
            images = await self.vector_store.get_all_images()

            # Ensure each image has a caption
            for image in images:
                if not image.get("caption") or image["caption"].startswith("A detailed description"):
                    # Generate a caption if missing or default
                    if self.llm_client:
                        try:
                            prompt = f"""
                            Provide a detailed 4-5 sentence description of an image with filename: {image.get("file_name", "unknown")}.
                            Include all important visual elements, describe the context and purpose of the image.
                            Be clear, accurate, and professional.
                            """
                            caption = await self.llm_client.generate_answer(
                                question=f"Describe this image: {image.get('file_name', 'unknown')}",
                                context=f"Filename: {image.get('file_name', 'unknown')}"
                            )
                            image["caption"] = caption
                        except Exception as e:
                            print(f"Error generating caption for {image.get('file_name', 'unknown')}: {e}")
                            image["caption"] = "Description not available"

            return images
        except Exception as e:
            print(f"Error fetching indexed images: {e}")
            return []

    async def search_images(self, query: str) -> List[Dict]:
        """Search images by text query using text embeddings."""
        try:
            # Generate text embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(f"query: {query}")

            # Search for similar images using text embeddings
            similar_images = await self.vector_store.search_images(query_embedding)
            return similar_images
        except Exception as e:
            print(f"Error searching images: {e}")
            return []

    def rename_image(self, image_id: int, new_name: str) -> bool:
        """Rename an image and update its metadata."""
        try:
            # Get the image metadata from the vector store
            image_metadata = self.vector_store.get_image_by_id(image_id)
            if not image_metadata:
                return False

            # Update the image name in the metadata
            old_file_path = image_metadata["file_path"]
            old_file_name = image_metadata["file_name"]
            new_file_path = os.path.join(
                os.path.dirname(old_file_path),
                new_name
            )

            # Rename the image file
            os.rename(old_file_path, new_file_path)

            # Update the image metadata in the vector store
            updated_metadata = {
                **image_metadata,
                "file_path": new_file_path,
                "file_name": new_name,
                "new_name": new_name
            }
            self.vector_store.update_image(image_id, updated_metadata)

            return True
        except Exception as e:
            print(f"Error renaming image: {e}")
            return False

    async def index_folder(self, folder_path: str) -> List[Dict]:
        """Index a folder containing image files."""
        try:
            from services.indexer import FileIndexer
            from services.llm_client import LLMClientFactory

            # Create LLM client
            llm_client = LLMClientFactory.create_client()

            # Use the FileIndexer to process the folder with LLM client
            indexer = FileIndexer(self.vector_store, self.embedding_service, llm_client)

            # Process the folder and get results
            async for file_path, processed_count in indexer.index_folder(folder_path):
                pass  # Just process all files

            # Get the indexed images
            images = await self.vector_store.get_all_images()
            return images
        except Exception as e:
            print(f"Error indexing folder: {e}")
            return []
