#!/usr/bin/env python3
"""
Simple synchronous test for Smart Images - Windows compatible
Tests basic connectivity without asyncio/transformers complexity
"""

import requests
import os
import json

def test_ollama_connection():
    """Test Ollama is running"""
    print("\n" + "="*60)
    print("  Testing Ollama Connection")
    print("="*60)
    
    try:
        url = "http://localhost:11434/api/tags"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            print(f"✓ Ollama is running!")
            print(f"✓ Available models: {len(models)}")
            
            # Check for vision model
            model_names = [m["name"] for m in models]
            print(f"✓ Models: {', '.join(model_names)}")
            
            has_vision = any("llava" in name for name in model_names)
            if has_vision:
                print("✓ Vision model (llava) is available!")
                return True
            else:
                print("✗ No vision model found - run: ollama pull llava:latest")
                return False
        else:
            print(f"✗ Error: Ollama returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to Ollama at localhost:11434")
        print("  Make sure Ollama is running!")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_ollama_vision_inference():
    """Test Ollama vision model can process requests"""
    print("\n" + "="*60)
    print("  Testing Ollama Vision Inference")
    print("="*60)
    
    try:
        # Simple test without actual image
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llava:latest",
            "prompt": "test",
            "stream": False,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✓ Vision model responds to requests")
            data = response.json()
            if "response" in data:
                print(f"✓ Response received: {data['response'][:50]}...")
            return True
        else:
            print(f"✗ Error: Vision model returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Vision model request timed out (model may be loading)")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to vision model")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_database():
    """Test SQLite database exists"""
    print("\n" + "="*60)
    print("  Testing Database")
    print("="*60)
    
    try:
        db_path = "smart_files.db"
        if os.path.exists(db_path):
            print(f"✓ Database exists: {db_path}")
            
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for image_embeddings table
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='image_embeddings'
            """)
            
            if cursor.fetchone():
                print("✓ image_embeddings table exists")
                
                # Get stats
                cursor.execute("SELECT COUNT(*) FROM image_embeddings")
                count = cursor.fetchone()[0]
                print(f"✓ Images indexed: {count}")
                
                conn.close()
                return True
            else:
                print("✗ image_embeddings table not found")
                conn.close()
                return False
        else:
            print(f"✗ Database not found at {db_path}")
            print("  Run backend to create it")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def test_imports():
    """Test critical Python imports"""
    print("\n" + "="*60)
    print("  Testing Python Imports")
    print("="*60)
    
    imports = {
        "httpx": "HTTP client",
        "PIL": "Image processing",
        "piexif": "EXIF parsing",
        "requests": "HTTP requests",
    }
    
    results = {}
    for module, desc in imports.items():
        try:
            __import__(module)
            print(f"✓ {module:20} - {desc}")
            results[module] = True
        except ImportError:
            print(f"✗ {module:20} - NOT INSTALLED")
            results[module] = False
    
    return all(results.values())


def main():
    print("\n" + "="*60)
    print("  SMART IMAGES - SIMPLE TEST SUITE (Windows Compatible)")
    print("="*60)
    
    results = {
        "Ollama Connection": test_ollama_connection(),
        "Vision Inference": test_ollama_vision_inference(),
        "Imports": test_imports(),
        "Database": test_database(),
    }
    
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n{passed}/{total} tests passed\n")
    
    if passed == total:
        print("✓ All systems ready! Your Smart Images implementation is working.")
        print("\nNext steps:")
        print("1. Run backend: python main.py")
        print("2. Open app and go to Smart Images tab")
        print("3. Click 'Add Folders' to index images")
        print("4. Try searching: 'beach', 'person', 'indoor', etc.\n")
    else:
        print("⚠ Some tests failed. Check the errors above.")
        print("\nCommon fixes:")
        print("- Ensure Ollama is running: ollama serve")
        print("- Verify llava is installed: ollama pull llava:latest")
        print("- Install requirements: pip install -r requirements.txt\n")


if __name__ == "__main__":
    main()
