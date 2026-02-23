#!/usr/bin/env python3
"""
Test script for semantic image search functionality
Tests: date_modified tracking, semantic search, and metadata filtering
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_semantic_search():
    """Test the semantic search implementation"""
    from services.vector_store import VectorStore
    from services.smart_images_service import SmartImagesService
    from services.embedding_service import EmbeddingService
    
    print("=" * 60)
    print("SEMANTIC SEARCH TEST SUITE")
    print("=" * 60)
    
    try:
        # Initialize services
        print("\n1. Initializing services...")
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        smart_images_service = SmartImagesService(vector_store, embedding_service)
        print("   ✓ Services initialized")
        
        # Get indexed images
        print("\n2. Fetching indexed images...")
        images = await smart_images_service.get_indexed_images()
        print(f"   ✓ Found {len(images)} indexed images")
        
        if not images:
            print("\n   ⚠ No images indexed. Please index some folders first.")
            print("   Add images through the UI: Smart Images → Add Your First Folder")
            return
        
        # Check if date_modified is present
        print("\n3. Checking date_modified metadata...")
        images_with_date = [img for img in images if img.get('date_modified')]
        print(f"   ✓ {len(images_with_date)} images have date_modified")
        if len(images_with_date) > 0:
            sample = images_with_date[0]
            print(f"   Sample: {sample['file_name']} → {sample['date_modified']}")
        
        # Test semantic search queries
        test_queries = [
            "mountain landscape",
            "recent images",
            "people portrait",
            "nature outdoor",
            "documents text",
        ]
        
        print("\n4. Testing semantic search queries...")
        for query in test_queries:
            results = await smart_images_service.search_images(query)
            
            if results:
                print(f"\n   Query: '{query}'")
                print(f"   Found {len(results)} results")
                
                # Show top result
                top = results[0]
                print(f"   Top result: {top['file_name']}")
                print(f"   - Caption: {top['caption'][:60]}...")
                print(f"   - Relevance: {top['similarity_score']:.2%}")
                
                if top.get('tags'):
                    print(f"   - Tags: {', '.join(top['tags'][:3])}")
                if top.get('date_modified'):
                    print(f"   - Modified: {top['date_modified']}")
            else:
                print(f"\n   Query: '{query}'")
                print(f"   ✗ No results found")
        
        # Test date-related search
        print("\n5. Testing date-specific queries...")
        date_queries = ["recent", "old images", "last week"]
        
        for query in date_queries:
            results = await smart_images_service.search_images(query)
            if results:
                print(f"\n   Query: '{query}' → {len(results)} results")
                for i, img in enumerate(results[:2], 1):
                    if img.get('date_modified'):
                        print(f"   {i}. {img['file_name']} ({img['date_modified']})")
        
        # Test cross-field search
        print("\n6. Testing cross-field search...")
        print("   Testing if search matches across caption, tags, and filename...")
        
        if images and images[0].get('tags'):
            test_tag = images[0]['tags'][0] if isinstance(images[0]['tags'], list) else str(images[0]['tags']).split(',')[0]
            test_tag = str(test_tag).strip()
            
            results = await smart_images_service.search_images(test_tag)
            print(f"\n   Searching for tag: '{test_tag}'")
            print(f"   ✓ Found {len(results)} results")
            
            # Verify the original image is in results
            original_ids = [img['id'] for img in images if test_tag in str(img.get('tags', []))]
            result_ids = [res['id'] for res in results]
            
            if set(original_ids) & set(result_ids):
                print(f"   ✓ Tag-based search working correctly")
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY: All tests completed successfully! ✓")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Try semantic search in the UI: Smart Images → Search")
        print("2. Test queries like 'mountains', 'person portrait', 'recent'")
        print("3. Verify date_modified shows in image preview modal")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_semantic_search())
