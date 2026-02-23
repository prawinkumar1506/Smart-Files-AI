"""
Smart Images AI - Image Indexing and Search Pipeline Test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This script tests the Smart Images AI implementation with:
1. EXIF metadata extraction
2. Ollama LLaVA vision model for image analysis
3. Vector embeddings for semantic search
4. Metadata tagging and filtering
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.vector_store import VectorStore
from services.embedding_service import EmbeddingService
from services.file_processors import ImageProcessor, FileProcessorFactory
from services.indexer import FileIndexer
from services.llm_client import LLMClientFactory

logger_enabled = True

def log(msg: str):
    if logger_enabled:
        print(f"[✓] {msg}")

def log_success(msg: str):
    print(f"[✓] SUCCESS: {msg}")

def log_error(msg: str):
    print(f"[✗] ERROR: {msg}")

def log_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def test_image_processor():
    """Test the image processor with a sample image"""
    log_section("Testing Image Processor with Ollama LLaVA")
    
    # Check if test image exists
    test_image_path = Path("test_image.jpg")
    if not test_image_path.exists():
        log_error("No test_image.jpg found in backend directory")
        log("To test with a real image, add test_image.jpg to the backend folder")
        return
    
    try:
        processor = ImageProcessor()
        log("Initialized ImageProcessor")
        
        # Extract text (this calls Ollama LLaVA)
        log("Calling Ollama LLaVA for image analysis...")
        text_result = await processor.extract_text(test_image_path)
        result = json.loads(text_result)
        
        log_success("Image analysis complete!")
        log(f"Caption: {result.get('caption', 'N/A')[:100]}...")
        log(f"Objects detected: {result.get('analysis', {}).get('objects', [])}")
        log(f"Tags generated: {result.get('metadata', {}).get('tags', [])}")
        
        return True
    except Exception as e:
        log_error(f"Image processor test failed: {e}")
        return False

async def test_exif_extraction():
    """Test EXIF metadata extraction"""
    log_section("Testing EXIF Metadata Extraction")
    
    test_image_path = Path("test_image.jpg")
    if not test_image_path.exists():
        log("Skipping EXIF test (no test image)")
        return
    
    try:
        processor = ImageProcessor()
        metadata = processor._extract_image_metadata(test_image_path)
        
        log_success("EXIF extraction successful!")
        log(f"Format: {metadata.get('format')}")
        log(f"Size: {metadata.get('size')}")
        log(f"Created: {metadata.get('created_at')}")
        exif = metadata.get('exif', {})
        if exif.get('date_taken'):
            log(f"Date taken (EXIF): {exif['date_taken']}")
        if exif.get('gps'):
            log(f"GPS: {exif['gps']}")
        return True
    except Exception as e:
        log_error(f"EXIF extraction failed: {e}")
        return False

async def test_vector_store():
    """Test vector store initialization"""
    log_section("Testing Vector Store")
    
    try:
        vector_store = VectorStore()
        await vector_store.initialize()
        log_success("Vector store initialized")
        
        stats = await vector_store.get_debug_stats()
        log(f"Indexed folders: {stats.get('folders', 0)}")
        log(f"Indexed files: {stats.get('files', 0)}")
        log(f"Document chunks: {stats.get('chunks', 0)}")
        
        return vector_store
    except Exception as e:
        log_error(f"Vector store initialization failed: {e}")
        return None

async def test_embedding_service():
    """Test embedding service"""
    log_section("Testing Embedding Service")
    
    try:
        embedding_service = EmbeddingService()
        log("Initialized EmbeddingService")
        
        # Test generating embedding
        test_text = "A man wearing a blue shirt standing on the beach"
        embedding = await embedding_service.generate_embedding(test_text)
        
        log_success("Embedding generation successful!")
        log(f"Embedding dimension: {len(embedding)}")
        log(f"Embedding shape: {embedding.shape}")
        
        return embedding_service
    except Exception as e:
        log_error(f"Embedding service failed: {e}")
        return None

async def test_ollama_connection():
    """Test Ollama connection"""
    log_section("Testing Ollama Connection")
    
    try:
        import httpx
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava:latest")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                log_success("Ollama is running!")
                log(f"Available models: {len(models)}")
                
                model_names = [m.get("name") for m in models]
                if vision_model in model_names:
                    log_success(f"Vision model '{vision_model}' is installed")
                else:
                    log_error(f"Vision model '{vision_model}' not found")
                    log(f"Available: {model_names}")
                
                return True
            else:
                log_error(f"Ollama connection failed: {response.status_code}")
                return False
    except Exception as e:
        log_error(f"Ollama connection test failed: {e}")
        log("Make sure Ollama is running: ollama serve")
        return False

async def test_search_text_generation():
    """Test search text generation"""
    log_section("Testing Search Text Generation")
    
    try:
        processor = ImageProcessor()
        
        caption = "A woman cooking in a modern kitchen"
        analysis = {
            "objects": ["woman", "stove", "kitchen", "pot"],
            "people_count": 1,
            "clothing": ["apron", "chef's hat"],
            "colors": ["white", "stainless steel"],
            "scene": "kitchen",
            "activity": "cooking",
            "context": "home cooking"
        }
        metadata = {
            "exif": {"date_taken": "2024-01-15"},
            "created_at": "2024-01-15T10:30:00"
        }
        
        search_text = processor._build_search_text(caption, analysis, metadata)
        log_success("Search text generated!")
        log(f"Search text length: {len(search_text)} chars")
        log(f"Preview: {search_text[:150]}...")
        
        return True
    except Exception as e:
        log_error(f"Search text generation failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  SMART IMAGES AI - IMPLEMENTATION TEST SUITE")
    print("="*60)
    
    results = {
        "Ollama Connection": await test_ollama_connection(),
        "Vector Store": await test_vector_store() is not None,
        "Embedding Service": await test_embedding_service() is not None,
        "Search Text Generation": await test_search_text_generation(),
        "EXIF Extraction": await test_exif_extraction(),
        "Image Processor": await test_image_processor(),
    }
    
    log_section("Test Results Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "[✓] PASS" if passed_test else "[✗] SKIP/FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Overall: {passed}/{total} tests passed\n")
    
    log_section("Next Steps")
    print("""
1. Install Ollama:
   - Download from https://ollama.ai
   - Run: ollama serve
   - Pull vision model: ollama pull llava:7b

2. Install Python dependencies:
   - pip install -r requirements.txt

3. Start the backend server:
   - python main.py

4. Use Smart Images UI to:
   - Add folders containing images
   - Search images semantically: "man in blue shirt", "beach photo", etc.
   - View AI-generated captions and metadata tags

Environment variables:
  - OLLAMA_BASE_URL (default: http://localhost:11434)
  - OLLAMA_VISION_MODEL (default: llava:7b)
""")

if __name__ == "__main__":
    asyncio.run(main())
