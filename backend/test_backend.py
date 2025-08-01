#!/usr/bin/env python3
"""
Test script to check backend connectivity and Phi model
"""
import asyncio
import aiohttp
import json
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_backend_health():
    """Test if backend is running and healthy"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get('http://localhost:8000/health') as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Backend is healthy: {data}")
                    return True
                else:
                    print(f"✗ Backend health check failed: {response.status}")
                    return False
    except Exception as e:
        print(f"✗ Cannot connect to backend: {e}")
        return False

async def test_phi_query():
    """Test Phi model query"""
    try:
        async with aiohttp.ClientSession() as session:
            # Test query endpoint
            payload = {
                "question": "What is the main topic of the documents?",
                "session_id": None,
                "llm_provider": "phi"
            }
            
            async with session.post('http://localhost:8000/api/query', json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Phi query successful")
                    print(f"Answer: {data.get('answer', 'No answer')[:200]}...")
                    return True
                else:
                    print(f"✗ Phi query failed: {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
    except Exception as e:
        print(f"✗ Phi query error: {e}")
        return False

async def main():
    """Main test function"""
    print("Testing SmartFile AI Backend...")
    print("=" * 50)
    
    # Test backend health
    if not await test_backend_health():
        print("\nBackend is not running or not accessible.")
        print("Please start the backend with: cd backend && python main.py")
        return
    
    # Test Phi model
    print("\nTesting Phi model...")
    await test_phi_query()
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main()) 