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

            for image in images:
                if not image.get("caption"):
                    image["caption"] = "Description not available"

            return images
        except Exception as e:
            print(f"Error fetching indexed images: {e}")
            return []

    async def search_images(self, query: str) -> List[Dict]:
        """
        Search images using semantic similarity across text embeddings, captions, tags,
        filenames, and metadata. Returns results ranked by relevance.
        """
        try:
            import re
            from datetime import datetime
            
            # Generate text embedding for the query
            query_embedding = await self.embedding_service.generate_embedding(f"query: {query}")
            
            # Get semantic matches from vector store
            similar_images = await self.vector_store.search_images(query_embedding, limit=100, threshold=0.1)
            
            # Enhance rankings by also matching metadata
            query_lower = query.lower()
            
            for image in similar_images:
                # Start with semantic similarity score
                relevance_score = image.get("similarity_score", 0)
                
                # Extract metadata
                metadata = image.get("metadata", {})
                caption = image.get("caption", "").lower()
                file_name = image.get("file_name", "").lower()
                tags = metadata.get("tags", [])
                
                # Bonus for caption match
                if query_lower in caption:
                    relevance_score += 0.15
                
                # Bonus for filename match
                if query_lower in file_name:
                    relevance_score += 0.20
                
                # Bonus for tag matches
                for tag in tags:
                    if query_lower in str(tag).lower():
                        relevance_score += 0.10
                
                # Check for date-related queries
                if any(word in query_lower for word in ['date', 'recent', 'old', 'today', 'week', 'month', 'year']):
                    date_modified = metadata.get("date_modified", "")
                    if date_modified:
                        try:
                            # Parse date and check relevance
                            date_obj = datetime.fromisoformat(date_modified)
                            now = datetime.now(date_obj.tzinfo) if date_obj.tzinfo else datetime.now()
                            days_ago = (now - date_obj).days
                            
                            # Boost recent files for "recent" queries
                            if 'recent' in query_lower and days_ago < 30:
                                relevance_score += 0.20
                            # Boost old files for "old" queries  
                            elif 'old' in query_lower and days_ago > 365:
                                relevance_score += 0.20
                        except:
                            pass
                
                # Update the similarity score with enhanced relevance
                image["similarity_score"] = min(1.0, relevance_score)
            
            # Sort by enhanced relevance score
            similar_images.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            
            return similar_images[:50]  # Return top 50 results
        except Exception as e:
            print(f"Error searching images: {e}")
            import traceback
            traceback.print_exc()
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
