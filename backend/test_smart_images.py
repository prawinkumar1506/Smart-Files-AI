import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vector_store import VectorStore
from services.smart_images_service import SmartImagesService
from services.embedding_service import EmbeddingService

async def test_smart_images():
    """Test the SmartImagesService with our changes"""
    # Initialize the vector store
    vector_store = VectorStore()
    await vector_store.initialize()

    # Create the smart images service with the shared vector store
    smart_images_service = SmartImagesService(vector_store=vector_store)

    # Test getting indexed images
    try:
        images = await smart_images_service.get_indexed_images()
        print(f"Successfully retrieved {len(images)} indexed images")
        if images:
            print(f"Sample image: {images[0].get('file_name', 'No name')}")
    except Exception as e:
        print(f"Error getting indexed images: {e}")

    # Close the vector store
    vector_store.close()

if __name__ == "__main__":
    asyncio.run(test_smart_images())
