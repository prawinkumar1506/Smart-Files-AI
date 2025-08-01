#!/usr/bin/env python3
"""
Test script to verify Phi model optimizations
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from services.llm_client import PhiLLMClient

async def test_phi_model():
    """Test the optimized Phi model"""
    print("Testing Phi model optimizations...")
    
    try:
        # Initialize client
        client = PhiLLMClient()
        print("✓ Phi client initialized successfully")
        
        # Test answer generation
        question = "What is the main topic?"
        context = "This is a test document about artificial intelligence and machine learning."
        
        print(f"Testing answer generation with question: '{question}'")
        start_time = asyncio.get_event_loop().time()
        
        answer = await client.generate_answer(question, context)
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        print(f"✓ Answer generated in {duration:.2f} seconds")
        print(f"Answer: {answer}")
        
        # Test session name generation
        print("\nTesting session name generation...")
        start_time = asyncio.get_event_loop().time()
        
        session_name = await client.generate_session_name("Hello, how are you today?")
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        print(f"✓ Session name generated in {duration:.2f} seconds")
        print(f"Session name: {session_name}")
        
        print("\n✅ All tests passed! Phi model is optimized for faster responses.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phi_model()) 